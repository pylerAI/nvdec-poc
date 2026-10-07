# Multimodal LLM Serving을 위한 GPU Video Decoding: NVIDIA B200에서의 NVDEC (PyNvVideoCodec) vs. CPU Decoding

**Pyler Platform Team — 2026년 9월**

## 요약 (Abstract)

Video understanding 서비스는 모델과 전혀 무관한 단계, 즉 H.264를 frame으로 decode하는 데 의외로 많은 compute를 쓴다. 본 보고서는 이 단계를 CPU(OpenCV/FFmpeg)에서 PyNvVideoCodec을 통한 GPU의 NVDEC engine으로 옮겼을 때 NVIDIA B200 한 장이 얻는 이득을 세 가지 레벨에서 정량화한다: (i) raw decode throughput, (ii) vLLM video loader의 decode stage(sampled frame만), (iii) vLLM 0.28로 30B multimodal 모델(NVIDIA Nemotron 3 Nano Omni 30B-A3B)을 end-to-end serving. CUDA MPS를 켜면 1080p H.264 raw decode는 **NVDEC에서 CPU core 2개로 12,200 frames/s**, **CPU에서는 57 core로 4,760 frames/s**에 도달한다. CPU core당 frame 수로는 60–120배다. MPS가 없으면 multi-process NVDEC은 context time-slicing 때문에 ~2,300 frames/s에서 막힌다. vLLM loader에서 1080p shot의 clip당 decode latency는 **2.0×(10 s), 2.0×(30 s), 5.3×(120 s)** 개선되는데, NVDEC 경로가 sampled frame이 들어 있는 GOP만 decode하기 때문이다. End-to-end에서는 64-core host에 API-server process 12개를 띄운 환경에서 NVDEC이 request당 server CPU를 **360p live segment에서 3.3×, 1080p VOD에서 7.8–10.7×** 줄이고, 1080p request의 p50 latency를 13–31 % 낮추면서 throughput은 15–32 % 높인다. 아울러 이득이 작은 경우(CPU 제약이 없는 환경의 짧은 360p segment), process당 NVDEC throughput을 제한하는 Python binding의 serialization, 그리고 stream-copy remux로 우회해야 했던 PyNvVideoCodec의 MPEG-TS 한계도 함께 보고한다.

## 1. 서론

Multimodal LLM은 video를 소수의 sampled frame(보통 content 1초당 1–2 frame)으로 받아들이지만, 그 frame을 만들려면 압축된 stream을 demux하고 decode해야 한다. vLLM 같은 serving stack에서는 이 작업이 GPU를 구동하는 바로 그 host의 CPU에서, API-server process 안에서 돌아간다. 모델은 점점 빨라지고 host는 CPU socket당 더 많은 GPU를 싣게 되면서, decode stage는 모델 크기가 아니라 해상도와 clip 길이에 비례해 커지는, request마다 붙는 고정 CPU 비용(CPU tax)이 된다.

NVIDIA GPU에는 전용 NVDEC engine(B200에는 7개)이 있고, 이 engine들은 LLM inference 중에는 놀고 있다. vLLM 0.27+는 `pynvvideocodec` video backend를 통해 이 engine을 쓸 수 있게 해 준다. 이 PoC의 질문은 좁다: **B200 한 장에서, multimodal LLM server의 frame-sampling workload에 대해 NVDEC/PyNvVideoCodec이 일반 CPU decoding보다 얼마나 나은가?** 이를 위해 두 가지 현실적인 입력(6초짜리 640×360 HLS MPEG-TS live segment, 그리고 10·30·120초 길이의 1080p VOD shot)과, decoder·loader·전체 serving 경로를 각각 분리해 보는 세 가지 측정 레벨을 사용한다.

## 2. 테스트 대상 시스템 (System under test)

### 2.1 하드웨어 및 소프트웨어

