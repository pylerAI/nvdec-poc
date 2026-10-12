# Qwen3-Omni(운영 모델) 라이브 6초 360p MPEG-TS, 1~9단계 실측 (2026-10-07)

운영 live-ingest 엔드포인트와 같은 모델·서버 인자·요청 모양으로 [live360_stages_2026-10-07.md](live360_stages_2026-10-07.md)(Nemotron)와 같은 단계별 측정을 했다. B200 1장(`dgx-b200-01`, GPU 0), vLLM 0.28.0, `Qwen3-Omni-30B-A3B-Instruct`. 모든 요청은 미디어 캐시를 빗나가고, 시스템 프롬프트는 운영처럼 프리픽스 캐시에 맞는다. 단계별 표 전체는 [qwen3omni_live360_2026-10-07_stages.md](qwen3omni_live360_2026-10-07_stages.md), 원시 데이터는 [qwen3omni_live360_2026-10-07_raw.tar.gz](qwen3omni_live360_2026-10-07_raw.tar.gz), 실행 로그는 [qwen3omni_live360_2026-10-07_chain.log](qwen3omni_live360_2026-10-07_chain.log)에 있다.

## 요약

1. **운영 요청 모양에서는 생성(9번)이 지배한다.** 1건 1.92 s 중 생성이 1.63 s(85%)다. 시스템 프롬프트 약 4,000토큰(프리픽스 캐시 적중)에 비디오 1,320 + 오디오 82토큰을 붙여 JSON 약 230토큰을 토큰당 7.0 ms로 뽑는다. 64동시에서는 생성 8.8 s(토큰당 38 ms) > 프리필 3.6 s > 프론트엔드 0.5 s이고 p50 14.6 s, 처리량 4.2 req/s다.
2. **구조화 출력(xgrammar)이 64동시 생성 시간을 약 2배로 늘린다.** 같은 프롬프트에서 `response_format`만 빼면 토큰당 36~44 ms → 16~24 ms, 64동시 p50 14.6 → 9.5~10.1 s다. 1건에서는 7.0 vs 6.8 ms로 차이가 없다. 동시 요청 수에 비례하는 CPU 비용이다. 다만 문법 없이는 영상만 요청의 출력 길이가 4~600토큰으로 불안정해진다.
3. **오디오+영상 요청은 인코더를 항목마다 따로 부른다.** 러너가 요청 순서대로 [영상, 오디오, 영상, 오디오…]를 넘기고 `group_and_batch_mm_kwargs`는 연속된 같은 모달리티만 묶기 때문에, 64동시 av 버스트에서 비전 64회(41 ms) + 오디오 64회(37 ms) = 5.0 s가 직렬로 든다. 영상만 요청은 16개씩 묶여 버스트당 약 1 s다. 프리필 p50 3.6 s(av) vs 1.2 s(v)의 차이가 여기서 난다.
4. **운영 모양에서 NVDEC은 지연 이득이 없고, 64동시에서는 CPU 디코드 구성이 약 1초(7%) 빠르다.** 디코드 자체는 NVDEC 22 ms vs OpenCV 55 ms로 빠르지만 요청의 1~3%라 묻히고, 12개 API 서버의 CUDA 컨텍스트가 디코드·동기화를 하며 엔진과 GPU를 나눠 쓰는 비용이 더 크다. MPS 자체의 비용은 작다(CPU 디코드 + MPS 켬 ≈ CPU 디코드). MPS 없이 NVDEC을 쓰면 64동시 디코드가 53 → 973 ms로 터진다(컨텍스트 타임슬라이싱, API 서버 CPU 0.74 cpu-s/요청). NVDEC의 이득은 API 서버 CPU(요청당 0.16 vs 0.40 cpu-s)뿐이다.
5. **Nemotron과 비교하면 Qwen3-Omni의 영상 인코더는 배치가 된다**(영상만일 때 16개/호출, 영상당 6 ms). 전처리(5번)도 30~59 ms로 Nemotron(80~112 ms)보다 싸다(672×384 업스케일 대신 640×352 유지).

## 운영 모양 (측정에 그대로 사용)

