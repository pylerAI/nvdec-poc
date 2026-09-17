# GPU Video Decoding for Multimodal LLM Serving: NVDEC (PyNvVideoCodec) versus CPU Decoding on NVIDIA B200

**Pyler Platform Team — September 2026**

## Abstract

Video-understanding services spend a surprising share of their compute on a step that has nothing to do with the model: decoding H.264 into frames. We quantify how much a single NVIDIA B200 gains by moving that step from CPU (OpenCV/FFmpeg) to the GPU's NVDEC engines through PyNvVideoCodec, at three levels: (i) raw decode throughput, (ii) the decode stage of vLLM's video loader (sampled frames only), and (iii) end-to-end serving of a 30B multimodal model (NVIDIA Nemotron 3 Nano Omni 30B-A3B) with vLLM 0.28. Raw decode of 1080p H.264 reaches **12,200 frames/s on NVDEC using 2 CPU cores** versus **4,760 frames/s on CPU using 57 cores** — 60–120× more frames per CPU core — provided CUDA MPS is enabled; without MPS, multi-process NVDEC is capped at ~2,300 frames/s by context time-slicing. In vLLM's loader, per-clip decode latency of 1080p shots improves **2.0× (10 s), 2.0× (30 s) and 5.3× (120 s)**, because the NVDEC path decodes only the GOPs that contain sampled frames. End-to-end, with 12 API-server processes on a 64-core host, NVDEC cuts server CPU per request **3.3× for 360p live segments and 7.8–10.7× for 1080p VOD**, and lowers p50 latency of 1080p requests by 13–31 % while raising throughput 15–32 %. We also report where the gain is small (short 360p segments on an unconstrained CPU), the Python-binding serialization that limits per-process NVDEC throughput, and the MPEG-TS limitations of PyNvVideoCodec that required a stream-copy remux to work around.

## 1. Introduction

Multimodal LLMs consume video as a handful of sampled frames — typically 1–2 frames per second of content — but producing those frames means demuxing and decoding a compressed stream. In a serving stack such as vLLM, this runs inside the API-server processes, on CPU, on the same host that drives the GPU. As models get faster and hosts pack more GPUs per CPU socket, the decode stage becomes a fixed CPU tax per request that scales with resolution and clip length rather than with model size.

NVIDIA GPUs carry dedicated NVDEC engines (seven on B200) that are idle during LLM inference. vLLM 0.27+ exposes them through a `pynvvideocodec` video backend. This proof of concept asks a narrow question: **how much better is NVDEC/PyNvVideoCodec than plain CPU decoding for the frame-sampling workload of a multimodal LLM server, on one B200?** We answer it with two realistic inputs — 6-second 640×360 HLS MPEG-TS live segments and 1080p VOD shots of 10, 30 and 120 seconds — and three measurement levels that isolate the decoder, the loader, and the whole serving path.

## 2. System under test

### 2.1 Hardware and software

| | |
|---|---|
| GPU | 1× NVIDIA B200 (183 GB), driver 580.126.09; second GPU in the pod left idle (`CUDA_VISIBLE_DEVICES=0`) |
| CPU | Intel Xeon Platinum 8570; container cgroup quota **64 cores** (host exposes 224) |
| Decoders | PyNvVideoCodec 2.1.1 (`__version__`; pip metadata 2.0.4) via NVDEC; OpenCV 5.0.0 (FFmpeg avcodec 62.28) for CPU |
| Serving | vLLM 0.28.0 (V1 engine), `--api-server-count 12`, torch 2.13 + CUDA 13.0, PyAV 16.1 |
| Model | `nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16`, `--reasoning-parser nemotron_v3`, `enable_thinking=false`, `max_tokens 64` |
| GPU sharing | CUDA MPS (`nvidia-cuda-mps-control -d`) in the NVDEC configuration, so the 12 API-server CUDA contexts and the engine share the GPU concurrently |
| Env | `NVIDIA_DRIVER_CAPABILITIES=video,compute,utility`, `OMP_NUM_THREADS=1` |

### 2.2 Decode paths compared

- **CPU (`opencv`)**: vLLM's default video backend. `cv2.VideoCapture` decodes every frame sequentially (FFmpeg auto-threading, ~6 threads per 1080p stream) and keeps the sampled ones.
- **NVDEC (`pynvvideocodec`)**: vLLM's PyNvVideoCodec backend. `SimpleDecoder` with scanned stream metadata decodes only the frames requested by index (`get_batch_frames_by_index`), so only the GOPs containing sampled frames are decoded, and decoder objects are reused across requests via `reconfigure_decoder` (`hw_decoders=2` cached decoder slots per process). Decoded frames land in device memory and are copied to pinned host memory for the HF processor.
- **MPEG-TS patch (`patches/nvdec_mpegts.py`)**: PyNvVideoCodec cannot index MPEG-TS (§5.3). Our build-time patch detects TS by its 0x47 sync bytes and stream-copies the video track into a fragmented MP4 in memory with PyAV (no re-encode, ~5 ms for a 6 s segment), then continues down vLLM's unmodified MP4 path. Audio for `use_audio_in_video` is read by vLLM's audio loader from the original bytes.

