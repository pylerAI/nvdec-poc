# 전처리 GPU 오프로딩, flag가 아니라 엔진 패치와 측정으로 푼다

## 결론 먼저

vLLM 0.28.0은 flag나 config만으로는 stage 5(resize/normalize)와 stage 6(audio → mel)을 GPU에서 돌릴 수 없다. 세 겹의 장치가 막고 있다.

- **config validator.** `--mm-processor-device cuda`(= `mm_processor_kwargs["device"]`)를 주면 startup에서 `MultiModalConfig.validate_mm_processor_device`가 "이 instance는 language model도 돌린다"는 이유로 `ValueError`를 던진다. 이 정책은 PR #50390(2026-08-05 merge)이 EPD encode-only instance에만 GPU 전처리를 허용하도록 의도적으로 넣은 것이다 ([vllm/config/multimodal.py L414-461](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/multimodal.py#L414-L461), [PR #50390](https://github.com/vllm-project/vllm/pull/50390)).
- **모델 processor.** 이 모델은 HF processor가 아니라 vLLM 자체 구현 `NanoNemotronVLProcessor`를 쓴다. `__init__`에 `device`도 `**kwargs`도 없어서 per-request kwargs로 우회해도 `TypeError`가 나고, 코드 어디에서도 device를 읽지 않는다 ([vllm/transformers_utils/processors/nano_nemotron_vl.py L764-774](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/transformers_utils/processors/nano_nemotron_vl.py#L764-L774)).
- **transport.** 설령 GPU에서 계산하더라도 기본 transport `direct_rpc`에서는 `_postprocess_output`이 `.cpu()`로 되돌린다 ([vllm/multimodal/processing/context.py L225-254](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/processing/context.py#L225-L254)).

NVDEC backend 자체도 `np.ndarray` 반환 계약 때문에 frame을 pinned host로 내린다 ([vllm/multimodal/video.py L814-867](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L814-L867)). 따라서 "GPU chain을 끊지 않는다"는 목표는 0.28.0의 설계와 정면으로 충돌한다.

결국 코드를 바꿔야 한다. 가장 적게 건드리면서 upstream 방향과도 맞는 길은 frontend가 아니라 **엔진 쪽**이다. processor가 raw uint8 NHWC frame(12 frame 360p 기준 8.3 MB, 지금의 bf16 18.6 MB보다 작다)을 내보내고, 모델의 `_extract_video_embeddings_temporal`에서 기존 `_bicubic_resize_and_normalize`를 CUDA로 실행하는 것이다. Qwen2-VL의 `mm_device_do_normalize`/`FusedInputNorm`, 그리고 Nemotron VL의 normalize만 옮기는 open PR #57924와 같은 패턴이다 ([PR #57924](https://github.com/vllm-project/vllm/pull/57924)).

오디오는 16 kHz waveform을 엔진에 보내고, 이미 `device=` 인자를 가진 `ParakeetExtractor`를 모델 forward 안에서 호출하면 된다(voxtral/midashenglm 선례). 하지만 원시 로그를 다시 읽으면 오디오 고유의 CPU 비용은 요청당 ~0.05 cpu-s에 불과하다. 0.07→0.29 cpu-s 차이는 오디오가 아니라 processor cache hit/miss 차이다.

더 중요한 발견은 따로 있다. VOD 행에서 rep 1과 rep 2–3 사이에 CPU가 2–4.4×, throughput이 4–4.5× 벌어지고, wall time이 "요청 수 × 요청당 CPU"로 정확히 떨어진다. 이 패턴은 64개 동시 요청이 12개 API server가 아니라 사실상 하나에 몰렸을 가능성을 강하게 시사한다. 이 가설이 맞으면 요청 분배를 고치는 것이 어떤 GPU 오프로딩보다 큰 이득이다.

그래서 순서는 다음과 같다.

1. 분배와 cache를 먼저 측정한다.
2. video transform을 엔진 GPU로 옮긴다.
3. 오디오는 CPU 중복 제거만 한다.

upstream은 co-located 배포의 frontend GPU 전처리를 막고, EPD(encode-only instance + `torch_shm` + torchcodec `device=cuda`, PR #53675, v0.30.0)로 가고 있다. B200 한 장에서는 EPD를 지금 할 이유가 없다.

## vLLM 0.28.0은 세 겹의 장치로 frontend GPU 전처리를 막는다

### 먼저 팀 다이어그램을 코드와 맞춘다

0.28.0에서 architecture `NemotronH_Nano_Omni_Reasoning_V3`는 모델 클래스 `NemotronH_Nano_VL_V2`로 매핑된다 ([vllm/model_executor/models/registry.py L530-532](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/registry.py#L530-L532)). 그 processing info는 HF `AutoProcessor`를 전혀 쓰지 않고, vLLM 자체 `NanoNemotronVLProcessor`를 `ctx.init_processor(...)`로 만든다 ([nano_nemotron_vl.py L200-210](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L200-L210)).

이 processor의 video 경로는 `video_to_pixel_values` → `torch.from_numpy(video)` → `@torch.compile(dynamic=True)`가 붙은 `_bicubic_resize_and_normalize` 순서다. NHWC→NCHW permute, float32 cast, `F.interpolate(mode="bicubic", align_corners=False, antialias=True)`, `(x/255-mean)/std`, 모델 dtype cast를 모두 CPU에서 한다 ([processors/nano_nemotron_vl.py L59-82, L217-248](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/transformers_utils/processors/nano_nemotron_vl.py#L59-L82)).

여기서 두 가지가 다이어그램과 다르다.

**target size는 560×315가 아니라 672×384이고, 640×360 입력을 오히려 upscale한다.** 규칙은 `video_target_num_patches=1024`에 맞춰 aspect를 보존하면서 16의 배수(그리고 pixel-shuffle을 위해 patch 수가 짝수)로 snap하는 것이다. 640×360(aspect 1.778)은 `(ph, pw) = (24, 42)` → 672×384, 1008 patches가 되고, 2×2 pixel shuffle 후 **tubelet당 252 token**이 된다 ([processors/nano_nemotron_vl.py L145-214](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/transformers_utils/processors/nano_nemotron_vl.py#L145-L214)). HF repo의 `image_processing.py`도 같은 산술("Port of vLLM's `_compute_aspect_preserving_size`")을 쓴다 ([image_processing.py L195-228](https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16/raw/main/image_processing.py)). 12 frame은 `video_temporal_patch_size=2`로 6 tubelet → 1512 video token이다. 측정된 prompt_tokens 1705(video-only)는 여기에 텍스트와 "Frame i sampled at …" separator ~190 token을 더한 값과 일치한다 ([results/run_all_2026-09-17.log L473](file:///Users/garamchoi/pyler/nvdec-poc/results/run_all_2026-09-17.log)). 다만 이는 정합성 확인이지 증명은 아니므로, 엔진에서 `pixel_values_flat_video.shape`을 한 번 찍어 보기를 권한다.

**"16×16 조각내기"는 CPU에서 일어나지 않는다.** patchify는 엔진 GPU의 RADIO 안 `Im2Patches`(einops `"b c (py yy) (px xx) -> b (py px) (c yy xx)"`)와 `video_embedder = ViTPatchLinear(3·T·16·16 → 1280)`가 담당한다 ([vllm/model_executor/models/radio.py L109-263, L386-445](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/radio.py#L109)).

따라서 stage 5의 실체는 "fp32 bicubic antialias resize + normalize + bf16 cast"다. 그 출력 `pixel_values_flat_video`는 (12,3,384,672) bf16 = **18.6 MB**로, raw frame 8.3 MB의 2.24배다(fp32 중간값은 37.2 MB). 숫자는 코드에서 확인한 shape/dtype으로 계산한 값이다.

### 질문 (1): flag만으로는 안 된다

이 전제 위에서 질문 (1)의 답은 "안 된다"이며, 이유는 서로 독립적인 세 지점에 있다.

**지점 1: config validator.** `VllmConfig.__post_init__`이 `_resolve_mm_processor_device()`와 `_validate_mm_processor_device()`를 부른다 ([vllm/config/vllm.py L1597-1599](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/vllm.py#L1597-L1599)). 후자는 요청된 device가 accelerator이고 `ec_config is None or not ec_config.is_encode_only`이면 다음 `ValueError`를 낸다 ([config/multimodal.py L414-461](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/multimodal.py#L414-L461); 테스트 [tests/config/test_multimodal_config.py L227-245](https://github.com/vllm-project/vllm/blob/v0.28.0/tests/config/test_multimodal_config.py#L227-L245)).

> Cannot run the multi-modal processor on 'cuda': this instance also runs the language model … its allocations are outside the memory the engine profiled for its KV cache -- risking OOM or a silently shrunken cache. Accelerator preprocessing is only supported on an encode-only instance of an encode/prefill/decode deployment

`--mm-processor-device`의 help도 "Only takes effect for HF 'fast' (torchvision-backed) processors, which accept a `device` argument … 'auto' resolves to 'cpu' everywhere else"라고 못박는다 ([vllm/engine/arg_utils.py L1367-1390](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/engine/arg_utils.py#L1367-L1390)).

**지점 2: 모델 processor.** `init_processor`는 merged kwargs를 signature 필터링 없이 `typ(**merged_kwargs)`로 넘긴다 ([context.py L211-223](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/processing/context.py#L211-L223)). 그래서 per-request `mm_processor_kwargs={"device":"cuda"}`는 validator를 우회하지만, `NanoNemotronVLProcessor.__init__`에서 `TypeError`로 죽는다(코드 추적; HTTP 응답은 실행으로 확인하지 않음). processor 파일에는 `device` 문자열 자체가 없다.

**지점 3: transport.** `_postprocess_output`은 `keep_on_device = (mm_tensor_ipc == "torch_shm")`일 때만 device tensor를 유지하고, 그 외에는 `tensor.cpu()`를 호출한다 ([context.py L225-254](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/processing/context.py#L225-L254)). `direct_rpc`의 `tensor_data()`도 `tensor.flatten().cpu()…`로 한 번 더 host copy를 한다 ([vllm/v1/utils.py L780-790](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/utils.py#L780-L790)).

0.28.0의 세 번째 메커니즘인 `mm_device_do_normalize`(PR #50411)는 normalize/rescale만 `FusedInputNorm`으로 옮긴다. 그런데 `supports_mm_device_do_normalize = True`인 모델이 `qwen2_vl.py` L1196과 `qwen2_5_vl.py` L1259뿐이라, Nemotron에서는 "Model does not support mm_device_do_normalize" 경고와 함께 강제로 꺼진다 ([vllm/config/model.py L931-974](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/model.py#L931-L974), [interfaces.py L158-162](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/interfaces.py#L158-L162), [vision.py L654-690](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/vision.py#L654-L690)).

### Backend 쪽 계약은 더 근본적이다

`VideoLoader.load_bytes -> tuple[npt.NDArray, dict]`가 API다 ([video.py L187-195](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L187-L195)). `_decode_to_pinned_host`는 `get_batch_frames_by_index` → `torch.from_dlpack` → `torch.stack` → NHWC → `torch.empty(..., device="cpu", pin_memory=True)` → `copy_(non_blocking=True)` → `stream.synchronize()` → `host_frames.numpy()` 순서로 반드시 host로 내린 뒤, `del device_frames`로 GPU 사본을 버린다 ([video.py L814-867](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L814-L867)). Parser도 `torch.Tensor` video를 받으면 `video.numpy()`를 호출하므로, CUDA tensor를 돌려주는 것만으로는 그 자리에서 실패한다 ([vllm/multimodal/parse.py L648-664, L733-774](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/parse.py#L648-L774)).

이 설계는 우연이 아니다. backend를 넣은 PR #44465 "Vram semaphore infra"(2026-06-27)는 "decoded into VRAM, copied to pinned host memory, then the VRAM is released"를 명시했고, "preprocessing to work on GPU-resident frame tensors"는 "a future PR … One issue must be discussed with the community first"로 미뤘다. 그 후속 PR은 아직 없다 ([PR #44465](https://github.com/vllm-project/vllm/pull/44465)). 공식 docs도 "decode the sampled video frames on the GPU before copying them into host memory for multimodal preprocessing"이라고 쓴다 ([docs/features/multimodal_inputs.md L927-945](https://github.com/vllm-project/vllm/blob/v0.28.0/docs/features/multimodal_inputs.md#L927-L945)).

### 오디오(stage 6)는 결이 다르다

`use_audio_in_video`가 켜지면 chat endpoint가 같은 `video_url`을 `fetch_audio`로 **한 번 더** 가져와(base64 재디코드 포함) `AudioMediaIO`로 넘긴다 ([vllm/entrypoints/chat_utils.py L1089-1097](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/entrypoints/chat_utils.py#L1089-L1097)). `load_audio`는 libsndfile을 먼저 시도했다가(TS/MP4 container는 열지 못함) PyAV로 container를 다시 demux해 AAC를 FFmpeg로 decode한다 ([vllm/multimodal/media/audio.py L48-171, L216-258](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/media/audio.py#L48-L73)). NVDEC support matrix에는 audio codec이 없으므로 demux와 AAC decode는 GPU로 갈 수 없다 ([NVIDIA Video Encode and Decode GPU Support Matrix](https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new)).

16 kHz resample은 모델의 data parser가 libswresample로 한다 ([parse.py L666-703](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/parse.py#L666-L703), [vllm/multimodal/audio.py L174-229](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/audio.py#L174-L229)). log-mel은 transformers의 `ParakeetFeatureExtractor`가 아니라 vLLM 자체 torch 구현 `ParakeetExtractor`(preemphasis 0.97, `torch.stft` n_fft 512/hop 160/win 400, 128 slaney mel bins, `log(x+2^-24)`, 30 s clip)가 계산한다.

핵심은 이것이다. **이 extractor는 이미 `__call__(raw_speech, *, device="cpu")` 인자를 갖고 Hann window와 mel filter를 device별로 cache하는데, processor의 호출부 `extractor(audios)`가 device를 넘기지 않는다** ([vllm/model_executor/models/parakeet.py L134-335](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/parakeet.py#L134-L335), [processors/nano_nemotron_vl.py L981-1007](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/transformers_utils/processors/nano_nemotron_vl.py#L981-L1007)). 즉 mel을 CPU에 묶어둔 것은 알고리즘이 아니라 호출부 한 줄이다. 그 결과 `input_audio_features`(clips, frames, 128)가 엔진으로 가서 `ProjectedParakeet`에 들어간다 ([nano_nemotron_vl.py L1262-1291](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L1262-L1291)).

### 단계별 정리

| 단계 | 0.28.0에서 실제 위치 | 거기에 묶어두는 코드 | GPU로 옮길 수 있나 |
|---|---|---|---|
| 3 decode | API server GPU (NVDEC, `_DEVICE_INDEX=0`, `hw_decoders` slot pool) | [video.py L674-765, L869-908](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L674-L765) | 이미 GPU |
| 4 D2H | pinned host copy, `np.ndarray` 반환 | 계약 [L187-195](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L187-L195), copy [L857-867](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L857-L867), parser `.numpy()` [parse.py L661-662](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/parse.py#L648-L774) | 계약 3곳을 바꿔야 |
| 5 resize+normalize | API server CPU, `_bicubic_resize_and_normalize` (torch.compile, OMP 1 thread) | `from_numpy` + CPU `norm_mean/std` [L247-248, L605-606](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/transformers_utils/processors/nano_nemotron_vl.py#L217-L248) | 연산 자체는 device-agnostic |
| 5' patchify | 엔진 GPU (`Im2Patches`, RADIO) | [radio.py L109-263](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/radio.py#L109) | 이미 GPU (다이어그램 수정) |
| 6a demux + AAC | API server CPU (PyAV/FFmpeg), container 2회 demux | [media/audio.py L48-171](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/media/audio.py#L48-L73) | 불가 (NVDEC에 audio codec 없음) |
| 6b resample 16 kHz | API server CPU (libswresample) | [parse.py L666-703](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/parse.py#L666-L703) | 가능 (torchaudio, 수치 미검증) |
| 6c log-mel | API server CPU, `ParakeetExtractor(device="cpu")` | 호출부 [L1006](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/transformers_utils/processors/nano_nemotron_vl.py#L981-L1007) | 코드는 이미 device 지원 |
| 7 encoder | 엔진 GPU (`embed_multimodal`, video는 한 개씩 순차) | [gpu_model_runner.py L3198-3288](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/worker/gpu_model_runner.py#L3198-L3288) | 이미 GPU |

## Transport는 공유메모리가 아니라 ZMQ msgpack이고, 12개 API server는 cache도 바꾼다

### 기본 transport의 실제 경로

다이어그램의 "공유메모리로 엔진에 전달"은 이 구성에서 틀렸다. 기본값 `--mm-tensor-ipc direct_rpc`에서 HF processor 출력(`MultiModalKwargsItem`, `EngineCoreRequest.mm_features` 안)은 `MsgpackEncoder`가 인코딩한다. **256 B 이상인 tensor는 모두 out-of-band buffer**로 같은 ZMQ multipart 메시지에 실려, client의 ROUTER socket에서 엔진의 DEALER socket으로 간다 ([vllm/v1/serial_utils.py L136-178, L257-273](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/serial_utils.py#L136-L162), [vllm/v1/engine/core_client.py L546-598](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/engine/core_client.py#L546-L598), [vllm/v1/engine/core.py L1651-1732](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/engine/core.py#L1651-L1732)). 엔진은 ZMQ frame을 zero-copy로 view한 뒤 `pin_memory()` 사본을 만들고 비동기 H2D를 한다 ([serial_utils.py L399-425](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/serial_utils.py#L399-L425), [vllm/multimodal/inputs.py L462-542](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/inputs.py#L462-L542)).

정직한 한 줄 요약은 "msgpack + out-of-band buffer를 ZMQ `ipc://` socket으로, kernel copy 한 번, 엔진에서 pin + H2D 한 번"이다. open PR #51349는 이 기본 경로를 "mm tensor → ZMQ IPC → CPU Buffer → Pin Memory → GPU"로 묘사하며 "dynamic memory allocation and pin memory being particularly expensive"라고 지적한다 ([PR #51349](https://github.com/vllm-project/vllm/pull/51349)).

TP=1이므로 엔진 쪽 worker는 `UniProcExecutor`로 EngineCore process 안에서 돈다. 따라서 엔진 안에서는 추가 hop이 없다 ([vllm/config/parallel.py L955-956](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/parallel.py#L955-L956), [uniproc_executor.py L51-74](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/executor/uniproc_executor.py#L51-L74)). host round-trip은 전부 P0(API server) 쪽, 즉 NVDEC D2H → CPU transform → ZMQ → pin → H2D에 있다.

### `--api-server-count 12`는 cache 종류까지 바꾼다

`_get_cache_type`은 `_api_process_count == 1`일 때만 IPC cache를 허용하고, 아니면 `"processor_only"`를 돌려준다 ([vllm/multimodal/registry.py L275-299](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/registry.py#L275-L299); docs: "API server scale-out disables multi-modal IPC caching" [docs/configuration/optimization.md L340-344](https://github.com/vllm-project/vllm/blob/v0.28.0/docs/configuration/optimization.md)). 그래서 각 API server는 4 GiB LRU(`mm_processor_cache_gb` 기본값)에 **완전한 item을 담고, hit여도 tensor를 매번 엔진에 보낸다.** 엔진 쪽 receiver cache와 shm cache는 없다 ([vllm/multimodal/cache.py L356-406](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/cache.py#L356-L406), [config/multimodal.py L152-172](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/multimodal.py#L152-L172)). cache key는 처리 전 입력(video는 frame과 원본 bytes 중 작은 쪽 + metadata + `hf_processor_mm_kwargs`)의 blake3 hash다 ([vllm/multimodal/hasher.py L92-118](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/hasher.py#L92-L118)).

`use_audio_in_video`가 켜진 요청은 사정이 또 다르다. `apply()`가 "Bypass the cached path: the HF processor must receive the prompt (with injected <so_embedding>) and the audio data together"라며 `_cached_apply_hf_processor` 대신 `_apply_hf_processor`를 직접 불러 **processor cache를 완전히 우회**한다 ([nano_nemotron_vl.py L737-744](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L737-L744)).

전처리는 process당 `ThreadPoolExecutor(max_workers=1)`인 `_mm_executor`에서 돌며, "must stay single-worker per #38418"로 고정되어 있다. 미디어 download/decode만 8-thread `global_thread_pool`에서 돈다 ([vllm/renderers/base.py L82-109](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/renderers/base.py#L82-L109), [connector.py L40-43](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/media/connector.py#L40-L43), [PR #38418](https://github.com/vllm-project/vllm/pull/38418)). PoC 보고서가 확인한 "`SimpleDecoder` 호출은 GIL을 잡는다"는 사실과 합치면, 같은 process 안에서 decoder thread와 executor thread가 GIL을 두고 경합한다는 추론이 나온다 ([REPORT.md §4.2](file:///Users/garamchoi/pyler/nvdec-poc/REPORT.md)).

### 원시 로그를 다시 읽으면 e2e 숫자가 다르게 보인다

위 네 가지(processor_only cache, audio의 cache bypass, 요청당 tensor 재전송, single-worker executor)를 알고 원시 로그를 다시 읽으면 PoC의 e2e 숫자가 다르게 보인다. 아래는 NVDEC+MPS 구성의 반복별 값이다. 모두 로그에서 직접 읽은 수치다 ([results/run_all_2026-09-17.log L463-574](file:///Users/garamchoi/pyler/nvdec-poc/results/run_all_2026-09-17.log)).

| 행 (N) | rep 1: req/s · p50 · cpu-s/req | rep 2 | rep 3 | 해석 |
|---|---|---|---|---|
| live 6 s 360p, audio+video (64) | 7.8 · 5.2 s · 0.29 | 7.9 · 5.1 · 0.29 | 8.1 · 4.9 · 0.29 | cache bypass → 항상 uncached, 반복 간 일정 |
| live 6 s 360p, video (64) | 28.9 · 2.1 s · 0.07 | 29.2 · 2.1 · 0.07 | 28.2 · 2.1 · 0.08 | 같은 clip 64회 → run 안에서 이미 cache hit |
| VOD 10 s 1080p ×64 | **2.4 · 13.2 s · 0.88** | 10.5 · 5.1 · 0.20 | 10.9 · 4.8 · 0.20 | rep 2–3는 rep 1의 clip 재사용 → hit |
| VOD 30 s 1080p ×32 | **0.9 · 20.6 s · 1.91** | 4.0 · 4.6 · 0.48 | 4.1 · 4.3 · 0.52 | 동일 |
| VOD 120 s 1080p ×8 | **0.2 · 25.9 s · 6.57** | 0.8 · 6.6 · 1.80 | 0.8 · 6.3 · 1.90 | 동일 (120 frame; prompt 17,363 token) |
| VOD 10 s 1080p ×64, audio+video | 2.5 · 14.3 s · 0.93 | 2.5 · 13.2 · 0.93 | 2.5 · 15.0 · 0.92 | cache bypass → 반복 간 일정 |

여기서 세 가지가 읽힌다.

**첫째, 보고서의 VOD 평균은 uncached 1회와 cached 2회의 혼합이다.** 보고서의 VOD 평균(p50 7.7 s, 7.9 req/s, 0.43 cpu-s)은 이 셋을 섞은 값이고, 처음 보는 콘텐츠에 해당하는 값은 rep 1(2.4 req/s, p50 13.2 s, 0.88 cpu-s)이다.

**둘째, 오디오 고유 비용은 작다.** 항상 uncached인 audio+video 10 s 행(0.93 cpu-s, 2.5 req/s)은 video-only rep 1(0.88, 2.4)과 거의 같다. 따라서 오디오 추출+mel이 더하는 것은 요청당 ~0.05 cpu-s와 ~0 req/s다. live 행의 0.07→0.29와 28.8→7.9 req/s는 "오디오 때문"이 아니라 "cache miss 때문"이다. 다이어그램의 "요청당 0.27 cpu-s"도 stage 5 단독이 아니라, uncached frontend 경로 전체(base64 2회, remux, decode 제출, D2H, transform, hashing, tokenization, IPC)의 합으로 보는 것이 맞다. 이 수치는 어느 소스에서도 그대로 도출되지 않는다.

**셋째, 반복 간 wall time 패턴이 이상하다.** rep 1의 wall은 26.4 s(10 s ×64), 37.2 s(30 s ×32), 37.8 s(120 s ×8)다. 이는 **"요청 수 × 요청당 ~0.4/1.2/4.7 s"와 정확히 맞고, 그 요청당 시간은 loader bench의 NVDEC decode(132/350/≈1,500 ms)에 1080p frame당 ~27 ms의 transform을 더한 값으로 분해된다.** cached rep에서는 wall이 decode만 남은 값(95/247/1,180 ms per request; 2 decoder slot 기준 66–132/175–350/750–1,500 ms 범위)으로 떨어진다. 보고서가 측정한 **단일 process NVDEC 상한 9.9 clips/s와 rep 2–3의 10.5–10.9 req/s가 일치**한다는 점에서 다시 확인된다 ([REPORT.md §4.2–4.3](file:///Users/garamchoi/pyler/nvdec-poc/REPORT.md)).

64개 요청이 12개 API server에 고르게 퍼졌다면 wall은 그 1/12 근처여야 한다. 이 산술은 **동시 64개 요청이 사실상 하나의 API server(single-worker executor + GIL을 잡는 decoder)에 직렬화되었다는 가설**을 강하게 지지한다. 메커니즘 후보는 이렇다. 부하 생성기는 64개 연결을 수 ms 안에 한꺼번에 여는데, API server들은 하나의 listen socket을 공유하므로 asyncio accept loop가 깨어난 process 하나가 backlog에 쌓인 연결을 한꺼번에 accept할 수 있다. 다만 이것은 코드로 확인하지 않은 추론이다.

검증은 싸다. burst 중 `/tmp/vllm_nvdec-mps.log`에서 `(APIServer pid=…)` prefix별 "Received request" 수를 세거나, 12개 PID의 CPU를 `top -H`로 보면 된다. 이 가설이 맞으면 요청 분배를 고치는 것만으로 frontend throughput이 최대 12배까지 열리고(그때는 GPU encoder/prefill이 병목이 된다), 그 뒤에야 GPU 오프로딩의 실제 가치가 보인다. 운영 트래픽(여러 채널의 6 s 세그먼트가 경계에 맞춰 몰려오는 live-ingest)이 bursty라면 같은 병리가 그대로 재현된다.

### 공간 예산과 IPC 규칙

`pynvvideocodec` backend가 설정되면 엔진 worker는 KV cache 예산에서 `mm_ipc_gpu_memory_gb` 외에 **API server당 `128 MiB × hw_decoders + 1.8 GiB`**("Per-API-server CUDA context and driver allocation, measured with PyNvVideoCodec 2.0.4 on H100")를 뺀다. 그래서 12 process × (256 MiB + 1.8 GiB) ≈ **24.6 GiB**가 고정비로 나간다 ([video.py L217-224](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L217-L224), [vllm/multimodal/gpu_ipc_memory.py L155-257](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/gpu_ipc_memory.py#L155-L257); 산술은 상수에서 계산, B200 측정치는 upstream에 없음).

이름과 달리 `gpu_ipc_memory.py`에는 CUDA IPC handle 코드가 없다. `MultiModalGPUMemoryPool`은 byte-counting semaphore일 뿐이고, `mm_ipc_gpu_memory_gb`가 0이면 `maybe_init_mm_gpu_ipc_pool`이 `None`을 돌려주며 decode는 lease 없이 진행된다 ([gpu_ipc_memory.py L3-17, L127-152](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/gpu_ipc_memory.py#L3-L17), [video.py L869-908](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L869-L908)). **PoC의 serve 라인에는 `--mm-ipc-gpu-memory-gb`가 없으므로, 지금 frontend VRAM은 사실상 gating 없이 쓰이고 있다** ([bench/e2e_matrix.sh L21-26](file:///Users/garamchoi/pyler/nvdec-poc/bench/e2e_matrix.sh)). open PR #52605는 lease가 켜져 있어도 DLPack frame + stack + contiguous 세 사본 때문에 실제 peak가 예산의 2–3배라고 지적한다 ([PR #52605](https://github.com/vllm-project/vllm/pull/52605)). 엔진 쪽 pinned memory는 tensor마다 pin하는 구조라 크기가 제각각인 video에서 계속 자란다는 보고(peak 5.67 GiB vs 고정 ring 0.50 GiB)도 열려 있다 ([PR #58461](https://github.com/vllm-project/vllm/pull/58461)).

GPU tensor를 process 경계 너머로 넘기려면 `torch_shm`이 유일한 shipped 경로다. `TensorIpcSender`가 `share_memory_()` 후 `torch.multiprocessing` Queue에 넣고(CUDA tensor는 CUDA IPC handle로 이동), `EngineCoreProc`가 `TensorIpcReceiver`로 받는다 ([vllm/v1/engine/tensor_ipc.py L30-178](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/engine/tensor_ipc.py#L30-L105)). 조건은 세 가지다.

- `VLLM_WORKER_MULTIPROC_METHOD=spawn`. 아니면 "torch_shm is known to fail" `ValueError`가 난다 ([config/vllm.py L1261-1270](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/vllm.py#L1261-L1270)).
- `world_size_across_dp == 1` ([config/model.py L1417-1431](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/model.py#L1417-L1431)).
- rank 0을 향한 단일 queue ([vllm/v1/engine/utils.py L1088-1094](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/v1/engine/utils.py#L1088-L1094)).

다중 API server는 테스트로 지원된다 ([tests/v1/test_tensor_ipc_queue.py L390-435](https://github.com/vllm-project/vllm/blob/v0.28.0/tests/v1/test_tensor_ipc_queue.py#L390-L435)). PR #49462가 `torch_shm`을 "single-API-server only"라고 쓴 것은 코드와 어긋난다.

PyTorch의 CUDA IPC 규칙은 다음과 같다 ([PyTorch multiprocessing docs](https://docs.pytorch.org/docs/stable/multiprocessing.html)). spawn/forkserver가 필수이고, **sender는 receiver가 들고 있는 동안 원본 tensor를 유지해야 하며**, consumer가 비정상 종료하면 sender 쪽 메모리가 영구 누수될 수 있다. TRT-LLM은 "CUDA IPC handles are invalid same-process"라서 별도 local store를 둔다 ([TRT-LLM shared_tensor.py](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/_torch/shared_tensor/shared_tensor.py)).

MPS 아래에서 각 client는 자기 GPU address space를 가진다 ([NVIDIA MPS Architecture](https://docs.nvidia.com/deploy/mps/architecture.html)). NVIDIA 문서에서 CUDA IPC 제한은 Tegra뿐이고 upstream RFC의 prototype은 H100 + MPS에서 돌았지만 ([RFC #30839](https://github.com/vllm-project/vllm/issues/30839)), B200 + MPS + `torch_shm` CUDA tensor 조합을 다룬 test나 문서는 없다. frontend SM 경합을 묶는 문서화된 lever는 `CUDA_MPS_ACTIVE_THREAD_PERCENTAGE`와 `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT`이다 ([MPS Environment Variables](https://docs.nvidia.com/deploy/mps/appendix-environment-variables.html)).

마지막으로 version 이동 시 걸릴 것이 있다. v0.31.0부터 per-request `mm_processor_kwargs`와 `media_io_kwargs`는 `--trust-request-mm-kwargs` 없이는 거부되는데(#58830), PoC의 부하 생성기는 둘 다 요청마다 보낸다 ([v0.31.0 release](https://github.com/vllm-project/vllm/releases/tag/v0.31.0), [bench/load_test.py L31-40](file:///Users/garamchoi/pyler/nvdec-poc/bench/load_test.py)).

## 현실적 선택지는 다섯 가지이고, 엔진 쪽 resize+normalize가 가장 적게 건드린다

질문 (2)의 답을 옵션별로 정리한다. 공통 전제는 두 가지다.

- `_bicubic_resize_and_normalize`는 `torch.from_numpy`와 CPU `norm_mean/norm_std`만 아니면 같은 코드가 CUDA에서 그대로 돈다(코드 확인).
- **GPU 작업을 어느 process에 두느냐가 설계의 전부다.** frontend에 두면 12개 process가 엔진이 profile하지 않은 VRAM을 쓰고 forward pass와 SM을 다툰다(validator 메시지가 말하는 바로 그 위험). 엔진에 두면 profiling run(128 frame × 512² dummy video)이 자동으로 그 경로를 포함한다 ([nano_nemotron_vl.py L838-876](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L781)).

### 옵션 A. frontend GPU processor + `torch_shm`

`--mm-processor-device` 또는 `device` kwarg 경로를 끝까지 뚫는 방법이다.

- **바꿔야 하는 곳**
  - validator 완화: [config/multimodal.py L414-461](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/multimodal.py#L414-L461)
  - backend가 `device_frames`를 반환하도록: [video.py L857-867](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L814-L867) + loader 계약 [L187-195](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L187-L195)
  - parser `.numpy()` 분기: [parse.py L661-662](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/parse.py#L648-L774)
  - hasher의 `.cpu()`: [hasher.py L98-99](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/hasher.py#L92-L118)
  - processor `__init__`에 device 추가, `from_numpy(...).to(cuda)`, mean/std 이동: [L247-248, L605-606, L764-774](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/transformers_utils/processors/nano_nemotron_vl.py#L217-L248)
  - lease 범위를 transform 출력까지 확장: [video.py L897-902](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L869-L908)
- **config/flag**: `--mm-tensor-ipc torch_shm`, `VLLM_WORKER_MULTIPROC_METHOD=spawn`, `--mm-ipc-gpu-memory-gb N`, 그리고 **`--mm-processor-cache-gb 0`**. cache를 끄지 않으면 P0 LRU가 CUDA tensor를 process당 최대 4 GiB 붙든다(cache 코드 [cache.py L356-406](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/cache.py#L356-L406)와 `_postprocess_output`에서 추론).
- **얻는 것**: host hop 완전 제거("끊기지 않는 chain").
- **잃는 것·위험**: 6곳 patch. 12 process의 unbudgeted VRAM과 SM 경합. MPS+CUDA IPC 미검증. sender keep-alive 규칙과 vLLM이 `queue.put` 후 reference를 버리는 동작의 상호작용 미문서. upstream 정책에 정면으로 역행.
- **upstream 적합성**: 낮음.

### 옵션 B. NVDEC lease 안에서 frontend GPU resize 후 작은 tensor만 D2H

- **바꿔야 하는 곳**
  - `_decode_to_pinned_host`에서 D2H 전에 resize(+normalize) 수행: [video.py L847-867](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/video.py#L814-L867)
  - loader가 처리된 frame을 돌려주므로 hashing(`MediaWithBytes`) 및 prompt replacement의 `video.shape` 사용처 조정: [nano_nemotron_vl.py L484-558](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L484-L558)
  - processor는 resize 생략
- **config/flag**: `--mm-ipc-gpu-memory-gb`를 fp32 중간값까지 포함해 산정.
- **얻는 것**: 1080p에서 D2H/IPC 8× 감소(6.2 MB→0.77 MB/frame), CPU transform 제거.
- **잃는 것·위험**: frontend resize kernel이 엔진 SM과 경합한다(SGLang이 2 worker에서 9.30→4.02 req/s 후퇴한 바로 그 현상). 16:9가 아닌 소스에서 target-size 규칙 재적용 시 일관성 검증 필요. 정책 역행.
- **upstream 적합성**: 낮음.

### 옵션 C. 엔진 쪽 resize+normalize (uint8 NHWC passthrough), 권장

- **바꿔야 하는 곳**
  - processor: `_preprocess_video`/`_videos_to_pixel_values_lst`가 `torch.from_numpy` zero-copy uint8 `(frames,H,W,3)`를 `pixel_values_flat_video`로 내보내고, `tokens_in_single_frame`을 `get_video_target_size_and_feature_size`로 계산: [L862-979](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/transformers_utils/processors/nano_nemotron_vl.py#L862-L979)
  - model: `NanoNemotronVLVideoPixelInputs` schema를 `("bvf","h","w",3)`로: [L165-181](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L165-L181)
  - model: `_parse_and_validate_video_input`: [L1350-1407](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L1350-L1407)
  - model: `_extract_video_embeddings_temporal`에서 video 1개씩 `_bicubic_resize_and_normalize(frames, size=(th,tw), mean.to(dev), std.to(dev), dtype)` 호출 후, EVS용 `rows/cols`를 resize 후 shape에서 계산: [L1171-1260](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L1171-L1260)
  - 모델 flag `supports_*` 추가
- **config/flag**: 없음(또는 모델 수준 opt-in flag). `_postprocess_output`은 정수 tensor를 cast하지 않으므로 uint8이 그대로 통과한다 ([context.py L245-252](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/processing/context.py#L225-L254)).
- **얻는 것**: frontend CPU transform 제거. GPU 작업이 엔진 profiled budget 안에 들어감. 360p에서 IPC/cache/H2D 18.6→8.3 MB. 같은 4 GiB cache에 2.2× 더 담김. prompt replacement·hashing·field config·dummy builder 무변경.
- **잃는 것·위험**: **1080p에서는 payload가 커진다**(10 frame: bf16 15.5 MB → uint8 raw 62 MB). GPU resize의 CPU 대비 수치 A/B 필요(저자들이 resize kernel 차이에 민감하다고 명시). `torch.compile(dynamic=True)` 함수가 worker에서 처음 compile되는 지연. in-tree에 forward 안 resize 선례 없음.
- **upstream 적합성**: 중간. `mm_device_do_normalize`와 같은 "모델 opt-in flag" 형태로 제안 가능.

### 옵션 C-lite. PR #57924 방식 (normalize만 엔진으로)

- **바꿔야 하는 곳**: `supports_mm_device_do_normalize = True` + uint8 resized passthrough + C-RADIO 앞 `FusedInputNorm` ([vision.py L587-733](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/vision.py#L587))
- **config/flag**: `mm_device_do_normalize`(기본 True)
- **얻는 것**: PR 측정 기준 32 frame @512² renderer 50.68→20.51 ms(2.47×), payload 48→24 MiB.
- **잃는 것·위험**: bicubic resize는 CPU에 남는다("Bicubic interpolation remains under torch.compile").
- **upstream 적합성**: 높음. PR이 열려 있다(2026-09-21).

### 옵션 D. EPD encode-only instance

- **바꿔야 하는 곳**: 두 번째 vLLM instance(`ec_role=ec_producer`, `--mm-encoder-only`), proxy(`disagg_epd_proxy.py`, "stable for 1e1p1d"), EC connector. Nemotron processor의 device plumbing은 여전히 없다.
- **config/flag**: `--ec-transfer-config`, `--mm-tensor-ipc torch_shm`, `--mm-processor-device auto`, v0.30.0부터 `--media-io-kwargs '{"video":{"backend":"torchcodec","device":"cuda"}}'`
- **얻는 것**: upstream이 승인한 유일한 "GPU end-to-end" 경로.
- **잃는 것·위험**: B200 한 장에 instance 2개(메모리 재분할, MPS). 0.28.0 connector는 disk(`ECExampleConnector`)와 host-mmap(`ECCPUConnector`)뿐. Dynamo 지원표상 vLLM `video_url`은 PD 경로에 남음.
- **upstream 적합성**: 높음. 단, 지금 이 배포에는 과하다.

### 오디오: waveform-in-model

- **바꿔야 하는 곳**
  - processor `_preprocess_audio`가 16 kHz waveform(+`audio_num_clips`)을 내보냄: [L981-1007](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/transformers_utils/processors/nano_nemotron_vl.py#L981-L1007)
  - `_get_audio_fields_config`에 `batched("audio")` field: [L407-418](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L395-L418)
  - 새 `…AudioWaveformInputs` schema
  - model에 `self.audio_extractor = ParakeetExtractor(config.sound_config)`를 두고 `_process_audio_input`에서 `device=`로 호출: [L1262-1291](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L1262-L1291)
- **config/flag**: 없음.
- **얻는 것**: S7(mel) frontend 제거. 전송량은 비슷(96 k sample int16 192 KB vs features bf16 ≈154 KB).
- **잃는 것·위험**: 이득이 ms 단위. `_postprocess_output`이 float을 bf16으로 cast하므로 int16 PCM으로 보내거나 `_call_hf_processor` override 필요. cuFFT vs CPU FFT 수치 차이 미측정.
- **upstream 적합성**: 중간. voxtral(`compute_whisper_melspec`)과 midashenglm(`DashengFrontend`) 선례가 있다 ([voxtral.py L745-782](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/voxtral.py#L745-L782), [midashenglm.py L297-347](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/midashenglm.py#L297-L347)).

### 옵션 C의 payload 역전은 숫자로 봐야 한다

target이 672×384(16:9 공통)이므로 **360p 소스는 raw < processed, 1080p 소스는 raw ≫ processed**다. 모두 코드에서 확인한 shape/dtype으로 계산한 값이다.

| 소스 | raw uint8 | processed bf16 | CPU fp32 중간값 |
|---|---|---|---|
| 12 frame 360p | 8.29 MB | 18.6 MB | 37.2 MB |
| 10 frame 1080p | 62.2 MB | 15.5 MB | **249 MB** |
| 120 frame 1080p | 747 MB | 186 MB | **3.0 GB** |

마지막 행의 3.0 GB는 지금 VOD 120 s 요청마다 API server CPU에서 할당되는 양이다.

따라서 **live 360p 세그먼트가 주 워크로드라면 C가 모든 면에서 이득**이다. 1080p VOD가 섞이면 C의 IPC/pin/H2D 증가분과 CPU resize 제거분을 비교해야 한다. 증가분은 pinned D2H가 ~13 GB/s라는 DeepStream mixin의 주석 기준으로 62 MB ≈ 5 ms이고, ZMQ copy와 pin copy가 각각 비슷한 규모다. 제거분은 아래 추정 ~27 ms/frame → 10 frame에 ~270 ms다. 산술상으로는 그래도 C가 남는다.

다만 PR #58461이 지적하는 pinned memory 증가는 raw payload에서 더 심해진다. 1080p 비중이 크면 C-lite(uint8 resized passthrough, 1080p에서 payload 15.5→7.7 MB)와 C를 소스 해상도에 따라 섞는 변형(frontend에서 target보다 큰 소스만 CPU resize)이 현실적이다.

### 수치 위험은 B와 C가 같다

같은 torch op이 CPU 대신 CUDA에서 도는 것이므로 차이는 fp32 bicubic/antialias 결과의 하위 bit 수준이다. 그러나 HF repo는 PIL bicubic과 torch antialias bicubic의 차이가 "52-layer ViT / mamba stack을 거치며 증폭돼 HF/vLLM 출력을 갈라놓는다"고 명시했다 ([image_processing.py L117-121](https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16/raw/main/image_processing.py)). transformers에서는 1e-5 수준의 `pixel_values` 차이가 Qwen3-VL bbox를 ~20 unit 흔든 사례도 있다 ([transformers issue #46688](https://github.com/huggingface/transformers/issues/46688)). 따라서 수용 기준은 `pixel_values_flat_video`의 pixel diff가 아니라 greedy 생성 텍스트 A/B여야 한다.

또 C에서 `@torch.compile(dynamic=True)` 함수가 엔진 worker 안에서 처음 실행될 때의 compile 지연, 그리고 메인 모델의 compile/CUDA graph 설정(`embed_multimodal`은 그 범위 밖)과의 상호작용은 검증되지 않았다.

## 다른 스택도 같은 벽에 부딪혔고, upstream vLLM은 EPD로 간다

질문 (4). 세 스택은 각기 다른 답을 택했지만 교훈은 하나로 모인다.

**SGLang**은 frontend(tokenizer manager) process에서 HF fast processor를 `cuda:{base_gpu_id}`로 돌리는 유일한 엔진이다. GPU JPEG decode(`torchvision.io.decode_jpeg(device="cuda")`), torchcodec NVDEC, 그리고 GPU `pixel_values`를 scheduler로 넘기는 `mm_feature_transport = cuda_ipc | cuda_vmm`(tokenizer worker당 persistent CUDA pool, consumer가 pool handle을 cache)을 갖췄다 ([SGLang base_processor.py](https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/multimodal/processors/base_processor.py), [cuda_ipc.py](https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/multimodal/transport/cuda_ipc.py)). 그 대가로 **같은 GPU를 scheduler와 나눠 쓰는 문제**를 그대로 맞았다. KV pool이 GPU를 채운 상태에서 1440p JPEG 한 장의 fp32 중간 tensor(~44 MB)가 OOM을 냈고 ([SGLang issue #42511](https://github.com/sgl-project/sglang/issues/42511)), GPU 전처리 worker를 2개로 늘리자 Qwen-VL이 9.30→4.02 req/s로 후퇴해 "GPU preprocessing → 1 worker"로 못박았다 ([SGLang PR #35349](https://github.com/sgl-project/sglang/pull/35349)).

**TensorRT-LLM**은 보수적이다. HF processor는 frontend thread pool(`--num_input_processor_workers`, 기본 8)에서 CPU로 돌리고 GPU encoding과 overlap하며, process 간 tensor는 `SharedTensorContainer`(CPU는 shm, CUDA는 `reduce_tensor` CUDA IPC)로 넘긴다 ([TRT-LLM Multimodal Support](https://nvidia.github.io/TensorRT-LLM/latest/features/multi-modality.html), [PR #19792](https://github.com/NVIDIA/TensorRT-LLM/pull/19792)). 그들이 찾은 병리는 참고할 만하다. PyTorch intra-op thread 과점으로 1024² 이미지의 processor 시간이 56 thread에서 77–97 ms, 16 thread에서 6–9 ms였다. 우리 쪽은 반대 방향(`OMP_NUM_THREADS=1`로 1080p fp32 resize를 single thread로 수행)이라, 12 process × 2–4 thread를 시험하는 것은 GPU 오프로딩 전에 해볼 값싼 실험이다.

**Dynamo**는 encoder 자체를 별도 GPU "encode worker"로 분리해 embedding을 NIXL(RDMA)로 보내고, 그 worker에서 PyNvVideoCodec/NVDEC를 쓴다. 하지만 vLLM backend에서 `video_url`은 여전히 prefill/PD 경로에 남고, SGLang backend에는 audio encoder 구현이 없다 ([Dynamo Encoder Disaggregation](https://docs.nvidia.com/dynamo/dev/multimodal/encoder-disaggregation.md), [Dynamo SGLang Multimodal](https://docs.nvidia.com/dynamo/dev/knowledge-base/modular-components/backends/sg-lang/sglang-multimodal.md)).

조사한 어떤 serving 스택도 video 전처리를 모델 forward 안에서 하지 않는다(모두 명시적 "processor" stage를 유지). 전처리를 GPU로 옮긴 곳은 예외 없이 (a) LLM이 없는 GPU(encoder-only)에서 하거나 (b) admission control(SGLang의 per-worker pool budget과 1-worker cap, vLLM의 `mm_ipc_gpu_memory_gb`)을 추가해야 했다. 12개 frontend가 B200 한 장을 LLM과 공유하는 우리 배치는 in-frontend 접근에 가장 불리한 경우다.

### upstream vLLM의 궤적은 일관된다

NVIDIA의 RFC #30839(2025-12-17, open)는 PyNvVideoCodec이 VRAM으로 직접 decode하고 `torch.multiprocessing.Queue`의 CUDA IPC로 CoreEngine에 zero-copy 전달하는 co-located 설계였다. H100 + cosmos-reason1-7b + 3 API server + MPS에서 throughput 3.24→3.32 req/s(+2–3%), CPU ~30%→<5%를 보고했다 ([RFC #30839](https://github.com/vllm-project/vllm/issues/30839)). 그 중 transport(#32104 `torch_shm`, 2026-03-21)와 VRAM semaphore(#44465, 2026-06-27)만 merge됐고, draft #31925(DP=TP=1 전용)는 그대로 열려 있다 ([PR #32104](https://github.com/vllm-project/vllm/pull/32104), [PR #31925](https://github.com/vllm-project/vllm/pull/31925)).

그 다음 merge된 유일한 "preprocess on GPU"인 PR #50390(2026-08-05, v0.28.0)은 HF image_processor가 GPU에서 256² 8.6×, 1024² 4.0×, 2048² 2.7×, 4096² 2.3× 빠르다는 표를 들고 왔다. 그러나 **EPD encode-only instance + `torch_shm`에만 허용**했고, "Change 2 is a latency win, not a throughput win"이라고 자평했다 ([PR #50390](https://github.com/vllm-project/vllm/pull/50390)).

PR #53675(2026-09-11, v0.30.0)는 EPD encoder에서 torchcodec `device="cuda"`로 frame을 GPU에 남기는 경로를 추가했다. 격리된 encode-only instance ablation에서 **GPU preprocess가 +220%(2.17→6.95 req/s), 그 위에 zero-copy NVDEC가 +54%(→10.71)**였다 ([PR #53675](https://github.com/vllm-project/vllm/pull/53675), [v0.30.0 release](https://github.com/vllm-project/vllm/releases/tag/v0.30.0)). 이 비율은 우리 결정에 직접 쓰인다. 이득의 대부분은 "transform을 GPU로"에서 오고, "D2H를 없애는 것"은 부차적이다. `pynvvideocodec` backend는 `main`에서도 여전히 host copy를 하며(`video_decoders/pynvvideocodec.py`), upstream이 "frame을 GPU에 남기는" 수단으로 고른 것은 torchcodec이다 ([pynvvideocodec.py @main](https://github.com/vllm-project/vllm/blob/main/vllm/multimodal/video_decoders/pynvvideocodec.py), [config/vllm.py @main L3056-3104](https://github.com/vllm-project/vllm/blob/main/vllm/config/vllm.py)).

| 항목 | 상태 (2026-10-07 기준) | 우리에게 의미 |
|---|---|---|
| RFC #30839 zero-copy NVDEC + IPC (co-located) | open, 2025-12-17 | 우리가 원하는 설계; infra만 merge되고 핵심은 정체 |
| PR #32104 `torch_shm` transport | merged 2026-03-21 (v0.28.0 포함) | GPU tensor 전송 수단 존재; spawn·DP/TP=1 |
| PR #44465 pynvvideocodec + VRAM semaphore | merged 2026-06-27 | D2H 고정; GPU-resident preprocessing은 "future PR" |
| PR #49317 event-loop 직렬화 bug | closed 2026-08-01 (#49608, #49477) | 0.28.0은 renderer thread pool로 전처리를 내림 |
| PR #49462 `mm_tensor_ipc=cuda_ipc` (persistent pool, TP-aware) | open 2026-07-22; v0.31.0에도 미포함 | 12 frontend용 GPU transport의 upstream 후보; `mm_ipc_gpu_memory_gb > 0` 필요 |
| PR #50390 `--mm-processor-device` | merged 2026-08-05 (v0.28.0) | EPD 전용 gate 확정 |
| PR #51349 `paged_shm` cache/transport | open 2026-08-07 | 기본 transport의 copy 비용을 줄이는 대안 |
| Issue #52409 EPD tracker, #52359 EPD refactor | open 2026-08-14/15 | EPD가 공식 방향 |
| PR #53675 torchcodec NVDEC for EPD encoder | merged 2026-09-11 (v0.30.0) | GPU preprocess +220%, zero-copy +54% |
| PR #57752 lazy decode behind processor cache | open experiment 2026-09-20 | cache hit 시 decode 생략; live 반복 세그먼트에 유용 |
| PR #57924 Nemotron VL normalize-on-device | open 2026-09-21 | C-lite의 upstream 버전 |
| PR #58461 pinned memory bound, #52605 lease peak | open 2026-09-23 / 2026-08-17 | C 채택 시 payload 증가와 맞물림 |
| v0.31.0 `--trust-request-mm-kwargs` (#58830), Triton `mm_input_norm` (#56798) | released 2026-10-05 | per-request kwargs 거부; normalize kernel 개선 |
| Q3 2026 roadmap #48168 | mm preprocessing/EPD 항목 없음 | co-located GPU 전처리를 upstream이 먼저 해줄 가능성 낮음 |

관련 링크: [PR #49462](https://github.com/vllm-project/vllm/pull/49462), [PR #51349](https://github.com/vllm-project/vllm/pull/51349), [Issue #52409](https://github.com/vllm-project/vllm/issues/52409), [Issue #52359](https://github.com/vllm-project/vllm/issues/52359), [PR #57752](https://github.com/vllm-project/vllm/pull/57752), [Issue #49317](https://github.com/vllm-project/vllm/issues/49317), [Roadmap #48168](https://github.com/vllm-project/vllm/issues/48168), [v0.29.0](https://github.com/vllm-project/vllm/releases/tag/v0.29.0), [v0.31.0](https://github.com/vllm-project/vllm/releases/tag/v0.31.0)

## 권장 경로: 분배와 cache를 먼저 측정하고, video transform을 엔진 GPU로 옮긴다

질문 (5). 순서가 중요하다. 지금 가진 e2e 숫자는 "12 API server의 병렬 처리"를 전제로 해석됐는데, 원시 로그는 그 전제를 지지하지 않는다. 그러므로 어떤 코드 변경보다 측정이 먼저다.

0.28.0에서는 `TimingContext`가 `get_mm_hashes`, `get_cache_missing_items`, `apply_hf_processor`, `merge_mm_kwargs`, `apply_prompt_updates` 단계를 기록한다. 다만 `ObservabilityConfig.enable_mm_processor_stats`가 "internal use only … not exposed as a CLI argument"라 프로그램적으로 켜야 한다. `vllm bench mm-processor`는 `apply_hf_processor_secs`와 `encoder_forward_secs`를 보여준다 ([context.py L47-77](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/multimodal/processing/context.py#L47-L77), [observability.py L68-71](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/observability.py#L68-L71), [cli/benchmark/mm_processor.py L36-47](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/entrypoints/cli/benchmark/mm_processor.py#L36-L47)).

### 측정 순서

| 순서 | 측정 | 왜 | 어떻게 |
|---|---|---|---|
| 1 | burst 중 API server별 요청 수 | wall ≈ N × 요청당 시간 패턴의 원인 확인; 맞으면 가장 큰 lever | 로그의 `(APIServer pid=…)` prefix별 "Received request" 집계, 12 PID의 `top -H` |
| 2 | `--mm-processor-cache-gb 0`으로 live video-only / audio+video 재측정 | 0.07 vs 0.29와 28.8 vs 7.9를 cache와 오디오로 분리 | 두 행 모두 uncached가 되면 차이는 오디오 몫만 남는다 |
| 3 | 단계별 시간 (`apply_hf_processor_secs`, `encoder_forward_secs`) | "0.27 cpu-s"를 stage 5 단독 값으로 확정 또는 폐기 | `enable_mm_processor_stats` 또는 `vllm bench mm-processor`, 360p 12 frame과 1080p 10/120 frame |
| 4 | `TORCH_LOGS=recompiles` on an API server | rep 1의 행당 ~40 cpu-s 초과분이 compile인지 transform인지; 요청마다 새 `NanoNemotronVLProcessor`/`ParakeetExtractor`가 생성되는 구조(`init_processor`는 cache하지 않음)가 guard 재검사를 유발하는지 | warm-up을 12 API server 모두에, 모든 shape class로 확장 ([e2e_matrix.sh L43-44](file:///Users/garamchoi/pyler/nvdec-poc/bench/e2e_matrix.sh)는 2+2 요청뿐) |
| 5 | `OMP_NUM_THREADS` 2–4 | TRT-LLM이 본 thread 효과의 반대 방향 확인 | 1080p 행에서 cpu-s/req와 req/s 동시 관찰 |
| 6 | 엔진에서 `pixel_values_flat_video.shape` 로깅 | 672×384 확인(다이어그램 560×315 폐기) | 한 요청이면 충분 |
| 7 | B200에서 `_bicubic_resize_and_normalize` CUDA micro-benchmark + CPU/CUDA 출력 diff + greedy text A/B | C/B의 수치 위험과 GPU 비용 산정(측정값 없음) | 12×360p→672×384, 120×1080p→672×384 |

### 측정 뒤의 구현 순서

**Phase 1: 옵션 C(video).** fork patch 2개 파일(`vllm/transformers_utils/processors/nano_nemotron_vl.py`, `vllm/model_executor/models/nano_nemotron_vl.py`)을 모델 수준 opt-in flag로 감싸고, 기존 CPU 경로를 기본값으로 남긴다.

기대 효과는 추정치다. 위 산술이 맞다면 API server당 요청 직렬 시간이 다음과 같이 줄어든다.

| 워크로드 | 현재 (추정) | C 적용 후 (추정) |
|---|---|---|
| 10 s 1080p | ~0.41 s | ~0.10–0.13 s (decode-bound) |
| 120 s 1080p | ~4.7 s | ~1.2–1.5 s |
| live 360p | ~0.13 s | ~0.035 s |

그 결과 **server당 frontend throughput 상한이 3–4×** 열린다(cached rep의 10.5 req/s, 28.9 req/s가 그 "transform 없는" 상한의 미리보기다). 요청당 CPU는 10 s 1080p에서 ~0.3–0.7 cpu-s, 120 s에서 ~3 cpu-s, live에서 ~0.1–0.2 cpu-s가 빠진다(rep 1–2 차이와 audio 행 비교에서 도출, rep 1에는 compile이 섞여 있을 수 있음). 그 지점부터는 GPU encoder/prefill이 병목이 되는데, 고유 콘텐츠에서의 GPU 처리 상한은 PoC에서 한 번도 측정되지 않았다(cached rep는 prefix cache hit로 encoder/prefill도 건너뛰었다). upstream 참조치로는 HF transform의 GPU 가속 2–9×(#50390)와 encoder-side +220%(#53675)가 있다.

**Phase 2: 오디오는 CPU 중복 제거만.** 측정 2가 "오디오 몫 ≈ 0.05 cpu-s"를 확인하면 mel의 GPU 이동은 보류한다. 대신 다음을 한다.

- remux가 이미 여는 PyAV pass에서 audio track도 decode해 video item metadata에 붙인다(S0–S2 중복 제거). `apply()`는 pre-populated audio를 우선 쓴다 ([nano_nemotron_vl.py L685-704](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/model_executor/models/nano_nemotron_vl.py#L685-L704)).
- container MIME에서 libsndfile probe를 생략한다.
- 반복 세그먼트가 있다면 `use_audio_in_video` 분기를 cache-aware로 바꾼다(`<so_embedding>` 주입 후 `_cached_apply_hf_processor` 호출).

waveform-in-model은 "frontend에서 feature 추출을 없앤다"는 아키텍처 요건이 있을 때만, Phase 1과 같은 patch 세트에 얹는다.

**Phase 3: 1080p 비중에 따라.** C-lite(uint8 resized passthrough)와의 혼합 또는 B(lease 안 frontend resize)를 검토한다. 단, B는 `--mm-ipc-gpu-memory-gb`를 켜고 lease를 fp32 중간값까지 확장한 뒤, `CUDA_MPS_ACTIVE_THREAD_PERCENTAGE`로 frontend SM을 묶은 상태에서만 시험한다.

upstream 기여는 C-lite(PR #57924 리뷰/보강)가 가장 빠르다. C는 "resize-in-forward" 선례가 없어 `mm_device_do_normalize`처럼 모델 opt-in flag로 RFC를 먼저 내는 편이 낫다.

### 하지 말아야 할 것

- **옵션 A**(`--mm-processor-device`/`device` kwarg + `torch_shm`)는 세 지점에서 막혀 있다. 뚫어도 12 process의 unbudgeted VRAM(cache를 끄지 않으면 process당 최대 4 GiB의 CUDA tensor LRU까지)과 SM 경합을 떠안는다. SGLang이 측정한 후퇴가 바로 그 모습이다.
- **NVDEC→processor zero-copy**는 8 MB짜리 pinned D2H를 없애려고 ms 단위 이득에 6곳 patch를 거는 일이다. #53675 ablation도 그것이 작은 쪽 이득임을 보여준다.
- **B200 한 장의 EPD**는 instance 2개와 proxy, connector(0.28.0은 disk/CPU-mmap)를 추가하면서도 Nemotron processor의 device plumbing 부재는 그대로 남긴다. multi-GPU로 갈 때 다시 본다.
- **DALI/CV-CUDA**는 세 번째 resize 구현을 들여와 수치 drift를 더하고, DALI는 process당 grow-only pool까지 가진다.
- **GPU audio decode**는 불가능하고, **GPU mel**은 ms 이득이다.
- **`torch_shm`을 CPU tensor에만 쓰는 것**은 RFC prototype의 +2–3%가 보여주듯 throughput에 거의 보탬이 없다.
- 마지막으로, 측정 1이 "요청 집중"을 확인한다면 GPU 오프로딩은 두 번째 문제다.

## 검증된 사실, 추론, 그리고 남은 공백

이 보고서에서 "코드 확인"은 두 가지를 뜻한다. 하나는 연구 노트가 v0.28.0 clone(`2cf0a69`, 2026-08-24; release 2026-08-26)에서 line 단위로 읽고 GitHub permalink를 붙인 사실이다. 다른 하나는 PoC repo의 `REPORT.md`, `patches/nvdec_mpegts.py`, `bench/e2e_matrix.sh`, `bench/load_test.py`, `results/run_all_2026-09-17.log`에서 직접 읽은 수치다. 그 외는 추론이다.

| 주장 | 근거 수준 |
|---|---|
| flag만으로는 stage 5/6을 GPU에서 못 돌린다 (validator, processor signature, `_postprocess_output`, backend D2H 계약) | 코드 확인 (line 인용) |
| per-request `device` kwarg → `TypeError` | 코드 추적; 실제 HTTP 응답은 미실행 |
| target 672×384(upscale), tubelet당 252 token, 12 frame = 1512 token | 코드 확인 + 산술; prompt_tokens 1705와 정합 (증명 아님) |
| patchify는 엔진 GPU(`Im2Patches`) | 코드 확인 |
| transport = msgpack + OOB buffer over ZMQ, cache = `processor_only` (api-server-count 12) | 코드 확인 |
| 12 API server 고정 예산 ≈ 24.6 GiB; PoC는 `--mm-ipc-gpu-memory-gb` 미설정 → pool 없음 | 상수·공식에서 산술 + serve script 확인; `mm_ipc_gpu_memory_gb=0`일 때 고정분 차감 조건의 세부는 노트의 서술에 의존 |
| 오디오 고유 비용 ≈ 0.05 cpu-s, 0.07→0.29는 cache 효과 | 로그 수치 확인 + 추론 (VOD 10 s 행 비교) |
| 64 요청이 사실상 하나의 API server에 직렬화 | 로그 산술에서 나온 **가설**; 메커니즘(공유 listen socket + accept burst)은 미확인 |
| 1080p frame당 transform ≈ 27 ms, 360p ≈ 8 ms | 위 가설 하의 **파생 추정**; 측정 3으로 대체해야 |
| rep 1의 행당 ~40 cpu-s 초과분 | compile(고정)과 transform(frame 비례) 두 모델이 모두 3개 점에 맞음; 미분리 |
| C의 기대 효과(3–4× server당 상한) | cached rep을 상한의 대리로 쓴 추정; 고유 콘텐츠의 GPU 상한 미측정 |
| GPU bicubic antialias의 B200 비용·수치 동일성, cuFFT mel 동일성 | 미측정 |
| `torch_shm` + CUDA tensor + MPS on B200 | upstream test/문서 없음; `expandable_segments`와 CUDA IPC export 상호작용도 미확인 |
| 1.8 GiB context 상수 | H100 측정값; B200 값 없음 |
| HF repo `video_processing.py`의 `device` 지원 | 코드 확인했으나 이 checkpoint에서 dead code(`attributes`에 없음); vLLM 경로와 무관 |
| `nemotron_omni_processing.md`의 마지막 절 | 작성자가 rate limit으로 중단됨; 옵션 (a)/(b)/(c) 비교는 있으나 망라적이라 가정하지 않음 |

### 남은 공백

측정표의 1–7 외에 다음이 남아 있다.

- `torch_shm` 아래에서 P0 `processor_only` LRU가 CUDA tensor를 유지하는지(코드 구조에서 추론, 실행 미확인)
- vLLM이 `queue.put` 후 sender reference를 버릴 때 PyTorch의 keep-alive 규칙과 어떻게 맞물리는지(upstream 논의 없음)
- EVS(`--video-pruning-rate`, HF README 권장 0.5이나 PoC는 미설정)를 켰을 때 C의 `rows/cols` 계산 경로
- 0.29→0.31 이동 시 PyAV backend 제거(#54231), `--trust-request-mm-kwargs`, receiver-cache 수정(#57833)의 영향
- 운영 live-ingest 트래픽의 도착 패턴(burst 여부)

## 결론

이 질문의 답은 기술적 불가능이 아니라 upstream의 선택에서 온다. vLLM은 "frontend process가 엔진 GPU를 건드리는" 설계를 EPD encode-only instance라는 울타리 안에만 허용하기로 했다. 그 결정은 validator의 에러 메시지, #44465의 "community first" 보류, #50390/#53675의 EPD 전용 gate로 일관되게 코드에 박혀 있다. 그래서 co-located B200 한 장에서 "NVDEC부터 encoder까지 GPU chain을 끊지 않는다"를 문자 그대로 구현하려면 upstream과 반대 방향으로 6곳을 패치해야 하고, 얻는 것은 ms 단위의 D2H다.

목표를 "host hop 제거"가 아니라 "CPU compute stage 제거"로 다시 쓰면 답이 단순해진다. compute(resize/normalize)는 엔진 forward 안으로 옮기고, hop(8 MB pinned copy + ZMQ)은 그대로 둔다. 이것이 upstream의 `mm_device_do_normalize` 계보와도 맞고, profiling과 메모리 회계도 공짜로 따라온다.

더 중요한 시사점은 측정에서 왔다. PoC의 e2e 표는 cache hit와 miss를 평균냈다. 오디오의 비용으로 보였던 것은 cache miss의 비용이었다. wall time은 12개 API server가 아니라 한 개가 일하는 것처럼 떨어진다. 이 세 가지를 풀기 전의 GPU 오프로딩은 측정되지 않은 병목을 겨냥하는 셈이다.

분배가 확인되고 transform이 엔진으로 가면, 그 다음 병목은 아마 `requires_sequential_video_encoding`이 강제하는 video 단위 순차 encoder와 pinned memory 증가일 것이다. 그때는 EPD가 아니라 upstream의 encoder batching과 #58461 같은 fix를 따라가는 것이 B200 한 장짜리 배포에 맞는 길이다.