| 항목 | 값 | 출처 |
|---|---|---|
| 서버 | `vllm serve` `--api-server-count 12`, `--max-model-len 49152`, `--max-num-batched-tokens 49152`, `--gpu-memory-utilization 0.9`, `--mm-processor-kwargs {"max_pixels":313600,"fps":2.0}`, `--structured-outputs-config {"backend":"xgrammar","disable_any_whitespace":true}`, `--limit-mm-per-prompt {"video":1,"audio":1}`, `ENABLE_MPS=true`, `OMP_NUM_THREADS=1` | `iac` `helm/charts/vllm-serving/values.yaml` `qwen3-omni-thinker-live-only` |
| 이미지 패치 | `nvdec_mpegts.py`, `omni_modality.py` | `docker` `vllm-serving/patches` |
| 요청 | system 프롬프트 17 KB(약 4,000토큰), user 콘텐츠는 `video_url`만(텍스트 없음), `response_format` json_schema(15개 필드), `max_tokens 2048`, `temperature 0.1`, `mm_processor_kwargs {"use_audio_in_video": true}`, `chat_template_kwargs {"enable_thinking": false}` | `vuf-poc` `common/omni_caption.py`, `common/captioning/regular.py`, `live-ingest/app.py` |
| 미디어 | 6초 640×360 H.264 + AAC 16 kHz TS 세그먼트, fps 2 → 12프레임 → 640×352로 패치화, 6×22×40 그리드 = 비디오 1,320토큰, 오디오 82토큰 | 측정 |

`video_url` 안의 `fps/min_pixels/max_pixels`는 vLLM 0.28.0이 읽지 않는다. 실제 값은 서버의 `--mm-processor-kwargs`와 로더 기본값(fps 2)에서 온다.

## 1~9번 중 제일 비싼 단계 (NVDEC + MPS, API 서버 12개, 오디오+영상)

| 단계 | 어디서 | 1건 단독 | 64동시 p50 | 비고 |
|---|---|---|---|---|
| 1 다운로드 | CPU/네트워크 | 1.7 ms × 2회 | 2.8 ms × 2회 | 로컬 HTTP 기준 |
| 2 포장 바꾸기 | CPU | 4.4 ms | 44 ms | |
| 3 디코드 | NVDEC | 22 ms (CPU 11) | 60 ms | OpenCV: 55 ms, 프로세스 CPU 154 ms |
| 4 호스트 복사 | GPU→CPU | 0.3 ms | 0.3 ms | 8.3 MB |
| 5 전처리 (640×352 패치화) | CPU | 45 ms (CPU 49) | 59 ms | CPU 디코드 구성에서는 30~38 ms |
| 6 오디오 | CPU | 약 10 ms (다운로드 1.7 + AAC 4.3 + 멜 2.4) | 약 14 ms | |
| 7 인코더 | GPU | 74 ms (비전 37 + 오디오 33) | 항목마다 호출: 버스트당 64×41 + 64×37 = 5.0 s | 영상만 요청은 16개씩 묶임 |
| 8 프리필 | GPU | 167 ms (인코더 제외 약 94 ms) | 3.6 s (p95 6.4 s) | 4,016토큰 프리픽스 캐시 적중 |
| 9 생성 | GPU | 1,629 ms (233토큰, 토큰당 7.0 ms) | 8.8 s (토큰당 38 ms) | **지연 1위** |
| 합계 | | 1.92 s (프론트엔드+IPC 116 ms) | 14.6 s, 4.2 req/s (프론트엔드+IPC 0.5 s) | |

- **CPU 기준**: API 서버는 요청당 0.16~0.19 cpu-s(5번 45~59 ms, 디코드 경로 19 ms, 오디오 10 ms). 엔진은 1건에서 요청당 1.8 cpu-s로, 생성 1.6 s 동안 엔진 스레드가 거의 100% 돈다(스텝당 7 ms가 CPU 쪽 작업). 64동시에서는 요청당 0.25 cpu-s다.
- **지연 기준, 1건**: 9 생성 1.63 s ≫ 8 프리필 0.17 s > 프론트엔드 0.12 s.
- **지연 기준, 64동시**: 9 생성 8.8 s > 8 프리필 3.6 s(이 중 인코더 직렬 호출 5.0 s/버스트) > 프론트엔드 0.5 s.

