# PyNvVideoCodec 2.1.1 / NVDEC integration — issues, reproductions and questions for NVIDIA

Environment: NVIDIA B200 (driver 580.126.09), NVDEC via `NVIDIA_DRIVER_CAPABILITIES=video,compute,utility`,
PyNvVideoCodec 2.1.1 (`__version__`; pip metadata 2.0.4), torch 2.13 + cu130, PyAV 16.1, vLLM 0.28.0.
Workload: HLS MPEG-TS segments (H.264 640×360 @ 29.97 fps, 6.0 s, one AAC track) and 1080p H.264 MP4
shots, sampled at 1–2 fps.

## What worked (and what we changed because of your advice)

| Decode path for one 6 s TS segment (12 sampled frames) | Latency |
|---|---|
| New `CreateDemuxer`+`CreateDecoder` per request, decode all 180 frames, per-frame `from_dlpack` + stack + stream sync | ~300 ms; under 64 concurrent requests on a saturated GPU p50 6.4 s even with MPS |
| Same full decode, one decoder reused across clips | 33 ms (9×) — the decoder-caching advice |
| Stream-copy remux TS → fMP4 (PyAV, 5 ms) then `SimpleDecoder.get_batch_frames_by_index` with `reconfigure_decoder` reuse | **20 ms**; 64 clips/s with 2 decoder slots × 8 threads |
| CPU (OpenCV/FFmpeg) reference | 30–58 ms |

End-to-end (vLLM serving, see `REPORT.md`): per-request server CPU dropped 3–4× with NVDEC. NVDEC engine
utilization is low (1–5 % live, 10–30 % for 1080p VOD) — decode is never the GPU bottleneck at these
sampling rates.

Two corrections to what we said in the 2026-09-12 call: during our load the GPU was at 99–100 % SM
utilization (not idle), so decode work issued from API-server CUDA contexts does queue behind
inference; and "MPS made NVDEC about as fast as CPU" referred to our MP4 ad path — the MPEG-TS path
used a different code path that decoded whole segments, and MPS did not fix that.

## Issues

### 1. MPEG-TS cannot be indexed or seeked

```python
import PyNvVideoCodec as nvc
d = nvc.CreateDemuxer(filename="segment.ts")      # any .ts; ours is 6 s H.264 640x360 + AAC
d.TimestampFromFrame(30)                           # SIGSEGV
d.Seek(d.TimestampFromFrame(150))                  # SIGSEGV (also with a hand-computed 90 kHz pts)
```

```python
sd = nvc.SimpleDecoder("segment.ts", output_color_type=nvc.OutputColorType.RGB, use_device_memory=True,
                       need_scanned_stream_metadata=True, gpu_id=0, cuda_stream=stream.cuda_stream,
                       decoder_cache_size=2)
sd.get_batch_frames_by_index([0, 15, 30, ...])    # IndexError (sorted_frames shorter than requested) on a 10 s TS,
                                                   # SIGSEGV on a 6 s TS that has an audio track
```

The same elementary stream stream-copied into fragmented MP4 works with identical calls
(scanned metadata total=180, fps=29.97, 12 frames in 20 ms). Without `need_scanned_stream_metadata`
a plain `SimpleDecoder("segment.ts")` returns a few frames, so the container is partially parsed but
the index is unreliable.

### 2. `PyNvDecoder.SetSeekPTS(pts)` has no effect on the `CreateDemuxer`+`CreateDecoder` path

All frames are still emitted (first output pts = stream start, not the target).

### 3. Open-GOP cut points make `get_batch_frames_by_index` fail

Cutting H.264 at non-IDR keyframes (stream copy at `is_keyframe` packets) produces clips that decode
with "Decode Error occurred for picture N" followed by `IndexError` in `get_batch_frames_by_index`
(fewer decoded frames than the scanned index promised). OpenCV/FFmpeg decode the same clips with
corrupted leading frames but no failure. Re-encoding with closed GOPs avoids it. A graceful fallback
(return the frames that did decode, or an explicit error) would help.

### 4. Per-process throughput does not scale with threads or decoder slots

Through vLLM's loader on 1080p 10 s shots: 8 threads reach 9.9 clips/s with 2, 4 or 7 decoder slots
(OpenCV: 19.4 clips/s). `SimpleDecoder` calls appear to hold the GIL. Multi-process frontends hide
this; single-process integrations will not.

### 5. Multi-process NVDEC without CUDA MPS is capped by context time-slicing

`bench/raw_decode_bench.py`, 1080p H.264, one reused `CreateDecoder` per process, all frames: 1 process
2,190 frames/s; 2/4/8/16 processes **2,630 / 2,290 / 2,260 / 2,230 frames/s** aggregate without MPS — the
same ~2,300 cap for 640×360 — with one full CPU core per process spent in synchronization. With
`nvidia-cuda-mps-control -d` the same code gives 4,270 / 8,240 / 11,820 / 12,180 frames/s on ≤ 2 cores.
Worth a prominent note in the PyNvVideoCodec docs for anyone decoding from several processes on an
inference GPU.

### 6. Warm-up cost is on first decode, not on `CreateDecoder`

`CreateDecoder` + first packet is 1.7 ms, yet a fresh decoder per 10 s clip costs 297 ms versus 33 ms
reused. If expected, a note in the docs (and pointing at `reconfigure_decoder`) would save others the
detour.

## Questions

1. Roadmap/ETA for native MPEG-TS support in `SimpleDecoder` (scanned metadata, `get_batch_frames_by_index`)
   and for demuxer `Seek`/`TimestampFromFrame` on TS. Is the SIGSEGV known?
2. Is the stream-copy remux to fMP4 a reasonable production workaround, or is there a supported way to
   hand a TS elementary stream to `SimpleDecoder`?
3. Decoder caching best practice for many short clips of one codec/resolution across worker processes:
   is `SimpleDecoder(decoder_cache_size=N)` + `reconfigure_decoder` the intended pattern? Guidance on
   decoders per process vs. the 7 NVDEC engines on B200 when the same GPU runs inference under MPS?
4. Decode on one GPU, infer on another (NVLink/InfiniBand cluster): can decoded frames be handed over
   peer-to-peer from PyNvVideoCodec output, or is shipping the bitstream and decoding locally the
   recommended path?

Reproduction scripts: `bench/nvdec_advice_bench.py`, `bench/remux_vllm_pattern.py`,
`bench/vod_loader_bench.py`. We can share the test segments on request.
