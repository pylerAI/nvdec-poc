# vod-360p-prod-cpu32


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 91.9 | 109.8 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 87.1 | 105.2 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.2 | 4.7 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 82.5 | 99.7 | 29.8 | 453.0 | - |
| 3a OpenCV open | 1.00 | 5.1 | 7.0 | 5.2 | 6.8 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 74.3 | 80.2 | 22.8 | 437.2 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.7 | 4.8 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 1.3 | 1.1 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.9 | 1.0 | 0.9 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 232.7 | 252.0 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 232.1 | 251.7 | 228.2 | 228.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 204.6 | 222.6 | 201.0 | 201.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 184.9 | 200.4 | 178.6 | 178.7 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.62 | 4.9 | 8.5 | 5.4 | 5.4 | - |
| hash (blake3) | 2.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 0.7 | 0.6 | 0.6 | - |
| 7 encoder call (all items in the step) | 1.00 | 86.0 | 92.1 | 86.4 | - | 85.8 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 44.9 | 48.7 | 45.1 | - | 44.3 |
| 7a sound encoder (per call) | 1.00 | 34.8 | 38.1 | 34.6 | - | 34.7 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 200.9 / 216.9 | decode 2400.6 / 2807.2 | e2e(server) 2934.2 / 3365.6 | frontend+IPC 361.8 / 391.2
  tokens: prompt 7520, generated 339.9, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 3 processes, requests per process [14, 8, 2]
  client latency p50 2.94s p95 3.37s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.802, engine 2.667, vllm_main 0.000; total 3.468; pod cgroup 3.488

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 89.8 | 114.0 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 88.9 | 113.1 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 2.5 | 3.7 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 85.6 | 108.0 | 29.1 | 427.1 | - |
| 3a OpenCV open | 1.00 | 5.2 | 7.2 | 5.0 | 6.9 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 77.3 | 98.7 | 22.4 | 411.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 238.6 | 247.6 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 238.2 | 247.0 | 231.8 | 231.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 208.6 | 216.2 | 203.3 | 203.5 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 192.6 | 200.0 | 186.7 | 186.8 | - |
| hash (blake3) | 1.00 | 0.4 | 0.5 | 0.4 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.3 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 52.1 | 54.8 | 52.2 | - | 52.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 45.9 | 48.4 | 45.8 | - | 45.2 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'opencv'}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 159.6 / 165.1 | decode 2187.6 / 3059.9 | e2e(server) 2689.7 / 3597.1 | frontend+IPC 361.6 / 387.5
  tokens: prompt 7336, generated 325.5, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 3 processes, requests per process [19, 3, 2]
  client latency p50 2.69s p95 3.60s (24 ok), throughput per run 0.4 req/s
  server CPU per request (cpu-s): api 0.772, engine 2.520, vllm_main 0.000; total 3.291; pod cgroup 3.309

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 149.2 | 171.2 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 128.3 | 158.5 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 3.9 | 11.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 114.6 | 145.2 | 36.1 | - |
| 3a OpenCV open | 1.00 | 11.1 | 21.2 | 5.9 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 96.6 | 129.0 | 28.2 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 8.1 | 43.0 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 2.0 | 5.7 | 1.2 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.8 | 5.4 | 1.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 449.3 | 837.6 | - | - |
| 5-6 processor (mm thread) | 1.00 | 237.7 | 273.5 | 227.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 208.7 | 243.9 | 199.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 173.6 | 220.7 | 173.7 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 5.7 | 48.7 | 5.1 | - |
| hash (blake3) | 2.00 | 0.4 | 0.8 | 0.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 1.5 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.44 | 171.4 | 468.9 | 208.9 | 171.4 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 47.2 | 53.4 | 46.5 | 46.5 |
| 7a sound encoder (per call) | 1.00 | 39.0 | 44.1 | 38.5 | 38.8 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 7, items/call mean 4.6 max 10; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 775.4 / 1107.9 | decode 4233.9 / 5243.0 | e2e(server) 5950.9 / 6475.2 | frontend+IPC 951.3 / 1529.8
  tokens: prompt 7396, generated 347.5, cached prompt tokens mean 4016 (max 4016), time/output token 12.2 ms
  API-server spread: 3 processes, requests per process [7, 5, 4]
  client latency p50 5.96s p95 6.48s (16 ok), throughput per run 1.2, 1.3 req/s
  server CPU per request (cpu-s): api 0.827, engine 0.774, vllm_main 0.000; total 1.601; pod cgroup 1.622

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 148.5 | 170.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 146.3 | 170.0 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 5.8 | 12.0 | - | - |
| 2-4 video load_bytes total | 1.00 | 138.4 | 162.2 | 35.1 | - |
| 3a OpenCV open | 1.00 | 7.0 | 19.2 | 4.3 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 126.4 | 139.4 | 28.8 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 439.1 | 870.5 | - | - |
| 5-6 processor (mm thread) | 1.00 | 218.5 | 261.2 | 217.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 189.1 | 229.4 | 190.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 166.3 | 207.6 | 173.9 | - |
| hash (blake3) | 1.00 | 0.7 | 1.0 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.56 | 68.0 | 98.6 | 66.6 | 68.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.56 | 58.4 | 82.7 | 57.3 | 57.2 |
  video_resize_norm: {'in': [1, 28, 3, 360, 640], 'out': [12320, 1536], 'grid_thw': [[14, 22, 40]]}
  video_decode_total: {'frames': [28, 360, 640, 3], 'backend': 'opencv'}
  encoder calls: 9, items/call mean 1.8 max 3; vision calls 9, videos/call mean 1.8 max 3
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 414.2 / 465.7 | decode 3377.8 / 4223.8 | e2e(server) 4372.6 / 5407.1 | frontend+IPC 740.6 / 1182.1
  tokens: prompt 7198, generated 279.6, cached prompt tokens mean 4016 (max 4016), time/output token 11.8 ms
  API-server spread: 3 processes, requests per process [6, 5, 5]
  client latency p50 4.38s p95 5.41s (16 ok), throughput per run 1.5, 1.8 req/s
  server CPU per request (cpu-s): api 0.856, engine 0.603, vllm_main 0.000; total 1.459; pod cgroup 1.479

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1246.2 | 1365.3 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 946.0 | 1316.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 17.2 | 73.5 | - | - |
| 2-4 video load_bytes total | 1.00 | 447.7 | 561.1 | 61.1 | - |
| 3a OpenCV open | 1.00 | 17.3 | 81.6 | 6.8 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 414.9 | 497.4 | 51.1 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 263.3 | 739.0 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 11.6 | 63.2 | 2.6 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 10.6 | 62.1 | 2.3 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 2519.4 | 4557.5 | - | - |
| 5-6 processor (mm thread) | 1.00 | 227.7 | 265.8 | 228.6 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 198.4 | 236.8 | 199.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 175.9 | 211.8 | 176.8 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.85 | 4.5 | 13.5 | 4.5 | - |
| hash (blake3) | 2.00 | 0.4 | 1.3 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 1.5 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.15 | 526.3 | 1209.8 | 558.4 | 526.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 43.2 | 48.9 | 43.0 | 42.6 |
| 7a sound encoder (per call) | 1.00 | 33.9 | 39.0 | 33.9 | 33.8 |
  video_resize_norm: {'in': [1, 28, 3, 360, 640], 'out': [12320, 1536], 'grid_thw': [[14, 22, 40]]}
  video_decode_total: {'frames': [28, 360, 640, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 19, items/call mean 13.5 max 30; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1833.2 | prefill 2344.3 / 4391.0 | decode 14983.2 / 20270.1 | e2e(server) 23151.9 / 24417.5 | frontend+IPC 4020.8 / 7753.8
  tokens: prompt 7443, generated 341.4, cached prompt tokens mean 4016 (max 4016), time/output token 43.5 ms
  API-server spread: 3 processes, requests per process [45, 42, 41]
  client latency p50 23.17s p95 24.42s (128 ok), throughput per run 2.6, 2.4 req/s
  server CPU per request (cpu-s): api 0.916, engine 0.402, vllm_main 0.000; total 1.318; pod cgroup 1.325

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 979.2 | 1346.8 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 974.6 | 1334.3 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 25.2 | 41.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 469.9 | 562.3 | 57.1 | - |
| 3a OpenCV open | 1.00 | 19.0 | 69.5 | 6.3 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 425.1 | 499.1 | 47.6 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 2559.9 | 4315.0 | - | - |
| 5-6 processor (mm thread) | 1.00 | 223.0 | 421.1 | 229.1 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 195.7 | 390.2 | 200.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 175.1 | 361.1 | 180.5 | - |
| hash (blake3) | 1.00 | 0.8 | 1.4 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 1.0 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.23 | 152.6 | 195.0 | 140.1 | 152.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.23 | 128.5 | 159.9 | 116.1 | 124.9 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'opencv'}
  encoder calls: 29, items/call mean 4.4 max 6; vision calls 29, videos/call mean 4.4 max 6
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 854.0 / 949.8 | decode 12237.2 / 16090.2 | e2e(server) 17021.2 / 19095.1 | frontend+IPC 3817.5 / 6093.3
  tokens: prompt 7243, generated 288.1, cached prompt tokens mean 4016 (max 4016), time/output token 43.6 ms
  API-server spread: 3 processes, requests per process [43, 43, 42]
  client latency p50 17.05s p95 19.10s (128 ok), throughput per run 3.2, 3.1 req/s
  server CPU per request (cpu-s): api 0.899, engine 0.323, vllm_main 0.000; total 1.222; pod cgroup 1.228

# vod-360p-nvdec-cpu32


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 65.1 | 71.4 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 60.5 | 66.4 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.4 | 4.0 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 56.0 | 60.1 | 28.7 | 30.7 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.5 | 4.8 | 1.8 | 3.7 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 50.1 | 55.1 | 24.9 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 0.5 | 0.5 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.7 | 4.8 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.0 | 1.4 | 1.0 | 1.0 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.8 | 1.2 | 0.8 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 227.6 | 246.3 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 227.2 | 246.0 | 229.3 | 229.5 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 200.4 | 218.8 | 201.7 | 201.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 177.2 | 188.5 | 177.4 | 177.6 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.50 | 4.3 | 9.1 | 5.0 | 5.0 | - |
| hash (blake3) | 2.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 0.9 | 0.6 | 0.6 | - |
| 7 encoder call (all items in the step) | 1.00 | 95.4 | 107.3 | 96.4 | - | 95.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 49.4 | 53.7 | 49.1 | - | 48.6 |
| 7a sound encoder (per call) | 1.00 | 40.4 | 45.9 | 40.6 | - | 40.3 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 20736000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 219.1 / 235.1 | decode 2412.9 / 2849.9 | e2e(server) 2960.7 / 3426.0 | frontend+IPC 338.3 / 365.7
  tokens: prompt 7520, generated 324.8, cached prompt tokens mean 4016 (max 4016), time/output token 7.6 ms
  API-server spread: 3 processes, requests per process [15, 5, 4]
  client latency p50 2.96s p95 3.43s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.387, engine 2.767, mps 0.001, vllm_main 0.000; total 3.155; pod cgroup 3.173

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 55.3 | 58.7 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 54.1 | 57.5 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 2.8 | 4.1 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 50.1 | 53.7 | 27.3 | 29.3 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.4 | 4.4 | 1.7 | 3.6 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 44.7 | 48.5 | 23.8 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 0.5 | 0.5 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 228.4 | 241.3 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 227.9 | 240.9 | 226.7 | 226.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 201.5 | 215.4 | 199.8 | 200.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 180.9 | 190.0 | 179.2 | 179.4 | - |
| hash (blake3) | 1.00 | 0.4 | 0.4 | 0.4 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 55.2 | 65.5 | 56.2 | - | 55.1 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 48.9 | 58.5 | 49.5 | - | 48.2 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 20736000}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 169.3 / 180.4 | decode 2099.0 / 3559.3 | e2e(server) 2596.4 / 4049.9 | frontend+IPC 327.3 / 337.9
  tokens: prompt 7336, generated 310.6, cached prompt tokens mean 4016 (max 4016), time/output token 7.6 ms
  API-server spread: 3 processes, requests per process [11, 10, 3]
  client latency p50 2.60s p95 4.05s (24 ok), throughput per run 0.4 req/s
  server CPU per request (cpu-s): api 0.375, engine 2.594, mps 0.001, vllm_main 0.000; total 2.970; pod cgroup 2.988

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 97.7 | 139.1 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 85.3 | 135.5 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 3.4 | 10.4 | - | - |
| 2-4 video load_bytes total | 1.00 | 74.9 | 122.1 | 33.9 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.1 | 63.6 | 1.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 64.4 | 112.6 | 30.8 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 0.9 | 0.5 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.3 | 10.7 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 4.6 | 1.4 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.0 | 4.4 | 1.2 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 461.0 | 740.6 | - | - |
| 5-6 processor (mm thread) | 1.00 | 235.4 | 284.9 | 237.6 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 206.6 | 250.4 | 208.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 186.0 | 217.0 | 184.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 4.7 | 7.6 | 4.4 | - |
| hash (blake3) | 2.00 | 0.3 | 0.7 | 0.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 1.3 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.38 | 283.0 | 454.1 | 249.0 | 242.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 48.6 | 56.4 | 48.0 | 47.9 |
| 7a sound encoder (per call) | 1.00 | 38.9 | 45.5 | 39.2 | 38.6 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 20736000}
  encoder calls: 6, items/call mean 5.3 max 10; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 716.6 / 1072.9 | decode 4728.5 / 5737.9 | e2e(server) 6381.1 / 6793.7 | frontend+IPC 947.5 / 1064.4
  tokens: prompt 7396, generated 355.4, cached prompt tokens mean 4016 (max 4016), time/output token 12.7 ms
  API-server spread: 3 processes, requests per process [6, 5, 5]
  client latency p50 6.39s p95 6.80s (16 ok), throughput per run 1.2, 1.3 req/s
  server CPU per request (cpu-s): api 0.347, engine 0.818, mps 0.000, vllm_main 0.001; total 1.166; pod cgroup 1.185

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 93.3 | 146.6 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 92.3 | 145.4 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.6 | 20.0 | - | - |
| 2-4 video load_bytes total | 1.00 | 85.7 | 138.2 | 36.9 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 2.9 | 70.3 | 1.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 64.4 | 122.1 | 33.6 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 0.8 | 0.5 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 448.0 | 729.4 | - | - |
| 5-6 processor (mm thread) | 1.00 | 229.5 | 333.4 | 231.1 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 199.8 | 295.4 | 203.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 180.9 | 269.3 | 184.9 | - |
| hash (blake3) | 1.00 | 0.4 | 1.0 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.50 | 80.7 | 102.2 | 77.3 | 79.8 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.50 | 68.9 | 86.6 | 66.2 | 67.2 |
  video_resize_norm: {'in': [1, 28, 3, 360, 640], 'out': [12320, 1536], 'grid_thw': [[14, 22, 40]]}
  video_decode_total: {'frames': [28, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 19353600}
  encoder calls: 8, items/call mean 2.0 max 3; vision calls 8, videos/call mean 2.0 max 3
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 470.3 / 494.2 | decode 3626.6 / 4760.4 | e2e(server) 4606.2 / 5982.5 | frontend+IPC 722.4 / 1017.5
  tokens: prompt 7198, generated 278.1, cached prompt tokens mean 4016 (max 4016), time/output token 12.5 ms
  API-server spread: 3 processes, requests per process [6, 5, 5]
  client latency p50 4.61s p95 5.99s (16 ok), throughput per run 1.3, 1.6 req/s
  server CPU per request (cpu-s): api 0.334, engine 0.672, mps 0.000, vllm_main 0.000; total 1.006; pod cgroup 1.025

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 613.9 | 844.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 443.4 | 797.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 8.7 | 37.1 | - | - |
| 2-4 video load_bytes total | 1.00 | 252.1 | 412.6 | 37.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 105.3 | 227.9 | 1.1 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 116.6 | 256.1 | 33.9 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 4.6 | 0.9 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 138.9 | 499.4 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.6 | 5.7 | 1.2 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.5 | 5.4 | 1.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 2532.9 | 4757.3 | - | - |
| 5-6 processor (mm thread) | 1.00 | 233.9 | 260.3 | 233.6 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 204.0 | 228.4 | 204.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 180.8 | 199.9 | 180.6 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.89 | 4.6 | 5.8 | 4.2 | - |
| hash (blake3) | 2.00 | 0.3 | 0.6 | 0.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 0.8 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.14 | 733.5 | 1434.9 | 680.7 | 689.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 48.6 | 54.8 | 48.5 | 48.0 |
| 7a sound encoder (per call) | 1.00 | 40.2 | 47.2 | 40.6 | 40.2 |
  video_resize_norm: {'in': [1, 28, 3, 360, 640], 'out': [12320, 1536], 'grid_thw': [[14, 22, 40]]}
  video_decode_total: {'frames': [28, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 19353600}
  encoder calls: 18, items/call mean 14.2 max 30; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 2082.3 | prefill 3616.2 / 5152.2 | decode 16055.7 / 21332.7 | e2e(server) 24419.2 / 25641.7 | frontend+IPC 3776.8 / 6946.8
  tokens: prompt 7443, generated 336.5, cached prompt tokens mean 4016 (max 4016), time/output token 47.1 ms
  API-server spread: 3 processes, requests per process [43, 43, 42]
  client latency p50 24.43s p95 25.68s (128 ok), throughput per run 2.5, 2.3 req/s
  server CPU per request (cpu-s): api 0.313, engine 0.439, mps 0.000, vllm_main 0.000; total 0.752; pod cgroup 0.758

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 477.1 | 834.9 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 473.8 | 832.3 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 23.1 | 44.5 | - | - |
| 2-4 video load_bytes total | 1.00 | 286.4 | 439.1 | 47.1 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 104.8 | 237.4 | 1.1 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 132.9 | 268.9 | 43.7 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 1.6 | 0.5 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 2201.9 | 3983.8 | - | - |
| 5-6 processor (mm thread) | 1.00 | 227.2 | 256.0 | 226.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 198.9 | 225.0 | 198.5 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 178.8 | 203.3 | 179.8 | - |
| hash (blake3) | 1.00 | 0.4 | 0.7 | 0.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.23 | 156.3 | 208.2 | 138.2 | 155.4 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.23 | 130.0 | 172.8 | 115.5 | 126.2 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 20736000}
  encoder calls: 30, items/call mean 4.3 max 8; vision calls 30, videos/call mean 4.3 max 8
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 794.4 / 1094.9 | decode 13054.2 / 17025.9 | e2e(server) 16768.4 / 19346.9 | frontend+IPC 3074.6 / 5150.4
  tokens: prompt 7243, generated 289.4, cached prompt tokens mean 4016 (max 4016), time/output token 45.6 ms
  API-server spread: 3 processes, requests per process [44, 44, 40]
  client latency p50 16.78s p95 19.35s (128 ok), throughput per run 3.4, 3.2 req/s
  server CPU per request (cpu-s): api 0.313, engine 0.321, mps 0.000, vllm_main 0.000; total 0.634; pod cgroup 0.639

# vod-360p-nvdec-asc12-cpu32


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 64.9 | 73.8 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 60.3 | 68.9 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.1 | 3.9 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 56.7 | 65.6 | 26.6 | 28.5 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.2 | 3.5 | 1.5 | 3.3 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 51.1 | 60.9 | 23.4 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 0.5 | 0.5 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.4 | 4.4 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.0 | 1.2 | 1.0 | 1.0 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.8 | 1.0 | 0.8 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 216.7 | 244.2 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 216.3 | 243.6 | 219.0 | 219.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 191.6 | 214.7 | 192.8 | 193.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 170.4 | 195.7 | 172.2 | 172.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.96 | 4.2 | 5.9 | 4.7 | 4.7 | - |
| hash (blake3) | 2.00 | 0.2 | 0.3 | 0.3 | 0.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.5 | 0.5 | 0.5 | - |
| 7 encoder call (all items in the step) | 1.00 | 85.3 | 88.5 | 85.5 | - | 85.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 44.5 | 46.0 | 44.4 | - | 43.9 |
| 7a sound encoder (per call) | 1.00 | 34.5 | 36.8 | 34.4 | - | 34.4 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 20736000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 197.9 / 204.4 | decode 2380.8 / 2699.5 | e2e(server) 2909.3 / 3228.9 | frontend+IPC 323.2 / 365.3
  tokens: prompt 7520, generated 326.3, cached prompt tokens mean 4016 (max 4016), time/output token 7.2 ms
  API-server spread: 3 processes, requests per process [13, 9, 2]
  client latency p50 2.91s p95 3.23s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.396, engine 2.638, mps 0.001, vllm_main 0.000; total 3.035; pod cgroup 3.053

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 55.5 | 59.5 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 54.5 | 58.2 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 2.9 | 3.5 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 50.1 | 54.2 | 26.0 | 27.9 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.3 | 3.8 | 1.6 | 3.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 45.2 | 48.3 | 22.4 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 0.5 | 0.5 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 202.7 | 249.2 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 202.5 | 248.9 | 206.0 | 206.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 176.2 | 218.6 | 181.4 | 181.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 162.7 | 197.7 | 166.1 | 166.3 | - |
| hash (blake3) | 1.00 | 0.4 | 0.5 | 0.4 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 51.0 | 55.1 | 51.3 | - | 50.9 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 44.8 | 48.4 | 45.1 | - | 44.2 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 20736000}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 156.2 / 166.4 | decode 1992.0 / 3154.5 | e2e(server) 2433.6 / 3644.2 | frontend+IPC 296.6 / 346.0
  tokens: prompt 7336, generated 308.4, cached prompt tokens mean 4016 (max 4016), time/output token 7.3 ms
  API-server spread: 6 processes, requests per process [8, 6, 4, 4, 1, 1]
  client latency p50 2.44s p95 3.65s (24 ok), throughput per run 0.4 req/s
  server CPU per request (cpu-s): api 0.373, engine 2.469, mps 0.001, vllm_main 0.000; total 2.843; pod cgroup 2.861

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 79.0 | 1180.2 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 73.1 | 1174.4 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.8 | 1061.4 | - | - |
| 2-4 video load_bytes total | 1.00 | 68.8 | 110.6 | 42.5 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.4 | 4.8 | 1.7 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 63.7 | 104.6 | 38.9 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 1.0 | 0.5 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.9 | 7.3 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 3.6 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.0 | 3.4 | 1.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 244.6 | 425.7 | - | - |
| 5-6 processor (mm thread) | 1.00 | 243.9 | 254.8 | 235.5 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 214.0 | 222.4 | 207.2 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 188.1 | 200.8 | 185.9 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 4.7 | 6.2 | 4.7 | - |
| hash (blake3) | 2.00 | 0.3 | 0.4 | 0.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.7 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.38 | 186.2 | 500.5 | 231.2 | 144.4 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 44.8 | 50.1 | 44.5 | 43.4 |
| 7a sound encoder (per call) | 1.00 | 36.0 | 47.1 | 35.8 | 35.8 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 20736000}
  encoder calls: 6, items/call mean 5.3 max 12; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 919.3 / 1001.6 | decode 4511.1 / 5431.0 | e2e(server) 5906.8 / 6990.5 | frontend+IPC 574.8 / 1464.5
  tokens: prompt 7396, generated 350.8, cached prompt tokens mean 4016 (max 4016), time/output token 12.6 ms
  API-server spread: 8 processes, requests per process [3, 3, 2, 2, 2, 2, 1, 1]
  client latency p50 5.91s p95 7.00s (16 ok), throughput per run 1.1, 1.3 req/s
  server CPU per request (cpu-s): api 0.401, engine 0.819, mps 0.001, vllm_main 0.000; total 1.221; pod cgroup 1.242

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 92.4 | 164.6 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 91.0 | 163.8 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.8 | 15.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 83.4 | 145.7 | 43.2 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.5 | 5.1 | 1.7 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 74.7 | 132.0 | 39.2 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 3.5 | 0.5 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 249.9 | 680.3 | - | - |
| 5-6 processor (mm thread) | 1.00 | 223.2 | 251.5 | 215.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 196.0 | 224.6 | 190.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 177.8 | 205.4 | 174.4 | - |
| hash (blake3) | 1.00 | 0.4 | 0.8 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.44 | 83.7 | 178.9 | 91.5 | 83.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.44 | 71.8 | 149.2 | 73.1 | 70.4 |
  video_resize_norm: {'in': [1, 28, 3, 360, 640], 'out': [12320, 1536], 'grid_thw': [[14, 22, 40]]}
  video_decode_total: {'frames': [28, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 19353600}
  encoder calls: 7, items/call mean 2.3 max 5; vision calls 7, videos/call mean 2.3 max 5
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 546.0 / 651.2 | decode 3360.7 / 3828.9 | e2e(server) 4363.1 / 4998.2 | frontend+IPC 520.3 / 1011.1
  tokens: prompt 7198, generated 273.8, cached prompt tokens mean 4016 (max 4016), time/output token 12.3 ms
  API-server spread: 7 processes, requests per process [6, 3, 2, 2, 1, 1, 1]
  client latency p50 4.37s p95 5.00s (16 ok), throughput per run 1.6, 1.6 req/s
  server CPU per request (cpu-s): api 0.341, engine 0.612, mps 0.000, vllm_main 0.000; total 0.953; pod cgroup 0.973

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 335.0 | 1118.9 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 328.7 | 1113.3 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 4.0 | 19.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 296.6 | 482.0 | 58.8 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 123.3 | 193.6 | 1.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 169.5 | 347.9 | 54.4 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 8.6 | 1.1 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.4 | 9.7 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.4 | 3.8 | 1.3 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.2 | 3.6 | 1.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 612.2 | 1350.9 | - | - |
| 5-6 processor (mm thread) | 1.00 | 272.2 | 328.4 | 272.0 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 239.5 | 290.2 | 239.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 211.2 | 262.3 | 216.7 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.93 | 4.8 | 8.4 | 4.6 | - |
| hash (blake3) | 2.00 | 0.3 | 0.6 | 0.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 1.1 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.14 | 759.9 | 1292.0 | 622.6 | 643.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 44.9 | 52.8 | 45.0 | 44.2 |
| 7a sound encoder (per call) | 1.00 | 35.6 | 42.4 | 36.1 | 35.5 |
  video_resize_norm: {'in': [1, 28, 3, 360, 640], 'out': [12320, 1536], 'grid_thw': [[14, 22, 40]]}
  video_decode_total: {'frames': [28, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 19353600}
  encoder calls: 18, items/call mean 14.2 max 30; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.1 / 0.2 | prefill 4101.8 / 7065.4 | decode 16175.7 / 20320.3 | e2e(server) 22411.1 / 23661.0 | frontend+IPC 2127.0 / 2645.8
  tokens: prompt 7443, generated 338.8, cached prompt tokens mean 4016 (max 4016), time/output token 48.2 ms
  API-server spread: 12 processes, requests per process [13, 12, 12, 12, 12, 11, 10, 10, 10, 9, 9, 8]
  client latency p50 22.42s p95 23.67s (128 ok), throughput per run 2.6, 2.4 req/s
  server CPU per request (cpu-s): api 0.396, engine 0.419, mps 0.000, vllm_main 0.000; total 0.814; pod cgroup 0.820

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 340.1 | 1114.4 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 339.2 | 1111.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 10.5 | 1027.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 311.4 | 436.5 | 58.8 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.5 | 218.1 | 1.5 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 166.1 | 310.6 | 54.9 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.5 | 3.4 | 0.8 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 616.9 | 1274.5 | - | - |
| 5-6 processor (mm thread) | 1.00 | 265.1 | 315.5 | 272.5 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 233.5 | 278.4 | 240.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 219.2 | 258.1 | 223.1 | - |
| hash (blake3) | 1.00 | 0.4 | 0.9 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.14 | 172.1 | 445.7 | 220.5 | 171.4 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.14 | 140.4 | 366.9 | 178.5 | 135.3 |
  video_resize_norm: {'in': [1, 30, 3, 360, 640], 'out': [13200, 1536], 'grid_thw': [[15, 22, 40]]}
  video_decode_total: {'frames': [30, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 20736000}
  encoder calls: 18, items/call mean 7.1 max 15; vision calls 18, videos/call mean 7.1 max 15
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 2295.7 / 3342.9 | decode 11939.5 / 15265.5 | e2e(server) 15483.0 / 18213.3 | frontend+IPC 1764.5 / 2205.3
  tokens: prompt 7243, generated 291.3, cached prompt tokens mean 4016 (max 4016), time/output token 41.1 ms
  API-server spread: 12 processes, requests per process [14, 12, 12, 11, 11, 11, 11, 10, 10, 9, 9, 8]
  client latency p50 15.49s p95 18.22s (128 ok), throughput per run 3.6, 3.3 req/s
  server CPU per request (cpu-s): api 0.389, engine 0.313, mps 0.000, vllm_main 0.000; total 0.702; pod cgroup 0.707

# vod-480p-prod


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 132.8 | 145.9 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 129.0 | 140.6 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.1 | 3.9 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 125.1 | 135.3 | 41.7 | 790.1 | - |
| 3a OpenCV open | 1.00 | 6.6 | 9.8 | 7.0 | 8.6 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 113.9 | 122.4 | 33.1 | 770.4 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.2 | 3.7 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 1.3 | 1.1 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.9 | 1.1 | 0.9 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 346.4 | 363.4 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 346.0 | 362.9 | 344.6 | 344.8 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 306.0 | 322.1 | 305.0 | 305.2 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 265.9 | 278.0 | 264.1 | 264.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 4.6 | 5.6 | 4.7 | 4.7 | - |
| hash (blake3) | 2.00 | 0.5 | 0.6 | 0.4 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.6 | 0.5 | 0.5 | - |
| 7 encoder call (all items in the step) | 1.00 | 99.8 | 103.9 | 99.6 | - | 99.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 53.3 | 56.5 | 53.4 | - | 52.4 |
| 7a sound encoder (per call) | 1.00 | 37.3 | 40.1 | 37.3 | - | 37.1 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 230.7 / 240.5 | decode 2490.3 / 2818.7 | e2e(server) 3235.0 / 3615.1 | frontend+IPC 525.3 / 560.9
  tokens: prompt 8705, generated 333.2, cached prompt tokens mean 4016 (max 4016), time/output token 7.3 ms
  API-server spread: 1 processes, requests per process [24]
  client latency p50 3.24s p95 3.66s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 1.262, engine 2.750, vllm_main 0.000; total 4.013; pod cgroup 4.034

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 121.2 | 159.3 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 120.3 | 158.1 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 3.2 | 4.6 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 116.1 | 153.0 | 43.0 | 756.8 | - |
| 3a OpenCV open | 1.00 | 7.4 | 13.3 | 7.4 | 9.0 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 105.4 | 136.8 | 33.9 | 738.2 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 343.0 | 375.5 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 342.6 | 375.2 | 345.0 | 345.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 302.9 | 337.6 | 305.7 | 306.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 265.6 | 289.3 | 267.6 | 267.8 | - |
| hash (blake3) | 1.00 | 0.6 | 0.7 | 0.6 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 63.1 | 71.5 | 63.9 | - | 63.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 54.4 | 62.4 | 55.2 | - | 53.6 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'opencv'}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 185.0 / 215.8 | decode 2354.1 / 3451.1 | e2e(server) 3059.5 / 4165.9 | frontend+IPC 529.0 / 563.6
  tokens: prompt 8521, generated 326.1, cached prompt tokens mean 4016 (max 4016), time/output token 7.3 ms
  API-server spread: 2 processes, requests per process [13, 11]
  client latency p50 3.06s p95 4.17s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 1.227, engine 2.676, vllm_main 0.000; total 3.903; pod cgroup 3.925

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 236.0 | 256.1 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 226.0 | 244.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 6.2 | 16.6 | - | - |
| 2-4 video load_bytes total | 1.00 | 211.3 | 231.9 | 54.4 | - |
| 3a OpenCV open | 1.00 | 12.2 | 29.8 | 8.4 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 191.6 | 216.3 | 43.8 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 6.0 | 15.5 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 2.6 | 11.5 | 1.5 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 2.4 | 10.9 | 1.2 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 686.3 | 1539.1 | - | - |
| 5-6 processor (mm thread) | 1.00 | 351.2 | 388.0 | 347.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 308.6 | 344.5 | 305.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 264.2 | 292.7 | 263.2 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 5.0 | 14.7 | 4.9 | - |
| hash (blake3) | 2.00 | 0.6 | 1.4 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.7 | 1.2 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.56 | 202.7 | 313.1 | 180.7 | 202.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 54.6 | 60.7 | 54.0 | 53.6 |
| 7a sound encoder (per call) | 1.00 | 39.4 | 43.8 | 38.7 | 39.3 |
  video_resize_norm: {'in': [1, 28, 3, 480, 854], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 9, items/call mean 3.6 max 6; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 777.2 / 920.4 | decode 4951.6 / 5424.2 | e2e(server) 6805.0 / 7545.6 | frontend+IPC 1224.8 / 2068.7
  tokens: prompt 8537, generated 352.4, cached prompt tokens mean 4016 (max 4016), time/output token 13.1 ms
  API-server spread: 3 processes, requests per process [6, 6, 4]
  client latency p50 6.86s p95 7.61s (16 ok), throughput per run 1.1, 1.2 req/s
  server CPU per request (cpu-s): api 1.394, engine 0.873, vllm_main 0.000; total 2.267; pod cgroup 2.293

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 233.9 | 261.2 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 228.7 | 260.5 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 8.2 | 12.2 | - | - |
| 2-4 video load_bytes total | 1.00 | 220.5 | 247.4 | 52.6 | - |
| 3a OpenCV open | 1.00 | 11.9 | 26.2 | 6.6 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 205.6 | 220.3 | 43.7 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 666.0 | 1392.1 | - | - |
| 5-6 processor (mm thread) | 1.00 | 334.1 | 382.5 | 339.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 296.1 | 335.9 | 300.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 260.0 | 305.3 | 265.1 | - |
| hash (blake3) | 1.00 | 0.9 | 1.5 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.62 | 71.3 | 127.8 | 81.6 | 68.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.62 | 63.3 | 105.3 | 69.1 | 59.4 |
  video_resize_norm: {'in': [1, 28, 3, 480, 854], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 480, 854, 3], 'backend': 'opencv'}
  encoder calls: 10, items/call mean 1.6 max 3; vision calls 10, videos/call mean 1.6 max 3
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 500.4 / 585.1 | decode 3795.6 / 5317.1 | e2e(server) 5324.1 / 6883.3 | frontend+IPC 1035.6 / 1713.3
  tokens: prompt 8334, generated 313.6, cached prompt tokens mean 4016 (max 4016), time/output token 12.8 ms
  API-server spread: 3 processes, requests per process [6, 6, 4]
  client latency p50 5.33s p95 6.89s (16 ok), throughput per run 1.2, 1.5 req/s
  server CPU per request (cpu-s): api 1.442, engine 0.736, vllm_main 0.001; total 2.178; pod cgroup 2.199

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 2271.2 | 2552.8 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1831.5 | 2507.4 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 22.2 | 82.4 | - | - |
| 2-4 video load_bytes total | 1.00 | 895.8 | 1087.8 | 98.4 | - |
| 3a OpenCV open | 1.00 | 34.2 | 118.1 | 9.7 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 820.9 | 988.0 | 84.9 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 406.2 | 1285.3 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 12.6 | 83.0 | 2.8 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 11.4 | 79.3 | 2.4 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 4003.4 | 7128.1 | - | - |
| 5-6 processor (mm thread) | 1.00 | 353.2 | 440.4 | 349.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 308.7 | 384.9 | 308.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 265.9 | 306.9 | 266.6 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.95 | 4.7 | 7.6 | 4.6 | - |
| hash (blake3) | 2.00 | 0.7 | 1.5 | 0.5 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 1.2 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.17 | 610.8 | 989.6 | 585.0 | 607.9 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 53.4 | 58.6 | 53.4 | 52.6 |
| 7a sound encoder (per call) | 1.00 | 38.2 | 44.6 | 38.4 | 38.2 |
  video_resize_norm: {'in': [1, 28, 3, 480, 854], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 480, 854, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 22, items/call mean 11.6 max 20; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 3378.4 / 4630.7 | decode 18082.1 / 24192.6 | e2e(server) 28343.8 / 30518.8 | frontend+IPC 6930.8 / 10484.1
  tokens: prompt 8600, generated 349.7, cached prompt tokens mean 4016 (max 4016), time/output token 50.8 ms
  API-server spread: 3 processes, requests per process [44, 42, 42]
  client latency p50 28.36s p95 30.53s (128 ok), throughput per run 2.1, 2.1 req/s
  server CPU per request (cpu-s): api 1.646, engine 0.479, vllm_main 0.000; total 2.124; pod cgroup 2.133

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1893.0 | 2621.3 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1841.0 | 2611.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 29.6 | 91.6 | - | - |
| 2-4 video load_bytes total | 1.00 | 905.8 | 1106.7 | 95.9 | - |
| 3a OpenCV open | 1.00 | 63.6 | 108.4 | 9.6 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 826.9 | 1006.2 | 82.4 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 4169.0 | 7049.3 | - | - |
| 5-6 processor (mm thread) | 1.00 | 342.9 | 403.7 | 353.0 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 303.3 | 353.3 | 313.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 268.2 | 313.1 | 275.3 | - |
| hash (blake3) | 1.00 | 1.1 | 1.8 | 0.7 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.38 | 130.3 | 173.7 | 118.6 | 129.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.38 | 107.8 | 144.5 | 98.8 | 104.9 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'opencv'}
  encoder calls: 48, items/call mean 2.7 max 5; vision calls 48, videos/call mean 2.7 max 5
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 691.3 / 906.1 | decode 14864.0 / 20070.2 | e2e(server) 21749.5 / 25158.8 | frontend+IPC 6523.8 / 9792.2
  tokens: prompt 8395, generated 305.6, cached prompt tokens mean 4016 (max 4016), time/output token 49.1 ms
  API-server spread: 3 processes, requests per process [44, 42, 42]
  client latency p50 21.75s p95 25.17s (128 ok), throughput per run 2.7, 2.5 req/s
  server CPU per request (cpu-s): api 1.656, engine 0.382, vllm_main 0.000; total 2.037; pod cgroup 2.045

# vod-480p-nvdec


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 83.7 | 90.1 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 79.2 | 83.6 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.6 | 5.9 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 74.3 | 77.6 | 29.2 | 31.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.1 | 5.4 | 1.9 | 4.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 67.5 | 71.3 | 24.5 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 0.9 | 0.8 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.4 | 4.8 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.0 | 1.3 | 1.0 | 1.0 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.8 | 1.1 | 0.9 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 347.7 | 367.6 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 347.3 | 367.1 | 342.4 | 342.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 307.0 | 325.0 | 302.6 | 302.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 263.3 | 278.3 | 261.7 | 261.9 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.67 | 4.2 | 6.5 | 4.4 | 4.4 | - |
| hash (blake3) | 2.00 | 0.4 | 0.6 | 0.4 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.9 | 0.6 | 0.6 | - |
| 7 encoder call (all items in the step) | 1.00 | 96.0 | 101.5 | 96.4 | - | 95.8 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.6 | 54.6 | 52.2 | - | 50.8 |
| 7a sound encoder (per call) | 1.00 | 35.1 | 38.5 | 35.3 | - | 34.9 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 36892800}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 220.8 / 235.6 | decode 2425.0 / 2948.1 | e2e(server) 3116.2 / 3637.6 | frontend+IPC 480.3 / 525.6
  tokens: prompt 8705, generated 338.0, cached prompt tokens mean 4016 (max 4016), time/output token 7.4 ms
  API-server spread: 3 processes, requests per process [15, 8, 1]
  client latency p50 3.12s p95 3.64s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.506, engine 2.795, mps 0.001, vllm_main 0.000; total 3.303; pod cgroup 3.331

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 72.0 | 80.0 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 70.9 | 78.2 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 3.2 | 4.5 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 67.0 | 73.3 | 29.7 | 31.9 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.8 | 4.6 | 1.8 | 3.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 60.2 | 67.4 | 25.3 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 0.8 | 0.8 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 326.8 | 369.0 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 326.5 | 368.5 | 333.1 | 333.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 287.4 | 332.1 | 293.5 | 293.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 256.0 | 283.0 | 255.9 | 256.2 | - |
| hash (blake3) | 1.00 | 0.5 | 0.8 | 0.5 | 0.5 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 61.1 | 67.7 | 61.4 | - | 61.1 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 52.7 | 55.9 | 52.6 | - | 51.7 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 36892800}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 177.6 / 189.0 | decode 2378.4 / 3377.1 | e2e(server) 3013.5 / 3998.6 | frontend+IPC 451.0 / 492.3
  tokens: prompt 8521, generated 332.4, cached prompt tokens mean 4016 (max 4016), time/output token 7.3 ms
  API-server spread: 3 processes, requests per process [14, 7, 3]
  client latency p50 3.02s p95 4.00s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.487, engine 2.712, mps 0.001, vllm_main 0.000; total 3.200; pod cgroup 3.228

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 124.8 | 200.6 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 115.9 | 192.8 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 5.0 | 22.5 | - | - |
| 2-4 video load_bytes total | 1.00 | 96.4 | 167.7 | 37.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.6 | 78.1 | 1.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 84.2 | 149.6 | 33.5 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 2.6 | 0.7 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.3 | 8.6 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.3 | 3.0 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.2 | 2.5 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 660.8 | 1324.4 | - | - |
| 5-6 processor (mm thread) | 1.00 | 333.8 | 373.0 | 335.8 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 294.0 | 332.9 | 295.3 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 257.5 | 283.4 | 254.9 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 5.0 | 7.5 | 4.9 | - |
| hash (blake3) | 2.00 | 0.5 | 0.7 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.9 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.56 | 193.5 | 279.6 | 170.8 | 193.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.2 | 62.5 | 51.8 | 50.3 |
| 7a sound encoder (per call) | 1.00 | 35.3 | 44.8 | 35.6 | 35.2 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 36892800}
  encoder calls: 9, items/call mean 3.6 max 6; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 735.9 / 859.1 | decode 4892.0 / 6631.2 | e2e(server) 6594.4 / 7736.9 | frontend+IPC 1118.2 / 1844.5
  tokens: prompt 8537, generated 363.6, cached prompt tokens mean 4016 (max 4016), time/output token 12.8 ms
  API-server spread: 3 processes, requests per process [7, 6, 3]
  client latency p50 6.60s p95 7.75s (16 ok), throughput per run 1.0, 1.2 req/s
  server CPU per request (cpu-s): api 0.454, engine 0.878, mps 0.001, vllm_main 0.000; total 1.333; pod cgroup 1.356

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 119.0 | 188.5 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 112.2 | 187.5 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 7.9 | 21.6 | - | - |
| 2-4 video load_bytes total | 1.00 | 102.6 | 170.4 | 39.1 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 3.6 | 84.3 | 1.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 88.3 | 152.0 | 34.9 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 2.5 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 635.3 | 996.7 | - | - |
| 5-6 processor (mm thread) | 1.00 | 331.6 | 379.8 | 332.8 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 292.1 | 338.4 | 292.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 261.3 | 311.7 | 260.6 | - |
| hash (blake3) | 1.00 | 0.8 | 1.1 | 0.7 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.56 | 86.6 | 128.8 | 85.0 | 86.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.56 | 73.2 | 107.2 | 71.9 | 71.6 |
  video_resize_norm: {'in': [1, 28, 3, 480, 854], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 480, 854, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 34433280}
  encoder calls: 9, items/call mean 1.8 max 3; vision calls 9, videos/call mean 1.8 max 3
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 509.5 / 570.5 | decode 3693.4 / 5715.1 | e2e(server) 5081.2 / 7179.9 | frontend+IPC 879.5 / 1388.9
  tokens: prompt 8334, generated 329.1, cached prompt tokens mean 4016 (max 4016), time/output token 12.4 ms
  API-server spread: 3 processes, requests per process [6, 6, 4]
  client latency p50 5.09s p95 7.19s (16 ok), throughput per run 1.1, 1.5 req/s
  server CPU per request (cpu-s): api 0.444, engine 0.763, mps 0.000, vllm_main 0.000; total 1.207; pod cgroup 1.230

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 802.5 | 962.1 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 569.2 | 956.6 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 11.6 | 39.1 | - | - |
| 2-4 video load_bytes total | 1.00 | 334.0 | 469.0 | 40.7 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 101.8 | 257.4 | 1.1 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 168.9 | 315.3 | 36.3 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 4.3 | 0.8 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 196.6 | 590.4 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 2.1 | 8.1 | 1.5 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.9 | 7.8 | 1.4 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 3747.1 | 7508.0 | - | - |
| 5-6 processor (mm thread) | 1.00 | 366.9 | 429.7 | 366.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 320.8 | 378.4 | 322.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 277.9 | 331.3 | 282.0 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.93 | 4.6 | 7.8 | 4.5 | - |
| hash (blake3) | 2.00 | 0.5 | 1.2 | 0.5 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 1.3 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.18 | 577.7 | 870.2 | 530.1 | 577.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.8 | 55.8 | 51.5 | 50.9 |
| 7a sound encoder (per call) | 0.99 | 35.1 | 40.2 | 35.3 | 35.1 |
  video_resize_norm: {'in': [1, 28, 3, 480, 854], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 480, 854, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 34433280}
  encoder calls: 23, items/call mean 11.1 max 20; vision calls 128, videos/call mean 1.0 max 1; sound calls 127, clips/call mean 1.0 max 2
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 2647.3 / 4053.7 | decode 17435.6 / 22704.8 | e2e(server) 25164.3 / 26863.0 | frontend+IPC 4790.0 / 9541.7
  tokens: prompt 8600, generated 345.6, cached prompt tokens mean 4016 (max 4016), time/output token 48.9 ms
  API-server spread: 3 processes, requests per process [45, 42, 41]
  client latency p50 25.19s p95 26.88s (128 ok), throughput per run 2.3, 2.4 req/s
  server CPU per request (cpu-s): api 0.452, engine 0.440, mps 0.000, vllm_main 0.000; total 0.892; pod cgroup 0.903

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 583.9 | 1158.0 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 577.2 | 1154.8 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 39.8 | 1015.0 | - | - |
| 2-4 video load_bytes total | 1.00 | 329.8 | 504.0 | 54.4 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 96.4 | 264.3 | 1.3 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 182.3 | 314.8 | 49.9 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 1.6 | 0.7 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 3462.0 | 6625.7 | - | - |
| 5-6 processor (mm thread) | 1.00 | 355.7 | 405.4 | 353.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 313.9 | 355.2 | 310.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 274.4 | 322.6 | 278.1 | - |
| hash (blake3) | 1.00 | 0.8 | 1.2 | 0.7 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.41 | 121.8 | 133.7 | 107.7 | 121.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.41 | 99.4 | 109.6 | 88.8 | 96.8 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 36892800}
  encoder calls: 53, items/call mean 2.4 max 3; vision calls 53, videos/call mean 2.4 max 3
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 622.6 / 694.9 | decode 14454.1 / 19563.2 | e2e(server) 19088.9 / 21943.3 | frontend+IPC 4174.6 / 7889.0
  tokens: prompt 8395, generated 302.8, cached prompt tokens mean 4016 (max 4016), time/output token 48.6 ms
  API-server spread: 3 processes, requests per process [46, 41, 41]
  client latency p50 19.10s p95 21.98s (128 ok), throughput per run 3.0, 2.8 req/s
  server CPU per request (cpu-s): api 0.451, engine 0.370, mps 0.000, vllm_main 0.000; total 0.822; pod cgroup 0.851

