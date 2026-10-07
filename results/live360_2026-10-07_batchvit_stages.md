
# /home/garam/nvdec-runs/live360-nvdec-asc12-batchvit

## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 36.9 | 42.8 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 29.4 | 34.5 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 1.7 | 2.9 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 26.6 | 31.8 | 15.0 | 17.4 | - |
| 2 remux TS->fMP4 | 1.00 | 3.9 | 4.6 | 3.6 | 5.3 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.3 | 1.7 | 0.8 | 1.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 20.3 | 24.7 | 9.7 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.2 | 0.3 | 0.2 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 6.8 | 7.7 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 3.9 | 4.8 | 4.1 | 4.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.1 | 0.2 | 0.1 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 3.6 | 4.3 | 3.7 | 3.7 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 101.9 | 135.7 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 101.4 | 135.1 | 106.6 | 113.8 | - |
| 5-6 HF processor call | 1.00 | 98.5 | 132.0 | 104.2 | 108.2 | - |
| 5 video preprocess | 1.00 | 95.0 | 127.2 | 100.5 | 104.5 | - |
| 5 resize+normalize (torch.compile, CPU) | 1.00 | 93.9 | 126.0 | 99.8 | 99.9 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d audio preprocess | 1.00 | 1.9 | 2.9 | 2.1 | 2.1 | - |
| 6d mel (ParakeetExtractor) | 1.00 | 1.6 | 2.6 | 1.8 | 1.8 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 2.00 | 70.4 | 72.7 | 53.0 | - | 54.2 |
| 7v vision encoder (per video) | 1.00 | 31.9 | 32.5 | 31.4 | - | 31.8 |
| 7a sound encoder (per call) | 1.00 | 71.2 | 72.9 | 71.4 | - | 71.2 |
  video_resize_norm: {'in': [12, 360, 640, 3], 'out': [12, 3, 384, 672], 'dtype': 'torch.bfloat16'}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 48, items/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 233.4 / 240.7 | decode 90.4 / 93.8 | e2e(server) 475.0 / 521.1 | frontend+IPC 146.9 / 186.3
  tokens: prompt 1784, generated 15.1, cached prompt tokens mean 0 (max 0), time/output token 6.5 ms
  API-server spread: 6 processes, requests per process [15, 3, 2, 2, 1, 1]
  client latency p50 0.48s p95 0.53s (24 ok), throughput per run 2.1 req/s
  server CPU per request (cpu-s): api 0.156, engine 0.338, mps 0.000, vllm_main 0.000; total 0.494; pod cgroup 0.504

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 32.8 | 37.8 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 31.7 | 36.9 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 1.7 | 2.7 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 28.7 | 33.0 | 15.9 | 17.9 | - |
| 2 remux TS->fMP4 | 1.00 | 4.4 | 5.0 | 4.0 | 5.3 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.4 | 1.8 | 0.9 | 1.6 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 21.3 | 25.0 | 9.9 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 0.3 | 0.3 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 106.6 | 132.8 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 106.1 | 132.5 | 110.3 | 118.1 | - |
| 5-6 HF processor call | 1.00 | 103.0 | 128.8 | 107.3 | 111.5 | - |
| 5 video preprocess | 1.00 | 101.4 | 127.0 | 105.7 | 109.8 | - |
| 5 resize+normalize (torch.compile, CPU) | 1.00 | 100.4 | 125.9 | 105.0 | 105.1 | - |
| 6d audio preprocess | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| hash (blake3) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| 7 encoder call (all items in the step) | 1.00 | 35.0 | 35.4 | 34.5 | - | 34.9 |
| 7v vision encoder (per video) | 1.00 | 31.9 | 32.3 | 31.5 | - | 31.8 |
  video_resize_norm: {'in': [12, 360, 640, 3], 'out': [12, 3, 384, 672], 'dtype': 'torch.bfloat16'}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 161.9 / 164.6 | decode 363.4 / 403.5 | e2e(server) 691.2 / 736.3 | frontend+IPC 148.7 / 176.8
  tokens: prompt 1705, generated 58.7, cached prompt tokens mean 0 (max 0), time/output token 6.4 ms
  API-server spread: 8 processes, requests per process [13, 3, 3, 1, 1, 1, 1, 1]
  client latency p50 0.69s p95 0.74s (24 ok), throughput per run 1.5 req/s
  server CPU per request (cpu-s): api 0.168, engine 0.550, mps 0.000, vllm_main 0.000; total 0.718; pod cgroup 0.727