An earlier design that created a fresh `CreateDemuxer`+`CreateDecoder` per request and decoded whole segments cost ~300 ms per 6 s segment versus 20 ms with the design above; decoder reuse alone is a 9× difference (297 ms → 33 ms per clip; `CreateDecoder` itself is 1.7 ms — the cost is paid on the first decoded frames). This follows NVIDIA DevTech's guidance to reuse decoders and decode only what is needed.

## 3. Methodology

### 3.1 Inputs

- **Live segment**: 6.0 s MPEG-TS, H.264 640×360 @ 29.97 fps (182 frames) plus one AAC track, 0.4 MB — the shape of an HLS segment. Sampled at 2 fps → 12 frames.
- **VOD shots**: a 42.9-minute 1080p H.264 title (955 MB) cut into fixed-length shots and re-encoded with closed GOPs (`libx264 -preset veryfast -g 30 -sc_threshold 0`; NVDEC's indexer rejects open-GOP cuts, §5.3): 64×10 s (6.2 MB, 307 frames), 32×30 s (17 MB), 8×120 s (61 MB, 3,633 frames). Sampled at 1 fps, capped at 128 frames (`num_frames`) — the model card's recommendation for 1080p.

### 3.2 Three measurement levels

1. **Raw decode** (`bench/raw_decode_bench.py`): decode *every* frame of a clip in 1–16 worker processes, each with one reused decoder (`CreateDecoder`, RGB output in device memory) or one `cv2.VideoCapture`. Workers warm up, synchronize on a barrier, then decode the clip 3–5×; we report frames/s over the slowest worker's window and CPU seconds from `getrusage`. NVDEC is measured with and without MPS.
2. **Decode stage** (`bench/vod_loader_bench.py`): vLLM's own loader (`VideoMediaIO.load_bytes`) with each backend, so container handling, frame sampling and the host copy are included. Median per-clip latency sequentially, and throughput with 8 threads in one process. **3 repetitions.**
3. **End-to-end** (`bench/e2e_matrix.sh`, `bench/load_test.py`): `vllm serve` with 12 API servers; a client in the same pod fires N concurrent chat-completion requests carrying the clip as a base64 data URL (live: N = 64, 2 fps, with and without `use_audio_in_video`; VOD: 64×10 s, 32×30 s, 8×120 s at 1 fps). We record client latency percentiles and throughput, **server CPU from the pod cgroup** (`cpu.stat` delta ÷ requests) and GPU SM/NVDEC utilization (`nvidia-smi dmon`, 1 s). Each configuration is started once (fresh caches), warmed with two requests, then the matrix runs **3 times**; we report means. The two configurations differ only in `--media-io-kwargs` (`backend`) and MPS.

The live tests reuse one segment across the 64 requests and therefore hit vLLM's prefix and multimodal-processor caches; we treat their absolute latencies as optimistic and compare configurations only against each other. VOD tests use distinct clips.

## 4. Results

### 4.1 Raw decode: NVDEC needs ~1/60 of the CPU per frame, and MPS to scale across processes

1080p H.264, 307-frame clip, aggregate over all workers (`results/summary.md`, section A/A′):

| Workers | CPU (OpenCV) frames/s | CPU cores used | NVDEC frames/s, **MPS on** | cores | NVDEC frames/s, MPS off | cores |
|---|---|---|---|---|---|---|
| 1 | 694 | 6.4 | 2,189 | 0.2 | 2,188 | 0.2 |
| 2 | 1,325 | 13.0 | 4,274 | 0.3 | 2,630 | 1.7 |
| 4 | 2,431 | 25.7 | 8,242 | 0.8 | 2,290 | 4.0 |
| 8 | **4,763** | 57.3 | 11,823 | 1.3 | 2,258 | 8.0 |
| 16 | 2,802 | 62.9 | **12,178** | 2.0 | 2,227 | 16.0 |

Per CPU core, OpenCV/FFmpeg delivers 83–109 frames/s of 1080p H.264; NVDEC delivers 6,000–13,500 frames/s per core of *host* CPU because the CPU only demuxes and submits packets. At the 64-core quota the CPU path peaks at 4,763 frames/s (≈159 real-time 1080p30 streams) and collapses when oversubscribed (16 workers × 6 FFmpeg threads); one B200's NVDEC engines deliver 12,178 frames/s (≈406 real-time streams) with two cores to spare for everything else. For 640×360 the picture is the same at higher absolute numbers: CPU 32,033 frames/s on 62.5 cores versus NVDEC 51,202 frames/s on 6.3 cores.

**MPS is not optional.** Without it, every NVDEC worker holds its own CUDA context and the contexts are time-sliced: aggregate throughput stays at ~2,300 frames/s regardless of worker count or resolution (the same 2,320 frames/s for 360p as for 1080p), and each worker burns a full core spinning in synchronization (8.0 cores for 8 workers). With MPS the same code scales 5.4× and CPU use drops 6×. A vLLM deployment with 12 API-server processes is exactly this multi-process pattern.

### 4.2 Decode stage in vLLM's loader: 2–5× lower latency for 1080p, parity for 360p

Mean of 3 repetitions (range in parentheses), sequential median per clip and 8-thread single-process throughput:

| Clip | Sampled frames | CPU (opencv) | NVDEC (pynvvideocodec) | Speed-up | Throughput CPU → NVDEC (clips/s, 1 process) |
|---|---|---|---|---|---|
| VOD 10 s 1080p, 1 fps | 10 | 258 ms (248–272) | **132 ms** (130–133) | 2.0× | 18.8 → 9.9 |
| VOD 30 s 1080p, 1 fps | 31 | 688 ms (680–702) | **350 ms** (348–352) | 2.0× | 6.9 → 3.7 |
| VOD 120 s 1080p, 1 fps | 32 (cap) | 2,132 ms (2,068–2,221) | **404 ms** (398–409) | **5.3×** | 2.2 → 3.2 |
| Live 6 s 360p TS, 2 fps | 12 | 32 ms (29–34) | 28 ms (26–31) | 1.1× | 115 → 50 |

The speed-up grows with clip length because the CPU path decodes all 3,633 frames of a 120 s clip to keep 32, whereas the NVDEC path seeks to each sampled frame's GOP (30 frames) and decodes ~32 × 30 frames. For a 6-second 360p segment there is little to save: both paths finish in ~30 ms, of which the remux is 5 ms and the NVDEC decode itself 20 ms.

The throughput column exposes a limitation of the Python binding rather than the hardware: within one process, 8 threads on NVDEC reach 9.9 clips/s of 10 s 1080p regardless of `hw_decoders` (2, 4 or 7 slots give the same number), while OpenCV — which releases the GIL — reaches 18.8. `SimpleDecoder` calls serialize under the GIL. Section 4.1 shows the engines themselves have 10× headroom; vLLM's multi-process front end recovers it, as §4.3 confirms.

### 4.3 End-to-end serving: 3–11× less CPU per request, 13–31 % lower latency for 1080p

Nemotron 3 Nano Omni on one B200, 12 API servers, 64-core quota; means of 3 repetitions (`results/summary.md`, section C):

| Workload | N | Decode | p50 | p95 | req/s | Server CPU per request | CPU saving |
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

All 1,536 requests succeeded in both configurations. Three patterns:

1. **CPU per request is where NVDEC wins decisively.** For 1080p content the server spends 3.3–36 cpu-s per request on the CPU path — for a 120 s shot that is 36 core-seconds to produce 32 frames — and 0.4–3.4 cpu-s on NVDEC. The remaining NVDEC-path CPU is the HF image processor, tokenization and the pinned-host copy, not decoding. For the 360p live segment the absolute numbers are small either way (0.23 vs 0.07 cpu-s).
2. **Latency improves when decode is a visible fraction of the request.** With 64 concurrent 1080p requests spread over 12 API servers, each server decodes ~5 clips back to back; the 2–5× decode-stage gain of §4.2 turns into 13 % (10 s), 31 % (30 s) and 29 % (120 s) lower p50 and 15–32 % higher throughput. For the 6-second 360p segment NVDEC is 0.2 s *slower* on the video-only path: the decode is ~30 ms on either side, and the NVDEC frames travel through a second CUDA context and a device→host copy before the processor.
3. **The GPU is never decode-bound.** Peak NVDEC utilization during the runs was 21–28 %; SM utilization was 30–50 % during VOD prefill. Decode and inference share the B200 through MPS without measurable interference at these rates.

The audio+video rows add Nemotron's speech encoder and vLLM's audio loader (PyAV, CPU) to every request; the decode-side saving is unchanged (0.48 → 0.29 and 3.97 → 0.93 cpu-s), but the audio path dominates latency and is outside the scope of this comparison.

## 5. Discussion

### 5.1 What the numbers mean for capacity planning

The gain is first a *CPU* gain. Per 1080p request the CPU path needs 3.3 (10 s) to 36 (120 s) core-seconds; a host with *c* cores per GPU can therefore preprocess at most *c*/3.3 to *c*/36 requests per second before the CPU, not the GPU, sets the ceiling. With NVDEC the same ceiling is 8–11× higher, and in our runs it is the GPU's prefill of 1.6k–17k visual tokens that limits throughput — the resource one actually buys a B200 for. On hosts with few cores per GPU (e.g. 16-core pod quotas on shared nodes) this is the difference between a decode-bound and a model-bound service; on the 64-core testbed it still shows as 13–31 % lower latency.

### 5.2 Where NVDEC does not help

Short, low-resolution clips decode in tens of milliseconds on either path; there the CUDA-context hop and host copy cost as much as they save. Teams whose inputs are exclusively ≤ 480p short segments should expect a CPU saving (3×) but no latency saving, and should weigh it against running MPS.

### 5.3 Limits of the current stack (details and reproductions in `docs/nvidia-issues.md`)

- **MPEG-TS.** PyNvVideoCodec's demuxer `Seek`/`TimestampFromFrame` SIGSEGV on TS, and `SimpleDecoder(need_scanned_stream_metadata=True)` fails to index it. A 5 ms stream-copy remux to fragmented MP4 is the pragmatic workaround until native TS indexing lands.
- **Open-GOP cuts.** Shots cut at non-IDR keyframes make `get_batch_frames_by_index` raise `IndexError` after "Decode Error occurred for picture N"; FFmpeg tolerates the same clips. Re-encode with closed GOPs or cut at IDR frames.
- **Per-process serialization.** `SimpleDecoder` holds the GIL; one process does not exceed ~10 decodes/s of 10 s 1080p clips. Multi-process front ends (vLLM's `--api-server-count`) recover the hardware's headroom; single-process integrations will not.
- **MPS dependence.** Multi-process NVDEC without MPS is capped at ~2,300 frames/s by context time-slicing and burns one core per process (§4.1). Any deployment that decodes from more than one process on the inference GPU should run MPS.
- **Warm-up placement.** A fresh decoder costs ~300 ms on its first frames rather than at `CreateDecoder`; decoder reuse (`reconfigure_decoder`) is essential for short clips.

## 6. Conclusion

On one B200, NVDEC through PyNvVideoCodec decodes 1080p H.264 at 12,200 frames/s with two CPU cores where FFmpeg needs 57 cores for 4,760 — a 60–120× improvement in frames per CPU core — once CUDA MPS lets multiple processes share the engines. Inside vLLM the sampled-frame decode of 1080p shots is 2–5× faster, and end-to-end serving of a 30B multimodal model uses 3–11× less server CPU per request with 13–31 % lower latency for 1080p inputs. Short 360p segments gain CPU but not latency. The remaining work is upstream: native MPEG-TS indexing and GIL-free decode calls in PyNvVideoCodec.

## 7. Reproduction

```
patches/nvdec_mpegts.py     vLLM 0.28.0 build-time patch: MPEG-TS -> in-memory fMP4 remux before the PyNvVideoCodec path
bench/raw_decode_bench.py   §4.1  raw decode throughput, N processes, cv2 vs PyNvVideoCodec (run with and without MPS)
bench/vod_loader_bench.py   §4.2  decode stage through vLLM VideoMediaIO (BACKENDS, HW_DECODERS)
bench/e2e_matrix.sh         §4.3  start vLLM (Nemotron 3 Nano Omni) with a media-io config, run the matrix 3x
bench/load_test.py          concurrent OpenAI-API load with data-URL video (ENDPOINT VIDEO N USE_AUDIO FPS MEDIA_IO)
bench/run_all.sh            the whole chain as executed for this report; bench/summarize.py -> results/summary.md
bench/cut_shots.py          stream-copy shot cutter (re-encode with closed GOPs afterwards)
bench/nvdec_advice_bench.py, bench/remux_vllm_pattern.py   PyNvVideoCodec microbenchmarks (decoder reuse, seek, remux)
results/run_all_2026-09-17.log   raw log of every number quoted above; results/summary.md   tables
```

Serve flags (NVDEC configuration): `vllm serve nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 --trust-remote-code --api-server-count 12 --max-model-len 32768 --limit-mm-per-prompt '{"video":1,"audio":1}' --media-io-kwargs '{"video":{"backend":"pynvvideocodec","hw_decoders":2,"fps":1,"num_frames":128}}' --reasoning-parser nemotron_v3`, with `nvidia-cuda-mps-control -d` started first, `NVIDIA_DRIVER_CAPABILITIES=video,compute,utility`, `OMP_NUM_THREADS=1`. The CPU configuration uses `"backend":"opencv"` and no MPS.

## Acknowledgements

NVIDIA video DevTech (2026-09-12 consultation) for the decoder-caching and sampled-decode guidance that shaped the MPEG-TS patch.