# vod-480p-nvdec-asc12


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 85.8 | 90.9 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 79.5 | 86.6 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.6 | 5.5 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 74.4 | 80.4 | 31.0 | 33.3 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.0 | 4.6 | 1.9 | 4.1 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 67.8 | 73.7 | 26.3 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 0.8 | 0.8 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.9 | 5.4 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.0 | 1.5 | 1.1 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.9 | 1.3 | 0.9 | 1.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 361.3 | 426.6 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 360.5 | 426.2 | 369.5 | 369.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 320.2 | 386.4 | 328.7 | 329.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 274.6 | 328.0 | 282.3 | 282.6 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.96 | 4.6 | 6.6 | 4.9 | 4.9 | - |
| hash (blake3) | 2.00 | 0.4 | 0.6 | 0.4 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 0.7 | 0.6 | 0.6 | - |
| 7 encoder call (all items in the step) | 1.00 | 105.3 | 114.3 | 106.0 | - | 104.9 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 56.0 | 59.9 | 56.3 | - | 55.1 |
| 7a sound encoder (per call) | 1.00 | 40.3 | 46.4 | 40.6 | - | 40.2 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 36892800}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 242.7 / 260.0 | decode 2549.1 / 2965.4 | e2e(server) 3286.4 / 3709.7 | frontend+IPC 501.8 / 567.7
  tokens: prompt 8705, generated 333.8, cached prompt tokens mean 4016 (max 4016), time/output token 7.7 ms
  API-server spread: 5 processes, requests per process [11, 8, 2, 2, 1]
  client latency p50 3.29s p95 3.72s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.569, engine 2.905, mps 0.001, vllm_main 0.000; total 3.475; pod cgroup 3.665

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 74.6 | 80.5 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 73.2 | 79.0 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 3.6 | 5.3 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 68.3 | 74.6 | 29.5 | 31.8 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.0 | 4.9 | 2.0 | 4.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 61.0 | 66.9 | 24.6 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 0.8 | 0.8 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 353.2 | 404.9 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 352.8 | 404.5 | 360.3 | 360.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 314.1 | 364.6 | 320.5 | 320.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 274.2 | 320.0 | 280.2 | 280.5 | - |
| hash (blake3) | 1.00 | 0.6 | 0.8 | 0.6 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 64.5 | 69.2 | 65.1 | - | 64.4 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 55.9 | 59.6 | 56.2 | - | 55.0 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 36892800}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 192.9 / 201.8 | decode 2498.0 / 3213.5 | e2e(server) 3223.0 / 3859.6 | frontend+IPC 477.9 / 530.5
  tokens: prompt 8521, generated 331.4, cached prompt tokens mean 4016 (max 4016), time/output token 7.7 ms
  API-server spread: 4 processes, requests per process [14, 7, 2, 1]
  client latency p50 3.23s p95 3.86s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.560, engine 2.832, mps 0.002, vllm_main 0.000; total 3.395; pod cgroup 3.490

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 119.7 | 147.8 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 112.1 | 133.6 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 5.0 | 12.0 | - | - |
| 2-4 video load_bytes total | 1.00 | 100.4 | 124.8 | 46.0 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.1 | 4.5 | 1.8 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 93.1 | 116.7 | 41.2 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 1.4 | 0.9 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.5 | 12.2 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.3 | 3.6 | 1.3 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.1 | 3.3 | 1.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 430.4 | 799.2 | - | - |
| 5-6 processor (mm thread) | 1.00 | 428.1 | 488.2 | 421.0 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 379.8 | 437.4 | 374.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 334.0 | 381.3 | 327.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 4.8 | 6.3 | 4.8 | - |
| hash (blake3) | 2.00 | 0.4 | 0.7 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 0.9 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.38 | 114.0 | 620.5 | 269.2 | 112.4 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 53.7 | 60.1 | 53.5 | 52.9 |
| 7a sound encoder (per call) | 1.00 | 38.6 | 45.2 | 38.8 | 38.6 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 36892800}
  encoder calls: 6, items/call mean 5.3 max 12; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 1217.4 / 1271.2 | decode 4680.8 / 5564.4 | e2e(server) 6758.5 / 7437.6 | frontend+IPC 854.6 / 1877.5
  tokens: prompt 8537, generated 359.6, cached prompt tokens mean 4016 (max 4016), time/output token 13.1 ms
  API-server spread: 10 processes, requests per process [3, 3, 2, 2, 1, 1, 1, 1, 1, 1]
  client latency p50 6.77s p95 7.45s (16 ok), throughput per run 1.1, 1.2 req/s
  server CPU per request (cpu-s): api 0.603, engine 0.865, mps 0.000, vllm_main 0.000; total 1.468; pod cgroup 1.510

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 123.4 | 183.3 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 121.5 | 182.3 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 9.0 | 23.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 107.0 | 156.7 | 42.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.4 | 78.4 | 1.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 95.1 | 111.9 | 37.6 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 1.5 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 399.8 | 1176.1 | - | - |
| 5-6 processor (mm thread) | 1.00 | 362.8 | 475.3 | 371.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 326.2 | 425.3 | 331.4 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 300.1 | 381.4 | 301.7 | - |
| hash (blake3) | 1.00 | 0.6 | 1.1 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.44 | 76.5 | 254.4 | 111.3 | 76.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.44 | 68.3 | 211.0 | 94.5 | 67.5 |
  video_resize_norm: {'in': [1, 28, 3, 480, 854], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 480, 854, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 34433280}
  encoder calls: 7, items/call mean 2.3 max 6; vision calls 7, videos/call mean 2.3 max 6
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 658.1 / 787.1 | decode 3974.8 / 5683.3 | e2e(server) 5151.9 / 7046.6 | frontend+IPC 765.5 / 1409.5
  tokens: prompt 8334, generated 319.8, cached prompt tokens mean 4016 (max 4016), time/output token 12.5 ms
  API-server spread: 9 processes, requests per process [5, 2, 2, 2, 1, 1, 1, 1, 1]
  client latency p50 5.16s p95 7.05s (16 ok), throughput per run 1.1, 1.4 req/s
  server CPU per request (cpu-s): api 0.525, engine 0.766, mps 0.002, vllm_main 0.000; total 1.293; pod cgroup 1.329

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 453.6 | 2208.4 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 447.2 | 2204.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 4.2 | 1064.8 | - | - |
| 2-4 video load_bytes total | 1.00 | 258.2 | 570.3 | 61.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 5.0 | 237.5 | 1.6 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 206.4 | 388.6 | 56.0 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 2.4 | 1.2 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.3 | 9.5 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.4 | 4.1 | 1.3 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.2 | 3.9 | 1.2 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 1079.9 | 2106.6 | - | - |
| 5-6 processor (mm thread) | 1.00 | 441.2 | 513.5 | 443.1 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 392.0 | 465.5 | 392.3 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 344.1 | 402.9 | 344.5 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.91 | 5.1 | 6.9 | 4.8 | - |
| hash (blake3) | 2.00 | 0.5 | 0.9 | 0.4 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 1.5 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.14 | 779.4 | 1180.0 | 732.3 | 733.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 54.3 | 62.9 | 54.6 | 53.4 |
| 7a sound encoder (per call) | 1.00 | 38.9 | 47.6 | 39.4 | 38.9 |
  video_resize_norm: {'in': [1, 28, 3, 480, 854], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 480, 854, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 34433280}
  encoder calls: 18, items/call mean 14.2 max 22; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 5213.3 / 7992.1 | decode 19466.0 / 24188.2 | e2e(server) 26788.7 / 29381.3 | frontend+IPC 2090.8 / 4058.3
  tokens: prompt 8600, generated 350.4, cached prompt tokens mean 4016 (max 4016), time/output token 54.3 ms
  API-server spread: 12 processes, requests per process [16, 13, 12, 11, 11, 11, 10, 10, 9, 9, 8, 8]
  client latency p50 26.80s p95 29.39s (128 ok), throughput per run 2.1, 2.3 req/s
  server CPU per request (cpu-s): api 0.580, engine 0.480, mps 0.000, vllm_main 0.000; total 1.061; pod cgroup 1.134

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 426.1 | 2212.3 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 423.8 | 2210.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 17.8 | 2091.3 | - | - |
| 2-4 video load_bytes total | 1.00 | 232.6 | 433.2 | 75.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.9 | 221.1 | 1.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 197.0 | 360.9 | 70.1 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.8 | 1.5 | 1.2 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 946.5 | 1958.0 | - | - |
| 5-6 processor (mm thread) | 1.00 | 428.4 | 504.4 | 423.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 379.9 | 446.4 | 375.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 340.4 | 398.1 | 339.7 | - |
| hash (blake3) | 1.00 | 0.8 | 1.1 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.17 | 306.1 | 426.0 | 244.6 | 247.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.17 | 249.4 | 351.4 | 200.8 | 196.1 |
  video_resize_norm: {'in': [1, 30, 3, 480, 854], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 480, 854, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 36892800}
  encoder calls: 22, items/call mean 5.8 max 11; vision calls 22, videos/call mean 5.8 max 11
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 2488.3 / 4224.4 | decode 14626.9 / 18582.8 | e2e(server) 19365.5 / 21805.2 | frontend+IPC 2066.9 / 3556.5
  tokens: prompt 8395, generated 309.2, cached prompt tokens mean 4016 (max 4016), time/output token 48.1 ms
  API-server spread: 12 processes, requests per process [16, 13, 13, 13, 13, 11, 10, 9, 8, 8, 8, 6]
  client latency p50 19.37s p95 21.81s (128 ok), throughput per run 3.0, 2.8 req/s
  server CPU per request (cpu-s): api 0.567, engine 0.374, mps 0.000, vllm_main 0.000; total 0.941; pod cgroup 0.976