| | |
|---|---|
| GPU | NVIDIA B200 1장 (183 GB), driver 580.126.09; pod의 두 번째 GPU는 사용하지 않음 (`CUDA_VISIBLE_DEVICES=0`) |
| CPU | Intel Xeon Platinum 8570; container cgroup quota **64 cores** (host가 노출하는 core는 224개) |
| Decoders | NVDEC: PyNvVideoCodec 2.1.1 (`__version__` 기준; pip metadata는 2.0.4); CPU: OpenCV 5.0.0 (FFmpeg avcodec 62.28) |
| Serving | vLLM 0.28.0 (V1 engine), `--api-server-count 12`, torch 2.13 + CUDA 13.0, PyAV 16.1 |
| Model | `nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16`, `--reasoning-parser nemotron_v3`, `enable_thinking=false`, `max_tokens 64` |
| GPU sharing | NVDEC configuration에서 CUDA MPS (`nvidia-cuda-mps-control -d`) 사용. 12개 API-server의 CUDA context와 engine이 GPU를 동시에 공유함 |
| Env | `NVIDIA_DRIVER_CAPABILITIES=video,compute,utility`, `OMP_NUM_THREADS=1` |

### 2.2 비교 대상 decode 경로

- **CPU (`opencv`)**: vLLM의 기본 video backend. `cv2.VideoCapture`가 모든 frame을 순차적으로 decode하고(FFmpeg auto-threading, 1080p stream당 ~6 thread) 그중 sampled frame만 남긴다.
- **NVDEC (`pynvvideocodec`)**: vLLM의 PyNvVideoCodec backend. scanned stream metadata를 쓰는 `SimpleDecoder`가 index로 요청한 frame만 decode하므로(`get_batch_frames_by_index`) sampled frame이 들어 있는 GOP만 decode된다. decoder object는 `reconfigure_decoder`로 request 간에 재사용한다(process당 cached decoder slot `hw_decoders=2`개). Decode된 frame은 device memory에 올라간 뒤 HF processor를 위해 pinned host memory로 copy된다.
- **MPEG-TS patch (`patches/nvdec_mpegts.py`)**: PyNvVideoCodec은 MPEG-TS를 index하지 못한다(§5.3). 우리의 build-time patch는 0x47 sync byte로 TS를 감지하고, PyAV로 video track을 메모리 상의 fragmented MP4로 stream-copy한 다음(re-encode 없음, 6 s segment 기준 ~5 ms) 수정하지 않은 vLLM의 MP4 경로를 그대로 탄다. `use_audio_in_video`용 audio는 vLLM의 audio loader가 원본 bytes에서 읽는다.

초기 설계는 request마다 `CreateDemuxer`+`CreateDecoder`를 새로 만들고 segment 전체를 decode했는데, 6 s segment당 ~300 ms가 들었다(위 설계는 20 ms). decoder 재사용만으로 9배 차이가 난다(clip당 297 ms → 33 ms. `CreateDecoder` 자체는 1.7 ms이고, 실제 비용은 처음 decode되는 frame들에서 치른다). 이는 decoder를 재사용하고 필요한 것만 decode하라는 NVIDIA DevTech의 가이드를 따른 것이다.

## 3. 방법론

### 3.1 입력

- **Live segment**: 6.0 s MPEG-TS, H.264 640×360 @ 29.97 fps (182 frames) + AAC track 1개, 0.4 MB. 전형적인 HLS segment 형태다. 2 fps로 sampling → 12 frames.
- **VOD shots**: 42.9분 길이의 1080p H.264 title(955 MB)을 고정 길이 shot으로 자른 뒤 closed GOP로 re-encode했다(`libx264 -preset veryfast -g 30 -sc_threshold 0`; NVDEC의 indexer는 open-GOP cut을 거부한다, §5.3): 64×10 s (6.2 MB, 307 frames), 32×30 s (17 MB), 8×120 s (61 MB, 3,633 frames). 1 fps로 sampling하고 최대 128 frame(`num_frames`)으로 cap했다. 1080p에 대한 model card 권장값이다.

### 3.2 세 가지 측정 레벨