## 구성별 비교 (64동시, 오디오+영상 / 영상만)

| 구성 | 1건 p50 | 64동시 p50 | 처리량 | 토큰당 생성 (1건 / 64동시) | API 서버 CPU/요청 |
|---|---|---|---|---|---|
| NVDEC + MPS (운영) | 1.92 / 1.85 s | 14.6 / 10.7 s | 4.2 / 5.7 req/s | 7.0 / 38 ms | 0.16 cpu-s |
| CPU(OpenCV), MPS 끔 | 1.87 / 1.66 s | 13.5 / 9.3 s | 4.4 / 6.5 req/s | 6.7 / 34 ms | 0.40 cpu-s |
| NVDEC + MPS, `response_format` 없음 | 1.84 / 0.26 s* | 9.5~10.1 / 2.3~2.7 s* | 2.9 / 2.9 req/s* | 6.8 / 16~24 ms | |
| CPU(OpenCV) + MPS 켬 | 1.88 / 1.87 s | 13.5 / 9.6 s | 4.3 / 6.4 req/s | 7.0 / 35 ms | 0.42 cpu-s |
| NVDEC, MPS 끔 | 1.76 / 1.75 s | 15.5 / 12.1 s | 4.0 / 5.1 req/s | 6.4 / 39 ms | 0.74 cpu-s |
| NVDEC + MPS + `--async-scheduling` | 1.97 / 1.91 s | 13.3 / 9.95 s | 4.65 / 6.15 req/s | 7.0 / 33 ms | 0.15 cpu-s |
| NVDEC + MPS + 모달리티 정렬(`SORT_MM=1`) | 1.93 / 1.92 s | **10.5 / 10.4 s** | **5.9 / 6.0 req/s** | 7.2 / 35 ms | 0.15 cpu-s |
| NVDEC + MPS + 정렬 + `--async-scheduling` | 1.90 / 1.98 s | 10.45 / 10.35 s | 5.9 / 5.9 req/s | 7.2 / 35 ms | 0.15 cpu-s |

\* 문법 없이는 영상만 요청의 출력이 4토큰(빈 응답) 또는 400~600토큰으로 불안정해서 p50·처리량은 비교 대상이 아니다. 오디오+영상은 262토큰으로 비슷하다.

## 실험: 인코더 항목을 모달리티별로 정렬

`SORT_MM=1`로 [bench/stagetime/sitecustomize.py](../bench/stagetime/sitecustomize.py)가 러너의 `_batch_mm_inputs_from_scheduler` 결과(해시·kwargs·LoRA 참조의 병렬 리스트)를 모달리티 기준으로 안정 정렬한다. 인코더 출력은 해시와 zip해서 캐시되므로 순서를 바꿔도 안전하다.

| | 기존 | 정렬 |
|---|---|---|
| 64동시 av 인코더 호출 | 비전 64회 × 41 ms + 오디오 64회 × 37 ms = 5.0 s/버스트 | 비전 4~5회 × 181 ms(14개) + 오디오 4~5회 × 55 ms = 1.1 s/버스트 |
| 영상당 / 클립당 | 41 / 37 ms | 13 / 4 ms |
| 64동시 av 프리필 p50 | 3.6 s | 1.3 s |
| 64동시 av p50 / 처리량 | 14.6 s / 4.2 req/s | 10.5 s / 5.9 req/s |
| 64동시 영상만 | 10.7 s | 10.4 s (변화 없음, 이미 묶이고 있었음) |
| 1건 | 1.92 s | 1.93 s (변화 없음) |

`--async-scheduling`은 단독으로는 64동시 토큰당 38 → 33 ms(av p50 14.6 → 13.3 s)를 줬고 구조화 출력과 함께 써도 오류가 없었지만, 정렬과 겹쳐 쓰면 정렬만 쓴 것(10.5 s)과 같았다. 1건에는 영향이 없다. 두 실험 모두 반복 2회라 5% 안쪽 차이는 잡음이다.

## 개선 우선순위 (운영 Qwen3-Omni 기준)