# vod-720p-prod


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 227.9 | 411.2 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 223.0 | 406.9 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 3.9 | 9.4 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 202.5 | 309.7 | 67.0 | 1583.9 | - |
| 3a OpenCV open | 1.00 | 11.0 | 16.8 | 11.1 | 12.6 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 185.1 | 212.3 | 54.1 | 1557.8 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.7 | 4.7 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 1.4 | 1.1 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.9 | 1.1 | 0.9 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 409.8 | 446.9 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 409.3 | 446.5 | 410.7 | 411.0 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 369.0 | 401.3 | 369.4 | 369.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 290.3 | 315.1 | 289.4 | 289.6 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.83 | 4.9 | 6.6 | 4.8 | 4.8 | - |
| hash (blake3) | 2.00 | 0.7 | 1.2 | 0.6 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.7 | 0.6 | 0.6 | - |
| 7 encoder call (all items in the step) | 1.00 | 97.4 | 109.5 | 97.8 | - | 97.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.5 | 59.5 | 52.2 | - | 50.6 |
| 7a sound encoder (per call) | 1.00 | 36.9 | 43.8 | 36.6 | - | 36.3 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 226.0 / 239.1 | decode 2360.0 / 2864.6 | e2e(server) 3243.0 / 3845.4 | frontend+IPC 690.3 / 870.1
  tokens: prompt 8705, generated 342.2, cached prompt tokens mean 4016 (max 4016), time/output token 7.1 ms
  API-server spread: 3 processes, requests per process [16, 5, 3]
  client latency p50 3.33s p95 4.99s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 2.124, engine 2.748, vllm_main 0.000; total 4.872; pod cgroup 6.122

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 193.5 | 264.6 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 192.5 | 263.6 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.3 | 10.0 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 186.7 | 258.3 | 64.5 | 1480.7 | - |
| 3a OpenCV open | 1.00 | 11.3 | 15.9 | 10.2 | 12.0 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 173.6 | 236.2 | 52.5 | 1453.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 413.5 | 443.2 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 412.9 | 442.8 | 407.7 | 408.0 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 370.0 | 397.8 | 367.2 | 367.5 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 290.8 | 313.2 | 290.0 | 290.2 | - |
| hash (blake3) | 1.00 | 1.1 | 1.3 | 1.1 | 1.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 59.6 | 62.3 | 59.4 | - | 59.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 50.8 | 54.1 | 51.1 | - | 50.0 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'opencv'}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 173.8 / 190.4 | decode 2286.6 / 3480.9 | e2e(server) 3119.0 / 4272.9 | frontend+IPC 661.1 / 732.5
  tokens: prompt 8521, generated 342.8, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 3 processes, requests per process [10, 9, 5]
  client latency p50 3.12s p95 4.28s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 2.013, engine 2.681, vllm_main 0.000; total 4.694; pod cgroup 4.994

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 515.9 | 570.8 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 509.6 | 565.3 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 7.5 | 25.3 | - | - |
| 2-4 video load_bytes total | 1.00 | 486.5 | 546.6 | 86.1 | - |
| 3a OpenCV open | 1.00 | 19.7 | 47.8 | 12.8 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 454.2 | 523.2 | 70.8 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.6 | 43.4 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.4 | 40.8 | 1.4 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.2 | 40.6 | 1.2 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 812.3 | 1246.0 | - | - |
| 5-6 processor (mm thread) | 1.00 | 412.0 | 448.9 | 409.6 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 369.4 | 407.3 | 368.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 285.7 | 310.4 | 285.2 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 5.0 | 11.6 | 5.0 | - |
| hash (blake3) | 2.00 | 1.1 | 1.7 | 0.8 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 1.6 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.50 | 190.1 | 281.1 | 187.7 | 189.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.2 | 55.6 | 50.4 | 50.3 |
| 7a sound encoder (per call) | 1.00 | 35.0 | 39.2 | 34.9 | 34.9 |
  video_resize_norm: {'in': [1, 28, 3, 720, 1280], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 8, items/call mean 4.0 max 6; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 856.4 / 870.0 | decode 4828.8 / 5697.7 | e2e(server) 6862.3 / 8047.5 | frontend+IPC 1482.3 / 2048.9
  tokens: prompt 8537, generated 372.2, cached prompt tokens mean 4016 (max 4016), time/output token 12.3 ms
  API-server spread: 3 processes, requests per process [6, 5, 5]
  client latency p50 6.87s p95 8.06s (16 ok), throughput per run 1.0, 1.1 req/s
  server CPU per request (cpu-s): api 2.499, engine 0.868, vllm_main 0.000; total 3.367; pod cgroup 3.405

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 549.8 | 572.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 548.7 | 572.0 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 10.5 | 18.6 | - | - |
| 2-4 video load_bytes total | 1.00 | 536.3 | 557.2 | 83.1 | - |
| 3a OpenCV open | 1.00 | 15.7 | 36.5 | 9.4 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 514.9 | 530.8 | 71.3 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 790.8 | 1642.3 | - | - |
| 5-6 processor (mm thread) | 1.00 | 402.1 | 457.6 | 403.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 359.3 | 411.8 | 362.2 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 284.2 | 326.3 | 285.9 | - |
| hash (blake3) | 1.00 | 1.3 | 4.6 | 1.3 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.5 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.69 | 68.3 | 91.1 | 73.2 | 68.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.69 | 60.5 | 77.2 | 62.4 | 59.8 |
  video_resize_norm: {'in': [1, 28, 3, 720, 1280], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 720, 1280, 3], 'backend': 'opencv'}
  encoder calls: 11, items/call mean 1.5 max 2; vision calls 11, videos/call mean 1.5 max 2
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 423.7 / 484.9 | decode 4130.7 / 4891.9 | e2e(server) 5855.4 / 6714.7 | frontend+IPC 1405.2 / 2276.4
  tokens: prompt 8334, generated 320.8, cached prompt tokens mean 4016 (max 4016), time/output token 12.6 ms
  API-server spread: 3 processes, requests per process [7, 5, 4]
  client latency p50 5.86s p95 6.72s (16 ok), throughput per run 1.2, 1.2 req/s
  server CPU per request (cpu-s): api 2.651, engine 0.749, vllm_main 0.000; total 3.401; pod cgroup 3.425

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 4793.1 | 5563.8 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 3997.7 | 5550.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 49.6 | 204.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 1930.2 | 2380.4 | 159.5 | - |
| 3a OpenCV open | 1.00 | 94.2 | 250.8 | 15.4 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 1806.8 | 2206.7 | 139.7 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 604.6 | 2693.7 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 14.6 | 95.6 | 2.5 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 11.9 | 93.9 | 2.2 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 4947.1 | 8725.2 | - | - |
| 5-6 processor (mm thread) | 1.00 | 426.0 | 507.5 | 426.5 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 382.1 | 454.4 | 383.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 296.6 | 349.4 | 297.2 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.95 | 4.7 | 15.9 | 4.8 | - |
| hash (blake3) | 2.00 | 1.2 | 2.0 | 0.8 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 1.0 | 1.5 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.23 | 474.3 | 658.9 | 416.0 | 474.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.0 | 55.8 | 50.7 | 50.2 |
| 7a sound encoder (per call) | 1.00 | 34.9 | 40.3 | 35.0 | 34.8 |
  video_resize_norm: {'in': [1, 28, 3, 720, 1280], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 720, 1280, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 29, items/call mean 8.8 max 16; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 1802.2 / 3224.2 | decode 18446.1 / 23360.2 | e2e(server) 30221.6 / 32823.5 | frontend+IPC 10444.4 / 15057.2
  tokens: prompt 8600, generated 358.0, cached prompt tokens mean 4016 (max 4016), time/output token 49.8 ms
  API-server spread: 3 processes, requests per process [45, 42, 41]
  client latency p50 30.25s p95 32.83s (128 ok), throughput per run 1.9, 1.9 req/s
  server CPU per request (cpu-s): api 3.156, engine 0.467, vllm_main 0.000; total 3.623; pod cgroup 3.645

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 4254.5 | 5974.1 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 4250.9 | 5965.5 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 62.1 | 502.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 2102.1 | 2402.8 | 168.2 | - |
| 3a OpenCV open | 1.00 | 95.9 | 201.9 | 15.0 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 1965.5 | 2276.8 | 148.7 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 5877.5 | 8222.2 | - | - |
| 5-6 processor (mm thread) | 1.00 | 423.9 | 1471.8 | 438.5 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 379.9 | 1384.6 | 394.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 298.4 | 1081.9 | 309.7 | - |
| hash (blake3) | 1.00 | 1.9 | 5.6 | 2.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 1.2 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.56 | 89.2 | 130.4 | 85.9 | 88.9 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.56 | 75.3 | 107.2 | 72.5 | 73.5 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'opencv'}
  encoder calls: 72, items/call mean 1.8 max 3; vision calls 72, videos/call mean 1.8 max 3
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 491.7 / 621.7 | decode 15048.4 / 20648.9 | e2e(server) 25748.9 / 28298.8 | frontend+IPC 10112.7 / 14188.3
  tokens: prompt 8395, generated 314.0, cached prompt tokens mean 4016 (max 4016), time/output token 49.3 ms
  API-server spread: 3 processes, requests per process [44, 42, 42]
  client latency p50 25.80s p95 28.32s (128 ok), throughput per run 2.3, 2.2 req/s
  server CPU per request (cpu-s): api 3.299, engine 0.392, vllm_main 0.000; total 3.691; pod cgroup 3.743