1. **Raw decode** (`bench/raw_decode_bench.py`): 1–16개의 worker process에서 clip의 *모든* frame을 decode한다. 각 worker는 재사용되는 decoder 1개(`CreateDecoder`, device memory에 RGB output) 또는 `cv2.VideoCapture` 1개를 가진다. Worker들은 warm-up 후 barrier에서 동기화하고 clip을 3–5회 decode한다. 가장 느린 worker의 구간 기준 frames/s와 `getrusage`로 얻은 CPU seconds를 보고한다. NVDEC은 MPS를 켠 경우와 끈 경우를 모두 측정한다.
2. **Decode stage** (`bench/vod_loader_bench.py`): vLLM 자체 loader(`VideoMediaIO.load_bytes`)를 각 backend로 돌리므로 container 처리, frame sampling, host copy가 모두 포함된다. 순차 실행 시 clip당 median latency와, 한 process 안에서 8 thread로 돌렸을 때의 throughput을 잰다. **3회 반복.**
3. **End-to-end** (`bench/e2e_matrix.sh`, `bench/load_test.py`): API server 12개로 `vllm serve`를 띄우고, 같은 pod 안의 client가 clip을 base64 data URL로 담은 chat-completion request N개를 동시에 보낸다(live: N = 64, 2 fps, `use_audio_in_video` 유무 각각; VOD: 1 fps로 64×10 s, 32×30 s, 8×120 s). Client 측 latency percentile과 throughput, **pod cgroup 기준 server CPU**(`cpu.stat` delta ÷ request 수), GPU SM/NVDEC utilization(`nvidia-smi dmon`, 1 s 간격)을 기록한다. 각 configuration은 한 번 기동하고(cache가 빈 상태) request 2개로 warm-up한 뒤 matrix를 **3회** 실행하며, 평균값을 보고한다. 두 configuration의 차이는 `--media-io-kwargs`(`backend`)와 MPS뿐이다.

Live test는 64개 request 모두에 같은 segment 하나를 재사용하므로 vLLM의 prefix cache와 multimodal-processor cache에 hit한다. 따라서 절대 latency는 낙관적인 값으로 보고, configuration 간 상대 비교에만 사용한다. VOD test는 서로 다른 clip을 사용한다.

## 4. 결과

### 4.1 Raw decode: NVDEC은 frame당 CPU를 ~1/60만 쓰며, process 간 scaling에는 MPS가 필요하다

1080p H.264, 307-frame clip, 전체 worker 합산 (`results/summary.md`, section A/A′):

| Workers | CPU (OpenCV) frames/s | 사용 CPU cores | NVDEC frames/s, **MPS on** | cores | NVDEC frames/s, MPS off | cores |
|---|---|---|---|---|---|---|
| 1 | 694 | 6.4 | 2,189 | 0.2 | 2,188 | 0.2 |
| 2 | 1,325 | 13.0 | 4,274 | 0.3 | 2,630 | 1.7 |
| 4 | 2,431 | 25.7 | 8,242 | 0.8 | 2,290 | 4.0 |
| 8 | **4,763** | 57.3 | 11,823 | 1.3 | 2,258 | 8.0 |
| 16 | 2,802 | 62.9 | **12,178** | 2.0 | 2,227 | 16.0 |

CPU core당 OpenCV/FFmpeg은 1080p H.264를 83–109 frames/s 처리한다. 반면 NVDEC에서는 CPU가 demux와 packet submit만 하므로 *host* CPU core당 6,000–13,500 frames/s가 나온다. 64-core quota에서 CPU 경로는 4,763 frames/s(≈ real-time 1080p30 stream 159개)에서 정점을 찍고, oversubscription(16 workers × 6 FFmpeg threads) 상태가 되면 무너진다. B200 한 장의 NVDEC engine은 core 2개만 쓰면서 12,178 frames/s(≈ real-time stream 406개)를 내므로, 나머지 CPU는 다른 작업에 쓸 수 있다. 640×360에서도 절대 수치만 높을 뿐 양상은 같다: CPU는 62.5 core로 32,033 frames/s, NVDEC은 6.3 core로 51,202 frames/s.

**MPS는 선택이 아니라 필수다.** MPS가 없으면 NVDEC worker마다 자기 CUDA context를 가지고, 이 context들이 time-slicing된다. 그 결과 worker 수나 해상도와 무관하게 aggregate throughput이 ~2,300 frames/s에 머물고(360p에서도 1080p와 같은 2,320 frames/s), 각 worker는 synchronization에서 spin하느라 core 하나를 통째로 태운다(worker 8개에 8.0 core). MPS를 켜면 같은 코드가 5.4배 scaling되고 CPU 사용량은 6분의 1로 줄어든다. API-server process 12개로 띄운 vLLM deployment가 바로 이 multi-process 패턴이다.