| 순위 | 조치 | 근거 | 기대 효과 (64동시 av p50 14.6 s 기준) | 작업량 |
|---|---|---|---|---|
| 1 | **구조화 출력 비용 줄이기** | 문법을 빼면 토큰당 38 → 16~24 ms, p50 14.6 → 9.5 s. 1건에선 차이 없음(동시 요청 수에 비례하는 CPU 작업) | 최대 약 5 s | 중간. xgrammar 버전·백엔드(`guidance`) 비교, 스키마 단순화(15개 필드·enum), vLLM 최신판의 비트마스크 경로 확인. 출력 정확성 때문에 끄는 건 불가 |
| 2 | **인코더 항목을 모달리티별로 묶기** | 실험 완료: p50 14.6 → 10.5 s, 처리량 4.2 → 5.9 req/s, 출력 영향 없음(순서만 바뀜) | 약 4 s | 작음. 러너 한 함수에 안정 정렬 추가(`SORT_MM` 패치 그대로). 업스트림 PR 가치 있음 |
| 3 | **생성 자체** | 1건의 85%가 생성(230토큰 × 7 ms). 엔진 스레드가 그동안 거의 100% CPU | 1건 지연의 대부분 | 큼. 출력 토큰 줄이기(스키마·프롬프트: transcript 등 긴 필드), 투기적 디코딩(EAGLE/MTP 지원 여부 확인), 스텝 CPU 오버헤드 프로파일링 |
| 4 | `--async-scheduling` | 단독 약 9%, 정렬과 겹치면 효과 없음 | 0~1 s | 플래그 하나. 2번 뒤에는 우선순위 낮음 |
| 5 | NVDEC 유지 여부 | 지연 이득 없음(64동시 +1 s), API 서버 CPU 0.40 → 0.16 cpu-s/요청. CPU limit 16코어에서 CPU 디코드는 5 req/s에 2코어 | CPU 예산의 문제 | 설정만. MPS는 NVDEC을 쓰는 한 필수 |
| — | 전처리(5번) GPU 이관, 리먹스, 호스트 복사 | 요청의 1~3% | 측정 가능한 이득 없음 | |

## 측정 방법과 한계

- Nemotron 측정과 같은 하네스([bench/live_stage_matrix.sh](../bench/live_stage_matrix.sh), 세그먼트 변형 800개, 단계별 타이머)를 쓰고, Qwen3-Omni의 전처리(`Qwen3OmniMoeProcessor`, `Qwen2VLVideoProcessor._preprocess`, `WhisperFeatureExtractor`)와 인코더(`_process_video_input`, `_process_audio_input`)에 훅을 걸었다.
- 운영 요청은 live-ingest가 세그먼트 8개를 동시에 보내는 버스트(`segment_n=8`, 마감 25초)다. 64동시는 그보다 큰 부하이고, 1건과 64동시 사이 값은 재지 않았다.
- `response_format` 없음 구성은 출력 길이가 달라 처리량 비교에 쓸 수 없고, 토큰당 생성 시간만 비교했다.
- 같은 노드에 다른 파드가 돌고 있어 CPU 단계가 실행마다 흔들린다(5번 45~59 ms).

## 재현

```bash
# 운영 모양 (iac values.yaml + vuf-poc live-ingest 계약)
export MODEL=/gpfs/public/artifacts/models/Qwen/Qwen3-Omni-30B-A3B-Instruct
export REASONING_PARSER= MAX_MODEL_LEN=49152 MAX_BATCHED=49152 GPU_UTIL=0.9
export MM_KWARGS='{"max_pixels":313600,"fps":2.0}' STRUCTURED='{"backend":"xgrammar","disable_any_whitespace":true}'
export SYSTEM_PROMPT="$(cat bench/prod/live_system_prompt.txt)" RESPONSE_FORMAT=@bench/prod/live_response_format.json
export PROMPT= MAX_TOKENS=2048
python bench/prod/omni_modality.py            # 운영 이미지의 Qwen3-Omni use_audio_in_video 패치
MPS=1 bash bench/live_stage_matrix.sh qwen-nvdec-asc12 '{"video":{"backend":"pynvvideocodec","hw_decoders":2}}'
      bash bench/live_stage_matrix.sh qwen-cpu-asc12   '{"video":{"backend":"opencv"}}'
```