# vod-720p-nvdec


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 127.6 | 134.1 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 122.2 | 129.3 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 3.4 | 8.8 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 116.7 | 120.5 | 32.1 | 34.8 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.8 | 5.6 | 2.1 | 4.7 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 107.8 | 111.2 | 25.6 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 1.7 | 1.6 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.0 | 4.4 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.0 | 1.4 | 1.1 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.9 | 1.2 | 0.9 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 384.1 | 398.6 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 383.9 | 398.1 | 383.5 | 383.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 346.2 | 361.4 | 344.5 | 344.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 270.2 | 289.8 | 270.9 | 271.2 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.67 | 4.2 | 4.5 | 4.2 | 4.2 | - |
| hash (blake3) | 2.00 | 0.7 | 1.0 | 0.5 | 0.5 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.6 | 0.5 | 0.5 | - |
| 7 encoder call (all items in the step) | 1.00 | 94.1 | 99.6 | 94.1 | - | 93.8 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.0 | 52.5 | 50.9 | - | 50.2 |
| 7a sound encoder (per call) | 1.00 | 34.3 | 36.9 | 34.6 | - | 34.1 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 82944000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 218.4 / 229.0 | decode 2380.1 / 2806.8 | e2e(server) 3157.1 / 3596.6 | frontend+IPC 559.3 / 583.5
  tokens: prompt 8705, generated 334.2, cached prompt tokens mean 4016 (max 4016), time/output token 7.2 ms
  API-server spread: 3 processes, requests per process [12, 11, 1]
  client latency p50 3.16s p95 3.60s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.547, engine 2.716, mps 0.002, vllm_main 0.000; total 3.265; pod cgroup 3.285

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 109.5 | 122.4 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 107.4 | 121.5 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.1 | 6.0 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 102.6 | 116.5 | 30.0 | 32.5 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.5 | 5.1 | 2.1 | 4.5 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 94.5 | 107.4 | 23.5 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 1.6 | 1.6 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 377.1 | 390.6 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 376.5 | 390.2 | 375.9 | 376.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 339.1 | 353.2 | 338.3 | 338.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 269.6 | 284.5 | 268.7 | 269.0 | - |
| hash (blake3) | 1.00 | 0.9 | 1.0 | 0.9 | 0.9 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 59.3 | 62.8 | 59.7 | - | 59.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 50.9 | 54.4 | 51.4 | - | 50.0 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 82944000}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 172.5 / 181.8 | decode 2260.1 / 2961.2 | e2e(server) 2979.4 / 3679.4 | frontend+IPC 534.3 / 556.1
  tokens: prompt 8521, generated 326.6, cached prompt tokens mean 4016 (max 4016), time/output token 7.2 ms
  API-server spread: 3 processes, requests per process [13, 10, 1]
  client latency p50 2.98s p95 3.68s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.531, engine 2.617, mps 0.002, vllm_main 0.000; total 3.150; pod cgroup 3.168

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 171.2 | 282.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 163.1 | 276.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 7.1 | 26.5 | - | - |
| 2-4 video load_bytes total | 1.00 | 140.1 | 257.9 | 42.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.1 | 4.8 | 1.5 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 125.5 | 237.0 | 36.1 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 2.9 | 2.0 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.8 | 6.4 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 2.7 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.9 | 2.3 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 757.9 | 1392.3 | - | - |
| 5-6 processor (mm thread) | 1.00 | 385.9 | 417.6 | 384.8 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 346.8 | 378.4 | 346.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 273.8 | 291.3 | 270.8 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 4.5 | 6.2 | 4.1 | - |
| hash (blake3) | 2.00 | 0.8 | 1.7 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 1.4 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.50 | 189.5 | 286.2 | 188.8 | 187.9 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 50.6 | 58.7 | 51.1 | 49.8 |
| 7a sound encoder (per call) | 1.00 | 35.2 | 40.1 | 34.9 | 34.9 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 82944000}
  encoder calls: 8, items/call mean 4.0 max 6; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 843.6 / 891.3 | decode 4699.3 / 5630.7 | e2e(server) 6522.0 / 7213.0 | frontend+IPC 1192.1 / 1745.3
  tokens: prompt 8537, generated 361.6, cached prompt tokens mean 4016 (max 4016), time/output token 12.5 ms
  API-server spread: 3 processes, requests per process [7, 5, 4]
  client latency p50 6.53s p95 7.22s (16 ok), throughput per run 1.1, 1.2 req/s
  server CPU per request (cpu-s): api 0.506, engine 0.845, mps 0.001, vllm_main 0.000; total 1.352; pod cgroup 1.375

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 158.9 | 257.6 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 152.4 | 256.4 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 11.6 | 25.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 140.5 | 241.1 | 41.5 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.0 | 117.2 | 1.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 122.0 | 219.4 | 34.9 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 2.4 | 6.5 | 2.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 721.8 | 1139.6 | - | - |
| 5-6 processor (mm thread) | 1.00 | 368.0 | 419.1 | 378.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 331.5 | 376.1 | 341.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 262.8 | 309.0 | 272.2 | - |
| hash (blake3) | 1.00 | 1.0 | 1.2 | 1.0 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.4 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.56 | 89.7 | 118.8 | 85.2 | 89.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.56 | 74.8 | 98.6 | 72.1 | 73.2 |
  video_resize_norm: {'in': [1, 28, 3, 720, 1280], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 77414400}
  encoder calls: 9, items/call mean 1.8 max 3; vision calls 9, videos/call mean 1.8 max 3
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 446.7 / 571.5 | decode 3971.8 / 5711.5 | e2e(server) 5308.0 / 7025.3 | frontend+IPC 1004.1 / 1444.8
  tokens: prompt 8334, generated 319.1, cached prompt tokens mean 4016 (max 4016), time/output token 12.5 ms
  API-server spread: 3 processes, requests per process [6, 6, 4]
  client latency p50 5.31s p95 7.03s (16 ok), throughput per run 1.1, 1.4 req/s
  server CPU per request (cpu-s): api 0.493, engine 0.773, mps 0.000, vllm_main 0.000; total 1.266; pod cgroup 1.288

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1137.0 | 1477.8 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 809.1 | 1456.6 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 17.7 | 55.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 490.5 | 745.2 | 47.4 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 140.1 | 380.0 | 1.3 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 256.6 | 504.6 | 40.6 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 4.6 | 2.0 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 269.0 | 919.8 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.5 | 7.7 | 1.2 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.4 | 6.8 | 1.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 4442.4 | 7899.7 | - | - |
| 5-6 processor (mm thread) | 1.00 | 394.6 | 436.1 | 393.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 353.4 | 391.3 | 353.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 277.4 | 303.8 | 278.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.94 | 4.4 | 7.3 | 4.2 | - |
| hash (blake3) | 2.00 | 0.6 | 1.3 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.9 | 1.3 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.21 | 472.8 | 677.4 | 443.9 | 472.8 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.0 | 54.2 | 50.6 | 50.2 |
| 7a sound encoder (per call) | 1.00 | 34.2 | 40.0 | 34.6 | 34.2 |
  video_resize_norm: {'in': [1, 28, 3, 720, 1280], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 77414400}
  encoder calls: 27, items/call mean 9.5 max 16; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 2053.6 / 3385.0 | decode 17740.4 / 23492.7 | e2e(server) 25801.3 / 27637.4 | frontend+IPC 5739.1 / 9956.2
  tokens: prompt 8600, generated 352.0, cached prompt tokens mean 4016 (max 4016), time/output token 49.4 ms
  API-server spread: 3 processes, requests per process [45, 42, 41]
  client latency p50 25.81s p95 27.64s (128 ok), throughput per run 2.2, 2.2 req/s
  server CPU per request (cpu-s): api 0.488, engine 0.462, mps 0.000, vllm_main 0.000; total 0.951; pod cgroup 0.958

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 846.6 | 1516.6 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 840.1 | 1508.8 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 48.9 | 88.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 484.2 | 777.7 | 65.7 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 184.9 | 379.2 | 1.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 265.9 | 453.2 | 59.2 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 3.0 | 1.7 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 3629.7 | 6596.3 | - | - |
| 5-6 processor (mm thread) | 1.00 | 379.2 | 428.6 | 379.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 340.8 | 381.6 | 342.3 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 269.9 | 303.0 | 272.0 | - |
| hash (blake3) | 1.00 | 0.9 | 1.2 | 0.9 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.48 | 90.8 | 127.3 | 94.2 | 90.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.48 | 76.7 | 106.4 | 79.4 | 74.9 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 82944000}
  encoder calls: 62, items/call mean 2.1 max 3; vision calls 62, videos/call mean 2.1 max 3
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 524.8 / 669.5 | decode 14711.5 / 20317.2 | e2e(server) 19804.0 / 22690.6 | frontend+IPC 4707.0 / 8283.0
  tokens: prompt 8395, generated 309.8, cached prompt tokens mean 4016 (max 4016), time/output token 47.6 ms
  API-server spread: 3 processes, requests per process [45, 43, 40]
  client latency p50 19.81s p95 22.73s (128 ok), throughput per run 2.9, 2.7 req/s
  server CPU per request (cpu-s): api 0.490, engine 0.379, mps 0.000, vllm_main 0.000; total 0.869; pod cgroup 0.876