### 4.2 vLLM loader의 decode stage: 1080p는 latency 2–5배 감소, 360p는 동등

3회 반복 평균(괄호 안은 범위). 순차 실행 시 clip당 median과, single process 8-thread throughput:

| Clip | Sampled frames | CPU (opencv) | NVDEC (pynvvideocodec) | Speed-up | Throughput CPU → NVDEC (clips/s, 1 process) |
|---|---|---|---|---|---|
| VOD 10 s 1080p, 1 fps | 10 | 258 ms (248–272) | **132 ms** (130–133) | 2.0× | 18.8 → 9.9 |
| VOD 30 s 1080p, 1 fps | 31 | 688 ms (680–702) | **350 ms** (348–352) | 2.0× | 6.9 → 3.7 |
| VOD 120 s 1080p, 1 fps | 32 (cap) | 2,132 ms (2,068–2,221) | **404 ms** (398–409) | **5.3×** | 2.2 → 3.2 |
| Live 6 s 360p TS, 2 fps | 12 | 32 ms (29–34) | 28 ms (26–31) | 1.1× | 115 → 50 |

Clip이 길수록 speed-up이 커지는 이유는 이렇다. CPU 경로는 32 frame을 얻으려고 120 s clip의 3,633 frame을 전부 decode하지만, NVDEC 경로는 각 sampled frame이 속한 GOP(30 frames)로 seek해서 ~32 × 30 frame만 decode한다. 6초짜리 360p segment에서는 아낄 것이 별로 없다. 두 경로 모두 ~30 ms에 끝나며, NVDEC 쪽은 그중 remux가 5 ms, NVDEC decode 자체가 20 ms다.

Throughput 열은 hardware가 아니라 Python binding의 한계를 보여 준다. 한 process 안에서 NVDEC 8 thread는 `hw_decoders` 값과 상관없이(slot 2, 4, 7개 모두 같은 수치) 10 s 1080p clip을 9.9 clips/s 처리하는 반면, GIL을 해제하는 OpenCV는 18.8까지 간다. `SimpleDecoder` 호출이 GIL 아래에서 serialize되기 때문이다. §4.1에서 봤듯 engine 자체에는 10배의 headroom이 있고, §4.3에서 확인하듯 vLLM의 multi-process front end가 이 headroom을 되찾아 준다.

### 4.3 End-to-end serving: request당 CPU 3–11배 감소, 1080p latency 13–31 % 감소

B200 한 장에서 Nemotron 3 Nano Omni, API server 12개, 64-core quota; 3회 반복 평균 (`results/summary.md`, section C):

| Workload | N | Decode | p50 | p95 | req/s | request당 server CPU | CPU 절감 |
|---|---|---|---|---|---|---|---|
| Live 6 s 360p TS, video | 64 | CPU | 1.9 s | 2.0 s | 32.4 | 0.23 cpu-s | |
| | | **NVDEC + MPS** | 2.1 s | 2.2 s | 28.8 | **0.07 cpu-s** | **3.3×** |
| Live 6 s 360p TS, audio+video | 64 | CPU | 5.0 s | 7.9 s | 7.8 | 0.48 cpu-s | |
| | | **NVDEC + MPS** | 5.1 s | 7.8 s | 7.9 | **0.29 cpu-s** | 1.7× |
| VOD 10 s 1080p ×64 | 64 | CPU | 8.9 s | 13.3 s | 6.7 | 3.34 cpu-s | |
| | | **NVDEC + MPS** | **7.7 s** | **11.7 s** | **7.9** | **0.43 cpu-s** | **7.8×** |
| VOD 30 s 1080p ×32 | 32 | CPU | 14.3 s | 20.4 s | 2.6 | 9.25 cpu-s | |
| | | **NVDEC + MPS** | **9.8 s** | **16.3 s** | **3.0** | **0.97 cpu-s** | **9.5×** |
| VOD 120 s 1080p ×8 | 8 | CPU | 18.2 s | 24.1 s | 0.5 | 36.45 cpu-s | |
| | | **NVDEC + MPS** | **12.9 s** | **18.3 s** | **0.6** | **3.42 cpu-s** | **10.7×** |
| VOD 10 s 1080p ×64, audio+video | 64 | CPU | 18.0 s | 30.5 s | 1.9 | 3.97 cpu-s | |
| | | **NVDEC + MPS** | **14.2 s** | **23.4 s** | **2.5** | **0.93 cpu-s** | 4.3× |