## burst-av: 192 requests (3 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 170.3 | 263.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 157.7 | 246.7 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.3 | 7.2 | - | - |
| 2-4 video load_bytes total | 1.00 | 149.9 | 240.7 | 39.1 | - |
| 2 remux TS->fMP4 | 1.00 | 48.2 | 79.7 | 14.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 35.1 | 107.9 | 0.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 53.5 | 111.4 | 22.0 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 1.0 | 0.3 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 10.9 | 19.9 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 7.8 | 17.6 | 6.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.1 | 0.7 | 0.1 | - |
| 6b'' PyAV AAC decode | 1.00 | 7.0 | 16.9 | 5.6 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 357.4 | 688.7 | - | - |
| 5-6 processor (mm thread) | 1.00 | 126.0 | 142.2 | 125.4 | - |
| 5-6 HF processor call | 1.00 | 123.0 | 138.6 | 122.9 | - |
| 5 video preprocess | 1.00 | 118.8 | 134.4 | 118.7 | - |
| 5 resize+normalize (torch.compile, CPU) | 1.00 | 117.6 | 133.4 | 117.9 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d audio preprocess | 1.00 | 2.3 | 3.2 | 2.4 | - |
| 6d mel (ParakeetExtractor) | 1.00 | 2.1 | 2.9 | 2.1 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 10.6 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.14 | 220.6 | 293.9 | 186.9 | 220.6 |
| 7v vision encoder (per video) | 0.12 | 123.3 | 173.5 | 111.3 | 122.7 |
| 7a sound encoder (per call) | 0.12 | 74.8 | 91.9 | 76.7 | 74.6 |
  video_resize_norm: {'in': [12, 360, 640, 3], 'out': [12, 3, 384, 672], 'dtype': 'torch.bfloat16'}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 27, items/call mean 14.2 max 19
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 1979.4 / 2417.4 | decode 701.2 / 1841.7 | e2e(server) 3415.0 / 3531.3 | frontend+IPC 704.9 / 1151.7
  tokens: prompt 1784, generated 15.1, cached prompt tokens mean 0 (max 0), time/output token 48.1 ms
  API-server spread: 12 processes, requests per process [21, 19, 19, 18, 18, 17, 17, 16, 12, 12, 12, 11]
  client latency p50 3.42s p95 3.54s (192 ok), throughput per run 18.3, 18.7, 17.9 req/s
  server CPU per request (cpu-s): api 0.197, engine 0.060, mps 0.000, vllm_main 0.000; total 0.257; pod cgroup 0.261

## burst-v: 192 requests (3 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 159.9 | 252.0 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 158.5 | 251.3 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 3.7 | 7.5 | - | - |
| 2-4 video load_bytes total | 1.00 | 150.1 | 242.0 | 38.8 | - |
| 2 remux TS->fMP4 | 1.00 | 49.2 | 81.9 | 15.5 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 24.9 | 104.5 | 0.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 57.4 | 105.8 | 20.8 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 1.1 | 0.4 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 334.7 | 666.1 | - | - |
| 5-6 processor (mm thread) | 1.00 | 122.8 | 147.3 | 122.5 | - |
| 5-6 HF processor call | 1.00 | 119.2 | 142.4 | 119.6 | - |
| 5 video preprocess | 1.00 | 117.5 | 139.3 | 117.8 | - |
| 5 resize+normalize (torch.compile, CPU) | 1.00 | 116.5 | 137.4 | 117.1 | - |
| 6d audio preprocess | 1.00 | 0.0 | 0.0 | 0.0 | - |
| hash (blake3) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 10.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.12 | 145.9 | 232.8 | 135.9 | 132.3 |
| 7v vision encoder (per video) | 0.12 | 122.0 | 195.4 | 113.7 | 110.6 |
  video_resize_norm: {'in': [12, 360, 640, 3], 'out': [12, 3, 384, 672], 'dtype': 'torch.bfloat16'}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 8.0 max 14
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 1359.4 / 1823.9 | decode 1108.5 / 2014.7 | e2e(server) 3331.4 / 3440.8 | frontend+IPC 697.8 / 1034.3
  tokens: prompt 1705, generated 58.5, cached prompt tokens mean 0 (max 0), time/output token 19.9 ms
  API-server spread: 12 processes, requests per process [24, 19, 18, 17, 17, 16, 16, 16, 15, 12, 12, 10]
  client latency p50 3.34s p95 3.45s (192 ok), throughput per run 18.9, 18.5, 18.4 req/s
  server CPU per request (cpu-s): api 0.188, engine 0.059, mps 0.000, vllm_main 0.000; total 0.247; pod cgroup 0.251

== leftovers
none
0 MiB