# vod-720p-nvdec-asc12


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 128.1 | 134.3 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 122.8 | 127.9 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 3.7 | 7.9 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 116.9 | 120.6 | 34.1 | 37.0 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.8 | 6.2 | 2.2 | 4.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 107.6 | 110.4 | 27.4 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 1.6 | 1.6 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.9 | 4.7 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 1.3 | 1.1 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.9 | 1.2 | 0.9 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 437.3 | 499.5 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 437.0 | 499.2 | 437.3 | 437.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 397.0 | 453.2 | 394.5 | 395.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 313.6 | 367.0 | 312.5 | 312.9 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.96 | 4.4 | 4.8 | 4.3 | 4.4 | - |
| hash (blake3) | 2.00 | 0.7 | 1.1 | 0.6 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.6 | 0.5 | 0.5 | - |
| 7 encoder call (all items in the step) | 1.00 | 101.4 | 110.9 | 101.4 | - | 101.1 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 52.3 | 56.0 | 52.8 | - | 51.5 |
| 7a sound encoder (per call) | 1.00 | 36.1 | 44.0 | 37.1 | - | 35.8 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 82944000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 229.3 / 262.6 | decode 2454.7 / 2744.3 | e2e(server) 3289.4 / 3580.7 | frontend+IPC 613.1 / 682.8
  tokens: prompt 8705, generated 336.2, cached prompt tokens mean 4016 (max 4016), time/output token 7.3 ms
  API-server spread: 7 processes, requests per process [6, 5, 4, 4, 2, 2, 1]
  client latency p50 3.29s p95 3.58s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.643, engine 2.774, mps 0.001, vllm_main 0.000; total 3.418; pod cgroup 3.439

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 111.0 | 126.2 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 109.1 | 124.8 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.6 | 6.0 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 103.5 | 118.6 | 33.9 | 36.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.8 | 5.8 | 2.3 | 4.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 94.6 | 108.6 | 27.1 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 1.7 | 1.6 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 441.6 | 470.0 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 441.2 | 469.5 | 438.5 | 439.0 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 397.4 | 429.0 | 393.2 | 393.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 323.1 | 343.7 | 315.8 | 316.1 | - |
| hash (blake3) | 1.00 | 0.9 | 1.2 | 0.9 | 0.9 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 62.7 | 70.1 | 63.3 | - | 62.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.5 | 59.1 | 52.1 | - | 50.6 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 82944000}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 178.2 / 195.3 | decode 2282.6 / 3327.2 | e2e(server) 3153.2 / 4057.1 | frontend+IPC 602.8 / 657.5
  tokens: prompt 8521, generated 328.5, cached prompt tokens mean 4016 (max 4016), time/output token 7.2 ms
  API-server spread: 5 processes, requests per process [13, 5, 3, 2, 1]
  client latency p50 3.16s p95 4.06s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.637, engine 2.645, mps 0.002, vllm_main 0.000; total 3.283; pod cgroup 3.304

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 159.0 | 1159.0 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 153.6 | 1154.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 5.7 | 1042.0 | - | - |
| 2-4 video load_bytes total | 1.00 | 140.2 | 154.4 | 44.7 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.7 | 6.0 | 2.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 129.7 | 145.3 | 37.8 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 1.8 | 1.6 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.8 | 5.4 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.0 | 2.0 | 1.0 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.8 | 1.9 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 453.3 | 863.9 | - | - |
| 5-6 processor (mm thread) | 1.00 | 447.4 | 477.2 | 438.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 405.2 | 432.7 | 397.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 328.8 | 351.5 | 318.1 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 4.1 | 6.3 | 4.3 | - |
| hash (blake3) | 2.00 | 0.6 | 1.2 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 1.1 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.44 | 136.5 | 559.9 | 220.6 | 136.4 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 50.7 | 64.7 | 50.9 | 49.7 |
| 7a sound encoder (per call) | 1.00 | 34.1 | 59.6 | 34.5 | 33.8 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 82944000}
  encoder calls: 7, items/call mean 4.6 max 12; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 1026.1 / 1227.9 | decode 4315.4 / 5429.6 | e2e(server) 6429.9 / 7074.0 | frontend+IPC 979.1 / 1922.5
  tokens: prompt 8537, generated 361.2, cached prompt tokens mean 4016 (max 4016), time/output token 12.3 ms
  API-server spread: 9 processes, requests per process [3, 3, 2, 2, 2, 1, 1, 1, 1]
  client latency p50 6.44s p95 7.08s (16 ok), throughput per run 1.1, 1.2 req/s
  server CPU per request (cpu-s): api 0.606, engine 0.829, mps 0.000, vllm_main 0.000; total 1.435; pod cgroup 1.454

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 155.0 | 172.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 153.7 | 165.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 9.2 | 21.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 145.1 | 151.7 | 48.4 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.5 | 5.5 | 1.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 133.9 | 136.7 | 41.4 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.7 | 4.2 | 2.2 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 456.7 | 965.0 | - | - |
| 5-6 processor (mm thread) | 1.00 | 446.8 | 503.7 | 447.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 402.8 | 458.3 | 406.4 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 328.0 | 374.6 | 330.5 | - |
| hash (blake3) | 1.00 | 0.9 | 1.0 | 0.9 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.4 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.38 | 122.9 | 264.0 | 128.1 | 106.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.38 | 98.6 | 204.7 | 102.7 | 86.9 |
  video_resize_norm: {'in': [1, 28, 3, 720, 1280], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 77414400}
  encoder calls: 6, items/call mean 2.7 max 6; vision calls 6, videos/call mean 2.7 max 6
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 706.9 / 843.2 | decode 3640.4 / 5365.4 | e2e(server) 5181.8 / 6887.4 | frontend+IPC 885.8 / 1478.3
  tokens: prompt 8334, generated 328.7, cached prompt tokens mean 4016 (max 4016), time/output token 12.1 ms
  API-server spread: 9 processes, requests per process [3, 3, 3, 2, 1, 1, 1, 1, 1]
  client latency p50 5.19s p95 6.89s (16 ok), throughput per run 1.2, 1.3 req/s
  server CPU per request (cpu-s): api 0.606, engine 0.774, mps 0.001, vllm_main 0.000; total 1.382; pod cgroup 1.400

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 603.7 | 2353.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 595.4 | 2346.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 6.6 | 2067.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 332.6 | 578.6 | 78.9 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 5.7 | 343.9 | 2.1 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 238.3 | 374.4 | 68.4 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 11.8 | 4.5 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.0 | 9.3 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.2 | 3.5 | 1.2 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.0 | 3.3 | 1.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 1088.0 | 2600.6 | - | - |
| 5-6 processor (mm thread) | 1.00 | 504.7 | 572.0 | 505.6 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 453.4 | 511.9 | 455.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 365.5 | 407.8 | 367.4 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.95 | 4.7 | 6.3 | 4.4 | - |
| hash (blake3) | 2.00 | 0.7 | 1.6 | 0.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.7 | 1.5 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.14 | 786.3 | 1055.0 | 695.9 | 743.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.0 | 62.4 | 51.7 | 50.1 |
| 7a sound encoder (per call) | 0.99 | 34.7 | 43.5 | 35.4 | 34.7 |
  video_resize_norm: {'in': [1, 28, 3, 720, 1280], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 77414400}
  encoder calls: 18, items/call mean 14.2 max 22; vision calls 128, videos/call mean 1.0 max 1; sound calls 127, clips/call mean 1.0 max 2
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 4187.8 / 7578.5 | decode 18181.7 / 22589.1 | e2e(server) 25598.2 / 27222.9 | frontend+IPC 2533.9 / 4401.3
  tokens: prompt 8600, generated 354.5, cached prompt tokens mean 4016 (max 4016), time/output token 51.8 ms
  API-server spread: 12 processes, requests per process [15, 14, 13, 12, 11, 10, 10, 10, 10, 9, 7, 7]
  client latency p50 25.61s p95 27.23s (128 ok), throughput per run 2.3, 2.2 req/s
  server CPU per request (cpu-s): api 0.661, engine 0.471, mps 0.000, vllm_main 0.000; total 1.132; pod cgroup 1.141

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1184.4 | 3329.3 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1182.7 | 3327.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 1008.3 | 3074.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 287.6 | 544.4 | 100.3 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 5.7 | 279.0 | 2.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 232.0 | 438.1 | 91.9 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 1.6 | 3.1 | 2.3 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 991.9 | 2222.5 | - | - |
| 5-6 processor (mm thread) | 1.00 | 489.5 | 547.9 | 490.8 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 441.3 | 490.9 | 443.2 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 359.4 | 401.7 | 360.2 | - |
| hash (blake3) | 1.00 | 1.0 | 1.5 | 1.0 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.4 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.16 | 275.9 | 485.6 | 277.9 | 275.9 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.16 | 205.0 | 374.3 | 213.5 | 199.2 |
  video_resize_norm: {'in': [1, 30, 3, 720, 1280], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 720, 1280, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 82944000}
  encoder calls: 21, items/call mean 6.1 max 11; vision calls 21, videos/call mean 6.1 max 11
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 2763.8 / 3520.8 | decode 13979.4 / 18683.3 | e2e(server) 19038.0 / 22183.3 | frontend+IPC 2667.7 / 4943.4
  tokens: prompt 8395, generated 312.3, cached prompt tokens mean 4016 (max 4016), time/output token 44.7 ms
  API-server spread: 12 processes, requests per process [17, 14, 12, 12, 12, 11, 10, 10, 9, 9, 6, 6]
  client latency p50 19.04s p95 22.19s (128 ok), throughput per run 3.1, 2.8 req/s
  server CPU per request (cpu-s): api 0.660, engine 0.362, mps 0.000, vllm_main 0.000; total 1.023; pod cgroup 1.030

