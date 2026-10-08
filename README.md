# nvdec-poc — NVDEC vs CPU video decoding for multimodal LLM serving (B200)

Proof of concept measuring how much a single NVIDIA B200 gains by decoding video on its NVDEC engines
(PyNvVideoCodec, vLLM's `pynvvideocodec` backend) instead of on CPU (OpenCV/FFmpeg), for the
frame-sampling workload of a multimodal LLM server. Inputs: 6 s 640×360 HLS MPEG-TS segments (live) and
1080p H.264 shots of 10/30/120 s (VOD). Model for the end-to-end tests: NVIDIA Nemotron 3 Nano Omni 30B-A3B
on vLLM 0.28.0.

**Headline (one B200, 64-core host):**

| Level | CPU (OpenCV/FFmpeg) | NVDEC (PyNvVideoCodec) |
|---|---|---|
| Raw 1080p H.264 decode, all frames | 4,760 frames/s on 57 cores | **12,180 frames/s on 2 cores** (with CUDA MPS) |
| vLLM decode stage, 1080p shot 10 s / 30 s / 120 s @ 1 fps | 258 / 688 / 2,132 ms | **132 / 350 / 404 ms** (2.0× / 2.0× / 5.3×) |
| End-to-end server CPU per request, 1080p 10 s / 30 s / 120 s | 3.3 / 9.3 / 36 cpu-s | **0.43 / 0.97 / 3.4 cpu-s** (7.8× / 9.5× / 10.7×) |
| End-to-end p50 latency, 1080p 10 s ×64 / 30 s ×32 / 120 s ×8 | 8.9 / 14.3 / 18.2 s | **7.7 / 9.8 / 12.9 s** |
| 360p 6 s live segment (video only) | 0.23 cpu-s, p50 1.9 s | 0.07 cpu-s, p50 2.1 s (CPU saving only) |

Full write-up: [REPORT.md](REPORT.md). The trial-and-error path that led here, on one page:
[docs/journey.md](docs/journey.md). Issues found in PyNvVideoCodec (MPEG-TS indexing, open-GOP cuts,
GIL serialization, MPS dependence) with reproductions: [docs/nvidia-issues.md](docs/nvidia-issues.md).

## Layout

| Path | What |
|---|---|
| `patches/nvdec_mpegts.py` | vLLM 0.28.0 build-time patch: MPEG-TS → in-memory fMP4 stream-copy remux, then vLLM's upstream `SimpleDecoder` path (sampled frames, decoder-slot reuse) |
| `bench/raw_decode_bench.py` | raw decode throughput, 1–16 processes, cv2 vs PyNvVideoCodec, CPU cores used |
| `bench/vod_loader_bench.py` | decode-stage benchmark through vLLM `VideoMediaIO`: `pynvvideocodec` vs `opencv` |
| `bench/e2e_matrix.sh` | start vLLM (Nemotron 3 Nano Omni) with a media-io config and run the live/VOD load matrix ×3 |
| `bench/load_test.py` | concurrent OpenAI-API load generator with data-URL video (file or directory of clips) |
| `bench/run_all.sh` | the full chain as run for the report; `bench/summarize.py` turns its log into `results/summary.md` |
| `bench/nvdec_advice_bench.py`, `bench/remux_vllm_pattern.py` | PyNvVideoCodec microbenchmarks: decoder reuse, seek, remux, concurrency |
| `bench/cut_shots.py` | cut a long MP4 into fixed-length shots by stream copy (re-encode with closed GOPs afterwards) |
| `bench/live_stage_matrix.sh` | live 6 s 360p TS, per-stage matrix: sequential and 64-burst requests with stage timers; `SERVE=vllm` (`vllm serve`, real API-server processes) or `SERVE=module` (`python -m …api_server`, which runs ONE API server in vLLM 0.28.0 regardless of `--api-server-count`) |
| `bench/stagetime/sitecustomize.py` | per-stage timers injected into every vLLM process (download, remux, NVDEC/OpenCV decode, host copy, resize/normalize, audio, encoders via CUDA events, per-request prefill/decode) for Nemotron 3 Nano Omni and Qwen3-Omni; experiments: `BATCH_VIDEO=1` batches Nemotron's per-video ViT calls per step (bit-identical output), `SORT_MM=1` orders an encoder step's items by modality so audio+video requests batch |
| `bench/make_variants.py`, `bench/seg_server.py`, `bench/live_load.py` | distinct-content copies of one segment (every request misses every cache), HTTP server for .ts/.mp4 clips with companion .wav (`/a/<key>.wav`), URL load generator (`use_audio_in_video` or a separate `audio_url` part as production VOD sends) |
| `bench/stage_report.py`, `bench/proc_cpu.py`, `bench/compare_runs.py` | per-stage tables from a matrix run; server CPU by process role; side-by-side comparison of runs (e.g. 360p vs 1080p) on per-request means |
| `bench/prod/` | production live-ingest request shape (system prompt, JSON response schema from `vuf-poc`) and the serving image's `omni_modality.py` patch, for measuring the production model Qwen3-Omni with the same harness (`results/qwen3omni_live360_stages_2026-10-07.md`) |
| `results/` | raw log and summary tables for every number in the report; live 360p stage breakdown in `results/live360_stages_2026-10-07.md` (Nemotron) and `results/qwen3omni_live360_stages_2026-10-07.md` (Qwen3-Omni, production shape); live 1080p in `results/live1080_stages_2026-10-08.md`; VOD 14 s scene clips (360p vs 1080p, production worker-captioning shape) in `results/vod14s_stages_2026-10-08.md` |

## Quick start (single B200)

```bash
pip install vllm==0.28.0 PyNvVideoCodec av soundfile librosa
python patches/nvdec_mpegts.py                      # only needed for MPEG-TS input
export CUDA_VISIBLE_DEVICES=0 NVIDIA_DRIVER_CAPABILITIES=video,compute,utility OMP_NUM_THREADS=1
nvidia-cuda-mps-control -d                          # required for multi-process NVDEC (see REPORT §4.1)

# raw decode: CPU vs NVDEC, 1..16 processes
python bench/raw_decode_bench.py shot_1080p_10s.mp4 --procs 1 4 8 16

# decode stage through vLLM's loader
HW_DECODERS=2 python bench/vod_loader_bench.py shots_10s/ 1 32 8

# end-to-end (NVDEC config; use '{"video":{"backend":"opencv","fps":1,"num_frames":128}}' for the CPU baseline)
MPS=1 VOD_DIR=/data/vod bash bench/e2e_matrix.sh nvdec-mps \
  '{"video":{"backend":"pynvvideocodec","hw_decoders":2,"fps":1,"num_frames":128}}'
```