두 configuration 모두 1,536개 request가 전부 성공했다. 세 가지 패턴이 보인다.

1. **NVDEC이 확실하게 이기는 지점은 request당 CPU다.** 1080p content에서 server는 CPU 경로로 request당 3.3–36 cpu-s를 쓰는데(120 s shot이라면 32 frame을 만드는 데 36 core-seconds), NVDEC에서는 0.4–3.4 cpu-s만 쓴다. NVDEC 경로에 남은 CPU는 decoding이 아니라 HF image processor, tokenization, pinned-host copy에서 나온다. 360p live segment는 어느 쪽이든 절대 수치가 작다(0.23 vs 0.07 cpu-s).
2. **Decode가 request에서 눈에 띄는 비중을 차지할 때 latency가 개선된다.** 64개의 동시 1080p request가 API server 12개에 나뉘면 server마다 clip ~5개를 연달아 decode한다. §4.2의 2–5배 decode-stage 이득은 여기서 p50 13 %(10 s), 31 %(30 s), 29 %(120 s) 감소와 throughput 15–32 % 증가로 이어진다. 6초짜리 360p segment의 video-only 경로에서는 NVDEC이 오히려 0.2 s *느리다*. decode는 양쪽 모두 ~30 ms인데, NVDEC frame은 processor에 도달하기 전에 별도의 CUDA context와 device→host copy를 거쳐야 하기 때문이다.
3. **GPU가 decode-bound가 되는 일은 없다.** 실행 중 NVDEC utilization peak는 21–28 %였고, VOD prefill 동안 SM utilization은 30–50 %였다. 이 정도 부하에서는 decode와 inference가 MPS로 B200을 공유해도 측정할 만한 간섭이 없다.

audio+video 행은 모든 request에 Nemotron의 speech encoder와 vLLM의 audio loader(PyAV, CPU)가 더해진 경우다. decode 쪽 절감은 그대로지만(0.48 → 0.29, 3.97 → 0.93 cpu-s), latency는 audio 경로가 좌우하며 이는 본 비교의 범위 밖이다.

## 5. 논의

### 5.1 Capacity planning 관점에서 본 수치의 의미

이 이득은 무엇보다 *CPU* 이득이다. 1080p request 하나에 CPU 경로는 3.3(10 s)에서 36(120 s) core-seconds가 필요하다. 따라서 GPU당 *c*개의 core를 가진 host는 초당 최대 *c*/3.3에서 *c*/36개의 request만 preprocess할 수 있고, 그 이상에서는 GPU가 아니라 CPU가 상한을 정한다. NVDEC을 쓰면 같은 상한이 8–11배 높아지며, 우리 실험에서 throughput을 제한한 것은 1.6k–17k개 visual token에 대한 GPU의 prefill이었다. 애초에 B200을 사는 이유가 바로 이 자원이다. GPU당 core가 적은 host(예: shared node의 16-core pod quota)에서는 이것이 decode-bound service냐 model-bound service냐를 가르는 차이가 되고, 64-core testbed에서도 latency 13–31 % 감소로 나타난다.

### 5.2 NVDEC이 도움이 되지 않는 경우

짧은 저해상도 clip은 어느 경로든 수십 ms 안에 decode된다. 이 경우에는 CUDA context hop과 host copy 비용이 절약분을 상쇄한다. 입력이 전부 ≤ 480p의 짧은 segment인 팀이라면 CPU 절감(3배)은 기대할 수 있지만 latency 절감은 없으므로, MPS 운영 부담과 저울질해 봐야 한다.

### 5.3 현재 stack의 한계 (상세 내용과 재현 방법은 `docs/nvidia-issues.md` 참고)