# vod-1080p-prod-cpu32


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 345.6 | 446.5 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 341.3 | 441.1 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 5.4 | 12.8 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 333.1 | 431.9 | 114.3 | 3072.8 | - |
| 3a OpenCV open | 1.00 | 15.4 | 22.2 | 15.6 | 17.5 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 310.2 | 401.8 | 96.8 | 3032.2 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.4 | 4.2 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 1.6 | 1.1 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.9 | 1.3 | 0.9 | 1.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 529.8 | 591.2 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 529.3 | 590.7 | 529.6 | 529.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 489.4 | 546.2 | 489.1 | 489.4 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 321.1 | 354.2 | 323.0 | 323.2 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.88 | 4.3 | 5.5 | 4.6 | 4.6 | - |
| hash (blake3) | 2.00 | 1.3 | 2.0 | 0.9 | 0.9 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.6 | 0.5 | 0.5 | - |
| 7 encoder call (all items in the step) | 1.00 | 92.5 | 97.5 | 92.9 | - | 92.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 50.3 | 51.8 | 50.2 | - | 49.5 |
| 7a sound encoder (per call) | 1.00 | 33.9 | 37.0 | 34.0 | - | 33.9 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 216.8 / 224.3 | decode 2316.0 / 2663.0 | e2e(server) 3515.5 / 3845.4 | frontend+IPC 930.2 / 1053.4
  tokens: prompt 8705, generated 327.4, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 3 processes, requests per process [13, 6, 5]
  client latency p50 3.52s p95 3.85s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 3.729, engine 2.600, vllm_main 0.000; total 6.328; pod cgroup 6.353

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 328.5 | 448.1 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 327.6 | 446.9 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 6.9 | 9.2 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 321.9 | 437.1 | 114.9 | 2930.4 | - |
| 3a OpenCV open | 1.00 | 16.2 | 26.4 | 16.7 | 18.5 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 296.7 | 399.0 | 96.3 | 2877.8 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 506.7 | 537.3 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 506.4 | 536.6 | 509.3 | 509.6 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 469.4 | 498.5 | 470.7 | 471.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 314.6 | 332.9 | 314.6 | 314.9 | - |
| hash (blake3) | 1.00 | 1.6 | 2.2 | 1.6 | 1.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 59.4 | 65.3 | 60.0 | - | 59.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 50.8 | 55.3 | 51.5 | - | 50.0 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'opencv'}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 175.4 / 182.7 | decode 2220.2 / 3189.9 | e2e(server) 3366.9 / 4273.0 | frontend+IPC 899.0 / 1046.5
  tokens: prompt 8521, generated 331.5, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 2 processes, requests per process [12, 12]
  client latency p50 3.37s p95 4.28s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 3.564, engine 2.585, vllm_main 0.001; total 6.150; pod cgroup 6.172

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 967.7 | 1406.5 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 962.8 | 1402.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 7.0 | 44.0 | - | - |
| 2-4 video load_bytes total | 1.00 | 914.6 | 1001.4 | 149.5 | - |
| 3a OpenCV open | 1.00 | 24.4 | 74.1 | 18.0 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 880.1 | 964.4 | 128.8 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.5 | 12.8 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.3 | 2.4 | 1.3 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.1 | 2.2 | 1.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 996.7 | 1883.8 | - | - |
| 5-6 processor (mm thread) | 1.00 | 556.3 | 624.9 | 538.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 512.1 | 577.7 | 496.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 328.8 | 378.2 | 326.7 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 5.1 | 10.0 | 5.3 | - |
| hash (blake3) | 2.00 | 1.6 | 4.0 | 1.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.9 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.75 | 104.3 | 191.3 | 125.5 | 103.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.4 | 54.1 | 50.7 | 50.5 |
| 7a sound encoder (per call) | 1.00 | 34.4 | 41.8 | 35.0 | 34.1 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 12, items/call mean 2.7 max 4; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 577.9 / 719.3 | decode 5034.7 / 5592.4 | e2e(server) 7530.8 / 8048.2 | frontend+IPC 2097.3 / 2968.1
  tokens: prompt 8537, generated 360.9, cached prompt tokens mean 4016 (max 4016), time/output token 13.4 ms
  API-server spread: 3 processes, requests per process [6, 5, 5]
  client latency p50 7.54s p95 8.06s (16 ok), throughput per run 1.0, 1.1 req/s
  server CPU per request (cpu-s): api 4.629, engine 0.836, vllm_main 0.000; total 5.465; pod cgroup 5.490

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1155.1 | 1223.5 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1153.1 | 1222.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 20.9 | 29.8 | - | - |
| 2-4 video load_bytes total | 1.00 | 1130.3 | 1192.0 | 159.9 | - |
| 3a OpenCV open | 1.00 | 21.5 | 49.3 | 14.7 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 1094.7 | 1148.3 | 142.5 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 1049.0 | 1599.2 | - | - |
| 5-6 processor (mm thread) | 1.00 | 534.0 | 641.6 | 523.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 494.7 | 592.1 | 484.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 323.8 | 392.4 | 321.3 | - |
| hash (blake3) | 1.00 | 1.7 | 4.0 | 1.8 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.9 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.75 | 67.5 | 104.2 | 71.8 | 64.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.75 | 58.3 | 87.8 | 61.5 | 54.9 |
  video_resize_norm: {'in': [1, 28, 3, 1080, 1920], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 1080, 1920, 3], 'backend': 'opencv'}
  encoder calls: 12, items/call mean 1.3 max 2; vision calls 12, videos/call mean 1.3 max 2
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 265.1 / 531.0 | decode 3991.6 / 6317.6 | e2e(server) 6593.4 / 8791.1 | frontend+IPC 2235.3 / 3010.1
  tokens: prompt 8334, generated 331.6, cached prompt tokens mean 4016 (max 4016), time/output token 12.6 ms
  API-server spread: 3 processes, requests per process [6, 5, 5]
  client latency p50 6.60s p95 8.80s (16 ok), throughput per run 0.9, 1.2 req/s
  server CPU per request (cpu-s): api 5.141, engine 0.810, vllm_main 0.000; total 5.951; pod cgroup 5.974

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 10224.2 | 12128.9 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 8457.3 | 11941.0 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 73.9 | 1397.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 4192.1 | 5682.0 | 493.7 | - |
| 3a OpenCV open | 1.00 | 106.8 | 330.6 | 23.0 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 3981.4 | 5363.2 | 465.2 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 1093.2 | 5992.6 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 5.9 | 101.9 | 2.4 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 4.1 | 101.1 | 2.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 7169.9 | 10870.6 | - | - |
| 5-6 processor (mm thread) | 1.00 | 538.9 | 611.5 | 550.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 498.2 | 561.0 | 509.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 321.8 | 373.5 | 329.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.97 | 4.3 | 6.6 | 4.5 | - |
| hash (blake3) | 2.00 | 1.5 | 3.4 | 1.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 1.2 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.46 | 189.5 | 289.0 | 201.1 | 189.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 50.1 | 53.9 | 50.2 | 49.2 |
| 7a sound encoder (per call) | 1.00 | 33.9 | 38.6 | 34.0 | 33.9 |
  video_resize_norm: {'in': [1, 28, 3, 1080, 1920], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 1080, 1920, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  encoder calls: 59, items/call mean 4.3 max 6; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 947.9 / 1072.8 | decode 19522.2 / 24001.1 | e2e(server) 37357.4 / 38702.2 | frontend+IPC 17462.4 / 23005.8
  tokens: prompt 8600, generated 354.5, cached prompt tokens mean 4016 (max 4016), time/output token 51.7 ms
  API-server spread: 3 processes, requests per process [46, 41, 41]
  client latency p50 37.38s p95 38.71s (128 ok), throughput per run 1.6, 1.6 req/s
  server CPU per request (cpu-s): api 6.433, engine 0.464, vllm_main 0.000; total 6.896; pod cgroup 6.910

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 8848.2 | 12703.5 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 8784.2 | 12701.6 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 149.5 | 2071.5 | - | - |
| 2-4 video load_bytes total | 1.00 | 4388.7 | 5498.2 | 489.4 | - |
| 3a OpenCV open | 1.00 | 115.1 | 333.2 | 22.3 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 4127.7 | 5223.0 | 461.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 8733.5 | 10322.6 | - | - |
| 5-6 processor (mm thread) | 1.00 | 536.5 | 3390.7 | 591.0 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 497.1 | 3242.6 | 546.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 322.3 | 1913.4 | 355.7 | - |
| hash (blake3) | 1.00 | 3.3 | 6.4 | 3.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 1.1 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.70 | 62.9 | 100.1 | 74.7 | 62.8 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.70 | 54.1 | 83.1 | 63.2 | 53.3 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'opencv'}
  encoder calls: 90, items/call mean 1.4 max 2; vision calls 90, videos/call mean 1.4 max 2
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 287.3 / 485.3 | decode 15100.8 / 20409.5 | e2e(server) 32871.4 / 35078.9 | frontend+IPC 17213.1 / 22755.3
  tokens: prompt 8395, generated 307.3, cached prompt tokens mean 4016 (max 4016), time/output token 50.6 ms
  API-server spread: 3 processes, requests per process [44, 43, 41]
  client latency p50 32.88s p95 35.09s (128 ok), throughput per run 1.9, 1.8 req/s
  server CPU per request (cpu-s): api 6.598, engine 0.416, vllm_main 0.000; total 7.014; pod cgroup 7.027

# vod-1080p-nvdec-cpu32


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 224.6 | 236.3 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 219.8 | 229.5 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 5.6 | 8.9 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 211.7 | 218.8 | 41.2 | 44.8 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 6.6 | 8.0 | 2.9 | 6.3 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 196.7 | 202.7 | 30.0 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.5 | 3.5 | 3.5 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.8 | 4.6 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.0 | 1.6 | 1.0 | 1.0 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.8 | 1.4 | 0.9 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 596.3 | 633.0 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 595.9 | 632.8 | 582.7 | 583.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 541.2 | 582.3 | 533.5 | 534.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 375.1 | 398.8 | 363.8 | 364.2 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.71 | 4.3 | 6.0 | 4.4 | 4.5 | - |
| hash (blake3) | 2.00 | 1.1 | 1.9 | 0.9 | 0.9 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.7 | 0.5 | 0.5 | - |
| 7 encoder call (all items in the step) | 1.00 | 97.4 | 105.5 | 97.6 | - | 97.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.7 | 57.1 | 52.4 | - | 50.7 |
| 7a sound encoder (per call) | 1.00 | 36.4 | 39.2 | 36.1 | - | 36.1 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 186624000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 224.9 / 246.2 | decode 2557.8 / 2841.8 | e2e(server) 3612.2 / 3982.0 | frontend+IPC 865.7 / 930.9
  tokens: prompt 8705, generated 337.0, cached prompt tokens mean 4016 (max 4016), time/output token 7.4 ms
  API-server spread: 2 processes, requests per process [15, 9]
  client latency p50 3.62s p95 3.98s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.759, engine 2.813, mps 0.002, vllm_main 0.000; total 3.574; pod cgroup 3.597

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 199.4 | 225.4 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 197.8 | 224.3 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 7.0 | 10.6 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 189.9 | 214.2 | 39.2 | 42.9 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 6.6 | 7.8 | 3.0 | 6.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 173.8 | 198.6 | 27.9 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.5 | 3.5 | 3.5 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 601.9 | 634.0 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 601.4 | 633.7 | 603.6 | 604.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 553.2 | 585.3 | 554.8 | 555.5 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 384.5 | 404.0 | 385.3 | 385.7 | - |
| hash (blake3) | 1.00 | 1.6 | 2.3 | 1.6 | 1.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 60.6 | 67.3 | 61.7 | - | 60.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 52.2 | 58.3 | 52.7 | - | 50.8 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 186624000}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 177.3 / 195.8 | decode 2427.6 / 3702.0 | e2e(server) 3430.3 / 4733.1 | frontend+IPC 863.4 / 898.9
  tokens: prompt 8521, generated 349.8, cached prompt tokens mean 4016 (max 4016), time/output token 7.3 ms
  API-server spread: 2 processes, requests per process [23, 1]
  client latency p50 3.43s p95 4.74s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.779, engine 2.853, mps 0.001, vllm_main 0.000; total 3.633; pod cgroup 3.659

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 278.5 | 488.4 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 274.0 | 483.3 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 8.0 | 48.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 241.7 | 433.1 | 50.3 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 6.6 | 220.5 | 2.3 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 214.7 | 411.6 | 39.1 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.3 | 3.6 | 3.4 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 3.9 | 5.8 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.0 | 2.4 | 1.0 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.8 | 2.1 | 0.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 1130.9 | 1791.3 | - | - |
| 5-6 processor (mm thread) | 1.00 | 588.9 | 693.5 | 582.0 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 542.7 | 641.4 | 534.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 369.9 | 443.5 | 366.4 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 4.3 | 5.4 | 4.2 | - |
| hash (blake3) | 2.00 | 1.3 | 2.0 | 0.9 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.8 | 1.8 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.69 | 97.2 | 272.6 | 135.0 | 97.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 50.3 | 56.5 | 50.0 | 49.2 |
| 7a sound encoder (per call) | 1.00 | 33.1 | 40.6 | 33.9 | 33.0 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 186624000}
  encoder calls: 11, items/call mean 2.9 max 6; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 573.5 / 716.8 | decode 4930.6 / 5850.1 | e2e(server) 7187.9 / 7581.6 | frontend+IPC 1465.6 / 2437.4
  tokens: prompt 8537, generated 358.4, cached prompt tokens mean 4016 (max 4016), time/output token 13.4 ms
  API-server spread: 3 processes, requests per process [7, 5, 4]
  client latency p50 7.20s p95 7.59s (16 ok), throughput per run 1.1, 1.2 req/s
  server CPU per request (cpu-s): api 0.715, engine 0.836, mps 0.001, vllm_main 0.000; total 1.552; pod cgroup 1.594

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 261.4 | 464.6 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 260.5 | 460.4 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 27.7 | 50.0 | - | - |
| 2-4 video load_bytes total | 1.00 | 236.7 | 424.4 | 54.3 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 5.9 | 200.0 | 2.1 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 206.6 | 406.9 | 42.6 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.7 | 6.8 | 3.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 1204.7 | 2251.5 | - | - |
| 5-6 processor (mm thread) | 1.00 | 608.0 | 708.2 | 622.8 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 558.9 | 652.9 | 572.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 392.8 | 442.0 | 397.1 | - |
| hash (blake3) | 1.00 | 2.0 | 2.3 | 1.8 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 1.4 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.81 | 65.5 | 94.8 | 71.7 | 65.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.81 | 56.4 | 84.1 | 60.2 | 55.7 |
  video_resize_norm: {'in': [1, 28, 3, 1080, 1920], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 174182400}
  encoder calls: 13, items/call mean 1.2 max 2; vision calls 13, videos/call mean 1.2 max 2
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 262.7 / 440.0 | decode 4262.2 / 5931.9 | e2e(server) 6152.9 / 7291.3 | frontend+IPC 1687.1 / 2763.7
  tokens: prompt 8334, generated 321.5, cached prompt tokens mean 4016 (max 4016), time/output token 13.2 ms
  API-server spread: 3 processes, requests per process [7, 6, 3]
  client latency p50 6.16s p95 7.30s (16 ok), throughput per run 1.1, 1.2 req/s
  server CPU per request (cpu-s): api 0.752, engine 0.787, mps 0.000, vllm_main 0.001; total 1.540; pod cgroup 1.596

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1827.5 | 2440.3 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1386.9 | 2419.5 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 24.3 | 108.1 | - | - |
| 2-4 video load_bytes total | 1.00 | 846.3 | 1212.3 | 61.2 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 326.1 | 645.3 | 1.5 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 431.7 | 722.6 | 47.1 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.5 | 7.6 | 6.2 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 432.9 | 1415.6 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.4 | 6.9 | 1.2 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.2 | 6.4 | 1.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 6758.9 | 12225.5 | - | - |
| 5-6 processor (mm thread) | 1.00 | 612.0 | 689.1 | 617.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 560.5 | 631.8 | 565.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 384.9 | 437.3 | 388.5 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.95 | 4.3 | 5.5 | 4.3 | - |
| hash (blake3) | 2.00 | 1.0 | 2.2 | 1.0 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.9 | 1.8 | 0.5 | - |
| 7 encoder call (all items in the step) | 0.63 | 186.4 | 284.8 | 158.8 | 186.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 53.0 | 63.1 | 53.4 | 52.1 |
| 7a sound encoder (per call) | 1.00 | 36.6 | 45.3 | 37.3 | 36.6 |
  video_resize_norm: {'in': [1, 28, 3, 1080, 1920], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 174182400}
  encoder calls: 81, items/call mean 3.2 max 6; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 648.1 / 1096.6 | decode 20909.1 / 27284.4 | e2e(server) 29850.4 / 32865.1 | frontend+IPC 8845.1 / 15076.0
  tokens: prompt 8600, generated 350.7, cached prompt tokens mean 4016 (max 4016), time/output token 58.0 ms
  API-server spread: 3 processes, requests per process [44, 42, 42]
  client latency p50 29.88s p95 32.87s (128 ok), throughput per run 1.9, 2.1 req/s
  server CPU per request (cpu-s): api 0.735, engine 0.507, mps 0.000, vllm_main 0.000; total 1.243; pod cgroup 1.269

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1445.0 | 2532.9 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1441.5 | 2530.7 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 95.8 | 1304.8 | - | - |
| 2-4 video load_bytes total | 1.00 | 852.7 | 1114.5 | 69.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 283.7 | 656.7 | 1.5 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 428.4 | 705.1 | 57.7 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.5 | 7.1 | 3.7 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 5937.0 | 10644.9 | - | - |
| 5-6 processor (mm thread) | 1.00 | 610.4 | 683.8 | 610.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 557.2 | 628.1 | 559.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 384.9 | 438.2 | 387.5 | - |
| hash (blake3) | 1.00 | 1.9 | 2.4 | 1.7 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.9 | 1.2 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.70 | 70.5 | 111.4 | 79.8 | 70.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.70 | 59.9 | 90.2 | 65.3 | 59.0 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 186624000}
  encoder calls: 89, items/call mean 1.4 max 2; vision calls 89, videos/call mean 1.4 max 2
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 298.8 / 488.6 | decode 15504.9 / 21794.5 | e2e(server) 23742.6 / 26533.5 | frontend+IPC 7519.8 / 13299.1
  tokens: prompt 8395, generated 311.3, cached prompt tokens mean 4016 (max 4016), time/output token 52.2 ms
  API-server spread: 3 processes, requests per process [45, 43, 40]
  client latency p50 23.75s p95 26.54s (128 ok), throughput per run 2.5, 2.4 req/s
  server CPU per request (cpu-s): api 0.734, engine 0.433, mps 0.000, vllm_main 0.000; total 1.167; pod cgroup 1.177