- **MPEG-TS.** PyNvVideoCodec demuxer의 `Seek`/`TimestampFromFrame`은 TS에서 SIGSEGV가 나고, `SimpleDecoder(need_scanned_stream_metadata=True)`는 TS를 index하지 못한다. Native TS indexing이 들어오기 전까지는 fragmented MP4로의 5 ms stream-copy remux가 현실적인 workaround다.
- **Open-GOP cuts.** non-IDR keyframe에서 자른 shot은 "Decode Error occurred for picture N" 이후 `get_batch_frames_by_index`에서 `IndexError`가 난다. FFmpeg은 같은 clip을 문제없이 처리한다. closed GOP로 re-encode하거나 IDR frame에서 잘라야 한다.
- **Per-process serialization.** `SimpleDecoder`가 GIL을 잡고 있어서, 한 process는 10 s 1080p clip 기준 ~10 decodes/s를 넘지 못한다. Multi-process front end(vLLM의 `--api-server-count`)는 hardware의 headroom을 되찾지만, single-process integration은 그렇지 못하다.
- **MPS dependence.** MPS 없는 multi-process NVDEC은 context time-slicing 때문에 ~2,300 frames/s에서 막히고 process마다 core 하나를 태운다(§4.1). Inference GPU에서 둘 이상의 process가 decode하는 deployment라면 반드시 MPS를 띄워야 한다.
- **Warm-up placement.** 새 decoder의 비용(~300 ms)은 `CreateDecoder` 시점이 아니라 처음 몇 frame을 decode할 때 발생한다. 짧은 clip에서는 decoder 재사용(`reconfigure_decoder`)이 필수다.

## 6. 결론

B200 한 장에서 CUDA MPS로 여러 process가 engine을 공유하게 하면, PyNvVideoCodec 기반 NVDEC은 CPU core 2개로 1080p H.264를 12,200 frames/s decode한다. FFmpeg은 4,760 frames/s에 57 core가 필요하므로, CPU core당 frame 수로 60–120배 개선이다. vLLM 내부에서 1080p shot의 sampled-frame decode는 2–5배 빨라지고, 30B multimodal 모델의 end-to-end serving에서 1080p 입력은 request당 server CPU를 3–11배 덜 쓰면서 latency도 13–31 % 낮아진다. 짧은 360p segment는 CPU 이득은 있지만 latency 이득은 없다. 남은 과제는 upstream 쪽이다: PyNvVideoCodec의 native MPEG-TS indexing과 GIL-free decode 호출.

## 7. 재현 방법

```
patches/nvdec_mpegts.py     vLLM 0.28.0 build-time patch: PyNvVideoCodec 경로 진입 전 MPEG-TS -> in-memory fMP4 remux
bench/raw_decode_bench.py   §4.1  raw decode throughput, N processes, cv2 vs PyNvVideoCodec (MPS on/off 각각 실행)
bench/vod_loader_bench.py   §4.2  vLLM VideoMediaIO를 통한 decode stage (BACKENDS, HW_DECODERS)
bench/e2e_matrix.sh         §4.3  media-io config로 vLLM (Nemotron 3 Nano Omni) 기동 후 matrix 3회 실행
bench/load_test.py          data-URL video를 담은 동시 OpenAI-API load (ENDPOINT VIDEO N USE_AUDIO FPS MEDIA_IO)
bench/run_all.sh            이 보고서를 위해 실제로 실행한 전체 chain; bench/summarize.py -> results/summary.md
bench/cut_shots.py          stream-copy shot cutter (이후 closed GOP로 re-encode 필요)
bench/nvdec_advice_bench.py, bench/remux_vllm_pattern.py   PyNvVideoCodec microbenchmark (decoder 재사용, seek, remux)
results/run_all_2026-09-17.log   위에 인용한 모든 수치의 raw log; results/summary.md   표
```

Serve flag (NVDEC configuration): `vllm serve nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 --trust-remote-code --api-server-count 12 --max-model-len 32768 --limit-mm-per-prompt '{"video":1,"audio":1}' --media-io-kwargs '{"video":{"backend":"pynvvideocodec","hw_decoders":2,"fps":1,"num_frames":128}}' --reasoning-parser nemotron_v3`. 실행 전에 `nvidia-cuda-mps-control -d`를 먼저 띄우고, `NVIDIA_DRIVER_CAPABILITIES=video,compute,utility`, `OMP_NUM_THREADS=1`을 설정한다. CPU configuration은 `"backend":"opencv"`를 쓰고 MPS는 쓰지 않는다.

## 감사의 글

MPEG-TS patch 설계의 바탕이 된 decoder caching 및 sampled decode 가이드를 제공해 준 NVIDIA video DevTech(2026-09-12 미팅)에 감사드린다.