# vod-1080p-nvdec-asc12-cpu32


## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 228.5 | 237.5 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 222.4 | 231.4 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 5.4 | 8.8 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 212.9 | 219.9 | 43.6 | 47.1 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 6.6 | 7.9 | 3.2 | 6.6 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 197.4 | 203.0 | 31.8 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.5 | 3.6 | 3.5 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.1 | 4.6 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 1.8 | 1.2 | 1.2 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.9 | 1.6 | 1.0 | 1.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 540.4 | 601.0 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 539.7 | 600.6 | 544.1 | 544.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 504.1 | 559.0 | 505.5 | 506.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 329.9 | 368.9 | 329.9 | 330.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.75 | 4.8 | 7.3 | 5.1 | 5.1 | - |
| hash (blake3) | 2.00 | 1.3 | 2.0 | 1.0 | 1.0 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.7 | 0.5 | 0.5 | - |
| 7 encoder call (all items in the step) | 1.00 | 99.1 | 108.5 | 99.9 | - | 99.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 52.1 | 55.7 | 53.1 | - | 51.2 |
| 7a sound encoder (per call) | 1.00 | 34.7 | 39.3 | 35.4 | - | 34.6 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 186624000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 225.6 / 242.5 | decode 2496.4 / 2746.1 | e2e(server) 3525.6 / 3826.4 | frontend+IPC 813.0 / 887.6
  tokens: prompt 8705, generated 334.2, cached prompt tokens mean 4016 (max 4016), time/output token 7.4 ms
  API-server spread: 6 processes, requests per process [13, 4, 3, 2, 1, 1]
  client latency p50 3.53s p95 3.83s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.772, engine 2.770, mps 0.002, vllm_main 0.000; total 3.544; pod cgroup 3.567

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 203.1 | 227.1 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 202.0 | 225.3 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 8.3 | 15.6 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 189.6 | 215.4 | 41.2 | 44.7 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 6.8 | 8.2 | 3.2 | 6.5 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 174.1 | 199.0 | 29.6 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.5 | 3.6 | 3.5 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 538.8 | 588.8 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 538.2 | 588.5 | 536.7 | 537.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 498.4 | 543.0 | 499.3 | 499.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 339.1 | 365.7 | 333.4 | 333.8 | - |
| hash (blake3) | 1.00 | 1.6 | 2.0 | 1.6 | 1.6 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 62.4 | 67.3 | 62.4 | - | 62.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 51.5 | 55.9 | 51.6 | - | 50.5 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 186624000}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 177.5 / 188.2 | decode 2465.8 / 3515.0 | e2e(server) 3441.9 / 4503.9 | frontend+IPC 793.0 / 837.3
  tokens: prompt 8521, generated 345.9, cached prompt tokens mean 4016 (max 4016), time/output token 7.3 ms
  API-server spread: 6 processes, requests per process [8, 8, 4, 2, 1, 1]
  client latency p50 3.45s p95 4.51s (24 ok), throughput per run 0.3 req/s
  server CPU per request (cpu-s): api 0.767, engine 2.783, mps 0.003, vllm_main 0.001; total 3.553; pod cgroup 3.574

## burst-c8-av: 16 requests (2 run(s)), concurrency 8, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 265.8 | 1227.0 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 261.1 | 1219.4 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 9.9 | 38.7 | - | - |
| 2-4 video load_bytes total | 1.00 | 229.7 | 442.7 | 56.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 6.6 | 8.2 | 2.7 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 216.5 | 418.9 | 43.8 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.3 | 9.9 | 4.6 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.1 | 5.4 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.1 | 1.9 | 1.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.0 | 1.7 | 1.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 573.0 | 1748.1 | - | - |
| 5-6 processor (mm thread) | 1.00 | 542.2 | 606.5 | 535.0 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 504.1 | 565.5 | 495.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 319.7 | 377.4 | 323.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 4.7 | 9.4 | 4.6 | - |
| hash (blake3) | 2.00 | 1.2 | 2.0 | 1.0 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.6 | 2.2 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.50 | 186.3 | 487.4 | 203.2 | 165.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 52.3 | 87.4 | 54.8 | 51.3 |
| 7a sound encoder (per call) | 1.00 | 33.6 | 46.3 | 35.8 | 33.6 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 186624000}
  encoder calls: 8, items/call mean 4.0 max 10; vision calls 16, videos/call mean 1.0 max 1; sound calls 16, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 916.2 / 1171.6 | decode 4775.2 / 5407.3 | e2e(server) 6808.4 / 7457.3 | frontend+IPC 1134.6 / 2293.6
  tokens: prompt 8537, generated 359.6, cached prompt tokens mean 4016 (max 4016), time/output token 12.6 ms
  API-server spread: 8 processes, requests per process [5, 2, 2, 2, 2, 1, 1, 1]
  client latency p50 6.82s p95 7.47s (16 ok), throughput per run 1.1, 1.1 req/s
  server CPU per request (cpu-s): api 0.718, engine 0.849, mps 0.001, vllm_main 0.000; total 1.567; pod cgroup 1.592

## burst-c8-v: 16 requests (2 run(s)), concurrency 8, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 262.5 | 428.3 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 261.0 | 427.2 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 20.4 | 43.8 | - | - |
| 2-4 video load_bytes total | 1.00 | 234.4 | 387.3 | 57.4 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 6.5 | 193.5 | 2.8 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 216.1 | 228.9 | 43.8 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 5.7 | 10.3 | 5.6 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 584.9 | 1362.6 | - | - |
| 5-6 processor (mm thread) | 1.00 | 549.6 | 634.2 | 551.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 506.7 | 585.0 | 512.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 345.6 | 391.1 | 341.2 | - |
| hash (blake3) | 1.00 | 1.9 | 5.3 | 2.0 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.9 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.44 | 67.5 | 258.7 | 113.2 | 67.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.44 | 57.0 | 200.0 | 90.9 | 56.2 |
  video_resize_norm: {'in': [1, 28, 3, 1080, 1920], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 174182400}
  encoder calls: 7, items/call mean 2.3 max 6; vision calls 7, videos/call mean 2.3 max 6
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 683.4 / 787.0 | decode 3942.5 / 5063.6 | e2e(server) 5621.9 / 6807.9 | frontend+IPC 1028.8 / 1844.8
  tokens: prompt 8334, generated 324.8, cached prompt tokens mean 4016 (max 4016), time/output token 12.7 ms
  API-server spread: 9 processes, requests per process [4, 3, 2, 2, 1, 1, 1, 1, 1]
  client latency p50 5.63s p95 6.81s (16 ok), throughput per run 1.2, 1.3 req/s
  server CPU per request (cpu-s): api 0.728, engine 0.761, mps 0.001, vllm_main 0.000; total 1.490; pod cgroup 1.518

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1380.7 | 3400.2 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1373.6 | 3393.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 10.1 | 2317.4 | - | - |
| 2-4 video load_bytes total | 1.00 | 462.4 | 768.3 | 84.2 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 7.3 | 461.7 | 2.6 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 288.7 | 576.7 | 67.7 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.6 | 10.5 | 8.0 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 4.2 | 11.9 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 1.2 | 2.7 | 1.2 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 1.0 | 2.5 | 1.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 1304.3 | 3403.5 | - | - |
| 5-6 processor (mm thread) | 1.00 | 620.2 | 704.3 | 607.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 567.7 | 648.7 | 561.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 382.6 | 445.4 | 377.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 0.91 | 4.7 | 6.7 | 4.7 | - |
| hash (blake3) | 2.00 | 1.3 | 2.3 | 1.0 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.8 | 1.8 | 0.6 | - |
| 7 encoder call (all items in the step) | 0.16 | 577.4 | 1008.7 | 593.2 | 577.4 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 50.9 | 59.0 | 51.0 | 50.0 |
| 7a sound encoder (per call) | 1.00 | 34.3 | 41.7 | 34.6 | 34.3 |
  video_resize_norm: {'in': [1, 28, 3, 1080, 1920], 'out': [16744, 1536], 'grid_thw': [[14, 26, 46]]}
  video_decode_total: {'frames': [28, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 224000, 'sr': 16000}
  d2h: {'bytes': 174182400}
  encoder calls: 21, items/call mean 12.2 max 22; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 4391.5 / 6651.2 | decode 18423.9 / 22771.9 | e2e(server) 25848.6 / 27244.4 | frontend+IPC 3353.1 / 6527.4
  tokens: prompt 8600, generated 353.5, cached prompt tokens mean 4016 (max 4016), time/output token 49.8 ms
  API-server spread: 12 processes, requests per process [16, 14, 14, 13, 12, 11, 10, 10, 10, 9, 6, 3]
  client latency p50 25.85s p95 27.25s (128 ok), throughput per run 2.3, 2.4 req/s
  server CPU per request (cpu-s): api 0.768, engine 0.451, mps 0.000, vllm_main 0.000; total 1.219; pod cgroup 1.231

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1510.0 | 3396.0 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1508.1 | 3393.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 1072.6 | 3085.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 467.9 | 863.7 | 129.8 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 7.9 | 426.9 | 2.7 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 379.1 | 705.2 | 113.5 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 3.5 | 12.0 | 7.5 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 1330.1 | 3368.7 | - | - |
| 5-6 processor (mm thread) | 1.00 | 599.0 | 681.3 | 601.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 554.5 | 629.9 | 556.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 371.5 | 433.8 | 377.8 | - |
| hash (blake3) | 1.00 | 1.9 | 2.7 | 1.8 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 1.2 | 0.3 | - |
| 7 encoder call (all items in the step) | 0.17 | 274.8 | 781.4 | 277.0 | 270.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.17 | 211.4 | 673.1 | 216.4 | 204.8 |
  video_resize_norm: {'in': [1, 30, 3, 1080, 1920], 'out': [17940, 1536], 'grid_thw': [[15, 26, 46]]}
  video_decode_total: {'frames': [30, 1080, 1920, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 186624000}
  encoder calls: 22, items/call mean 5.8 max 11; vision calls 22, videos/call mean 5.8 max 11
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 2184.1 / 2973.6 | decode 13798.3 / 19855.0 | e2e(server) 19110.2 / 23663.9 | frontend+IPC 3048.3 / 6556.3
  tokens: prompt 8395, generated 311.2, cached prompt tokens mean 4016 (max 4016), time/output token 43.3 ms
  API-server spread: 12 processes, requests per process [21, 20, 14, 12, 11, 11, 10, 8, 7, 5, 5, 4]
  client latency p50 19.11s p95 23.67s (128 ok), throughput per run 3.3, 2.7 req/s
  server CPU per request (cpu-s): api 0.801, engine 0.357, mps 0.000, vllm_main 0.000; total 1.159; pod cgroup 1.168

