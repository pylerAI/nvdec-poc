
# qwen-live360-nvdec-asc12

## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 39.4 | 42.2 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 30.6 | 33.1 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 1.7 | 2.7 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 27.4 | 30.6 | 16.9 | 19.1 | - |
| 2 remux TS->fMP4 | 1.00 | 4.4 | 5.7 | 4.5 | 6.0 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.8 | 2.5 | 1.4 | 2.1 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 20.4 | 22.8 | 9.8 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 0.3 | 0.3 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 7.4 | 8.6 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 4.3 | 5.7 | 4.5 | 4.6 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.2 | 0.4 | 0.2 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 3.9 | 5.1 | 4.1 | 4.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 60.6 | 88.0 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 60.1 | 87.5 | 65.8 | 65.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 52.2 | 79.3 | 57.2 | 57.2 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 44.6 | 69.3 | 49.2 | 49.2 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.4 | 2.6 | 2.4 | 2.4 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.3 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 73.5 | 77.5 | 73.9 | - | 73.5 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 36.9 | 38.7 | 37.1 | - | 36.7 |
| 7a sound encoder (per call) | 1.00 | 33.0 | 34.4 | 33.1 | - | 33.0 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.6 | prefill 167.0 / 174.8 | decode 1628.8 / 1827.9 | e2e(server) 1921.8 / 2121.4 | frontend+IPC 116.0 / 156.7
  tokens: prompt 5438, generated 232.7, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 6 processes, requests per process [8, 7, 5, 2, 1, 1]
  client latency p50 1.92s p95 2.12s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.189, engine 1.843, mps 0.001, vllm_main 0.000; total 2.033; pod cgroup 2.048

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 30.6 | 33.3 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 29.6 | 32.2 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 2.3 | 3.0 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 26.4 | 28.1 | 15.1 | 17.3 | - |
| 2 remux TS->fMP4 | 1.00 | 4.4 | 5.2 | 4.1 | 5.5 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.9 | 2.1 | 1.3 | 2.0 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 18.9 | 21.0 | 8.7 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.2 | 0.3 | 0.2 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 59.5 | 82.1 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 59.1 | 81.5 | 60.5 | 60.6 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 50.6 | 74.7 | 53.2 | 53.3 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 44.8 | 69.0 | 47.4 | 47.4 | - |
| hash (blake3) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 40.3 | 41.8 | 40.3 | - | 40.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 36.9 | 38.3 | 36.9 | - | 36.6 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 129.7 / 133.2 | decode 1616.7 / 1765.8 | e2e(server) 1848.9 / 2015.2 | frontend+IPC 108.8 / 134.1
  tokens: prompt 5356, generated 230.1, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 9 processes, requests per process [9, 4, 3, 2, 2, 1, 1, 1, 1]
  client latency p50 1.85s p95 2.02s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.177, engine 1.788, mps 0.001, vllm_main 0.000; total 1.966; pod cgroup 1.982

## burst-av: 192 requests (3 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 166.2 | 253.1 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 151.7 | 232.4 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.8 | 8.4 | - | - |
| 2-4 video load_bytes total | 1.00 | 139.5 | 214.5 | 37.9 | - |
| 2 remux TS->fMP4 | 1.00 | 43.5 | 80.0 | 14.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 7.7 | 60.2 | 1.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 52.6 | 97.6 | 20.3 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 2.4 | 0.4 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 11.0 | 20.3 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 7.7 | 14.0 | 6.5 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.1 | 0.6 | 0.1 | - |
| 6b'' PyAV AAC decode | 1.00 | 7.0 | 13.0 | 6.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 199.8 | 442.0 | - | - |
| 5-6 processor (mm thread) | 1.00 | 78.1 | 119.1 | 77.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 67.1 | 103.6 | 66.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 58.7 | 91.2 | 58.2 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.9 | 4.2 | 2.5 | - |
| hash (blake3) | 2.00 | 0.2 | 0.4 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.4 | 0.7 | 0.4 | - |
| 7 encoder call (all items in the step) | 0.07 | 864.3 | 2835.5 | 1184.5 | 864.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 41.2 | 46.9 | 40.8 | 41.0 |
| 7a sound encoder (per call) | 1.00 | 37.4 | 41.7 | 37.1 | 37.4 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 13, items/call mean 29.5 max 68; vision calls 192, videos/call mean 1.0 max 1; sound calls 192, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.1 / 0.2 | prefill 3638.9 / 6439.7 | decode 8773.0 / 11165.9 | e2e(server) 14642.1 / 15290.2 | frontend+IPC 508.3 / 3932.5
  tokens: prompt 5438, generated 229.9, cached prompt tokens mean 4016 (max 4016), time/output token 38.3 ms
  API-server spread: 12 processes, requests per process [20, 20, 19, 19, 18, 16, 15, 15, 15, 14, 12, 9]
  client latency p50 14.65s p95 15.29s (192 ok), throughput per run 4.3, 4.1, 4.2 req/s
  server CPU per request (cpu-s): api 0.162, engine 0.246, mps 0.000, vllm_main 0.000; total 0.408; pod cgroup 0.413

## burst-v: 192 requests (3 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 147.8 | 1182.6 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 144.9 | 1177.0 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.6 | 1050.1 | - | - |
| 2-4 video load_bytes total | 1.00 | 126.8 | 199.6 | 44.1 | - |
| 2 remux TS->fMP4 | 1.00 | 36.2 | 94.6 | 13.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.4 | 60.1 | 1.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 50.7 | 110.6 | 27.5 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 1.4 | 0.4 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 160.6 | 350.7 | - | - |
| 5-6 processor (mm thread) | 1.00 | 65.5 | 116.1 | 69.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 56.4 | 101.9 | 61.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 49.3 | 92.5 | 53.8 | - |
| hash (blake3) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.07 | 116.3 | 813.8 | 243.6 | 116.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.07 | 94.1 | 396.9 | 181.9 | 92.3 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 13, items/call mean 14.8 max 34; vision calls 13, videos/call mean 14.8 max 34
  engine per request (p50 / p95 ms): queued 0.1 / 0.1 | prefill 1192.8 / 1553.2 | decode 8563.8 / 9335.9 | e2e(server) 10675.3 / 11078.9 | frontend+IPC 395.9 / 1706.0
  tokens: prompt 5356, generated 231.8, cached prompt tokens mean 4016 (max 4016), time/output token 37.3 ms
  API-server spread: 12 processes, requests per process [21, 20, 19, 18, 18, 16, 15, 14, 13, 13, 13, 12]
  client latency p50 10.68s p95 11.08s (192 ok), throughput per run 5.7, 5.9, 5.6 req/s
  server CPU per request (cpu-s): api 0.150, engine 0.179, mps 0.000, vllm_main 0.000; total 0.329; pod cgroup 0.334

# qwen-live360-cpu-asc12

## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 71.8 | 84.5 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 63.5 | 74.3 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 1.5 | 2.8 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 60.6 | 71.2 | 21.3 | 182.4 | - |
| 3a OpenCV open | 1.00 | 2.5 | 2.7 | 2.5 | 4.3 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 54.8 | 65.1 | 16.1 | 154.3 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 7.0 | 8.5 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 5.1 | 6.4 | 5.0 | 5.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 4.6 | 5.2 | 4.6 | 4.6 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 45.6 | 56.5 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 45.3 | 56.3 | 46.1 | 46.1 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 38.1 | 47.9 | 39.0 | 39.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 30.2 | 40.6 | 31.5 | 31.5 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.3 | 2.6 | 2.3 | 2.3 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.3 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 75.1 | 77.8 | 74.8 | - | 75.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 37.5 | 39.8 | 37.9 | - | 37.3 |
| 7a sound encoder (per call) | 1.00 | 33.7 | 36.4 | 33.9 | - | 33.7 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.5 | prefill 169.0 / 173.9 | decode 1559.3 / 1726.3 | e2e(server) 1866.2 / 2026.5 | frontend+IPC 138.1 / 153.5
  tokens: prompt 5438, generated 224.3, cached prompt tokens mean 4016 (max 4016), time/output token 6.9 ms
  API-server spread: 4 processes, requests per process [17, 5, 1, 1]
  client latency p50 1.87s p95 2.03s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.317, engine 1.742, vllm_main 0.000; total 2.059; pod cgroup 2.083

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 75.1 | 84.4 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 74.1 | 83.5 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 1.8 | 3.0 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 71.4 | 80.6 | 20.0 | 178.3 | - |
| 3a OpenCV open | 1.00 | 2.5 | 4.2 | 2.7 | 4.6 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 65.5 | 72.7 | 14.9 | 151.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 40.4 | 51.7 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 40.0 | 51.4 | 41.3 | 41.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 34.5 | 44.2 | 35.6 | 35.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 28.6 | 38.3 | 29.5 | 29.5 | - |
| hash (blake3) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 37.7 | 40.2 | 38.0 | - | 37.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 35.3 | 37.3 | 35.6 | - | 35.1 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'opencv'}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.6 | prefill 124.2 / 130.7 | decode 1404.1 / 1585.0 | e2e(server) 1658.8 / 1842.1 | frontend+IPC 131.8 / 138.5
  tokens: prompt 5356, generated 214.7, cached prompt tokens mean 4016 (max 4016), time/output token 6.6 ms
  API-server spread: 5 processes, requests per process [9, 8, 3, 2, 2]
  client latency p50 1.66s p95 1.84s (24 ok), throughput per run 0.6 req/s
  server CPU per request (cpu-s): api 0.302, engine 1.589, vllm_main 0.000; total 1.891; pod cgroup 1.926

## burst-av: 192 requests (3 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 240.8 | 328.5 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 146.2 | 208.2 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 3.5 | 10.4 | - | - |
| 2-4 video load_bytes total | 1.00 | 135.2 | 180.3 | 50.0 | - |
| 3a OpenCV open | 1.00 | 9.4 | 29.1 | 3.9 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 117.0 | 150.9 | 41.2 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 83.2 | 147.1 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 72.2 | 135.0 | 22.6 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.4 | 1.7 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 70.1 | 131.0 | 21.7 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 141.0 | 312.2 | - | - |
| 5-6 processor (mm thread) | 1.00 | 50.9 | 81.9 | 51.6 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 42.1 | 71.2 | 43.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 33.3 | 61.0 | 35.5 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.9 | 9.2 | 2.6 | - |
| hash (blake3) | 2.00 | 0.2 | 0.6 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.6 | 0.4 | - |
| 7 encoder call (all items in the step) | 0.07 | 954.9 | 2493.6 | 1054.4 | 954.8 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 35.8 | 42.2 | 36.4 | 35.5 |
| 7a sound encoder (per call) | 1.00 | 32.4 | 36.5 | 32.7 | 32.4 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  encoder calls: 13, items/call mean 29.5 max 68; vision calls 192, videos/call mean 1.0 max 1; sound calls 192, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.1 / 0.1 | prefill 3240.3 / 3658.2 | decode 7970.3 / 10245.1 | e2e(server) 13505.5 / 14016.0 | frontend+IPC 2262.3 / 3510.4
  tokens: prompt 5438, generated 228.0, cached prompt tokens mean 4016 (max 4016), time/output token 36.4 ms
  API-server spread: 12 processes, requests per process [25, 24, 20, 17, 16, 16, 15, 15, 15, 12, 9, 8]
  client latency p50 13.51s p95 14.02s (192 ok), throughput per run 4.1, 4.5, 4.5 req/s
  server CPU per request (cpu-s): api 0.399, engine 0.233, vllm_main 0.000; total 0.632; pod cgroup 0.653

## burst-v: 192 requests (3 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 152.7 | 212.4 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 144.3 | 208.9 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 3.5 | 10.5 | - | - |
| 2-4 video load_bytes total | 1.00 | 132.5 | 170.1 | 48.8 | - |
| 3a OpenCV open | 1.00 | 12.1 | 30.4 | 4.0 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 112.2 | 139.2 | 39.5 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 161.8 | 354.9 | - | - |
| 5-6 processor (mm thread) | 1.00 | 52.6 | 97.9 | 54.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 45.7 | 85.9 | 48.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 38.4 | 74.3 | 40.6 | - |
| hash (blake3) | 1.00 | 0.2 | 0.8 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.06 | 340.8 | 517.0 | 234.1 | 203.8 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.06 | 276.3 | 414.5 | 190.7 | 166.0 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'opencv'}
  encoder calls: 12, items/call mean 16.0 max 36; vision calls 12, videos/call mean 16.0 max 36
  engine per request (p50 / p95 ms): queued 0.1 / 0.2 | prefill 1199.8 / 1237.9 | decode 7475.2 / 8088.5 | e2e(server) 9308.6 / 9792.7 | frontend+IPC 444.8 / 1514.5
  tokens: prompt 5356, generated 218.0, cached prompt tokens mean 4016 (max 4016), time/output token 33.9 ms
  API-server spread: 12 processes, requests per process [26, 23, 21, 20, 19, 19, 19, 17, 9, 9, 6, 4]
  client latency p50 9.31s p95 9.80s (192 ok), throughput per run 6.5, 6.4, 6.6 req/s
  server CPU per request (cpu-s): api 0.378, engine 0.157, vllm_main 0.000; total 0.535; pod cgroup 0.555

# qwen-live360-cpu-mps

## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 72.0 | 81.6 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 63.2 | 73.5 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 1.6 | 2.8 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 60.2 | 70.1 | 21.7 | 177.7 | - |
| 3a OpenCV open | 1.00 | 2.5 | 2.9 | 2.7 | 4.3 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 52.3 | 64.3 | 16.3 | 151.9 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 7.1 | 7.8 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 5.1 | 5.3 | 5.1 | 5.1 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.2 | 0.3 | 0.2 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 4.6 | 4.8 | 4.6 | 4.6 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 54.8 | 62.2 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 54.3 | 61.7 | 51.1 | 51.1 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 44.1 | 52.1 | 42.7 | 42.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 36.7 | 45.1 | 35.5 | 35.5 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.4 | 2.7 | 2.4 | 2.4 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 72.3 | 76.9 | 73.3 | - | 72.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 36.2 | 38.5 | 36.6 | - | 36.0 |
| 7a sound encoder (per call) | 1.00 | 32.5 | 36.1 | 33.0 | - | 32.4 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.9 | prefill 164.8 / 177.7 | decode 1538.8 / 1770.3 | e2e(server) 1872.8 / 2061.6 | frontend+IPC 137.1 / 157.7
  tokens: prompt 5438, generated 218.9, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 9 processes, requests per process [6, 5, 4, 2, 2, 2, 1, 1, 1]
  client latency p50 1.88s p95 2.06s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.321, engine 1.733, mps 0.001, vllm_main 0.000; total 2.055; pod cgroup 2.078

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 67.1 | 73.4 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 65.8 | 72.2 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 1.7 | 2.8 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 63.2 | 68.7 | 20.3 | 174.7 | - |
| 3a OpenCV open | 1.00 | 2.5 | 2.7 | 2.5 | 4.4 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 57.5 | 63.1 | 15.2 | 150.8 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 52.5 | 81.7 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 52.0 | 81.2 | 50.7 | 50.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 43.8 | 74.6 | 43.8 | 43.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 37.6 | 68.5 | 37.4 | 37.5 | - |
| hash (blake3) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 39.7 | 41.2 | 40.0 | - | 39.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 36.3 | 37.6 | 36.5 | - | 36.1 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'opencv'}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 2.0 | prefill 128.6 / 133.9 | decode 1606.9 / 1768.0 | e2e(server) 1866.2 / 2015.5 | frontend+IPC 138.1 / 157.3
  tokens: prompt 5356, generated 229.9, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 7 processes, requests per process [8, 5, 4, 3, 2, 1, 1]
  client latency p50 1.87s p95 2.02s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.311, engine 1.774, mps 0.000, vllm_main 0.000; total 2.086; pod cgroup 2.109

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 256.0 | 326.1 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 152.1 | 203.2 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 3.5 | 10.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 142.5 | 188.1 | 51.3 | - |
| 3a OpenCV open | 1.00 | 10.0 | 23.7 | 4.0 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 123.2 | 162.1 | 42.0 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 97.9 | 158.4 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 84.7 | 150.3 | 24.9 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.4 | 1.2 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 82.7 | 148.7 | 24.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 191.3 | 387.1 | - | - |
| 5-6 processor (mm thread) | 1.00 | 62.7 | 110.7 | 64.1 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 52.2 | 96.5 | 54.5 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 44.0 | 88.2 | 46.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 3.0 | 8.3 | 2.6 | - |
| hash (blake3) | 2.00 | 0.2 | 0.6 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.7 | 0.4 | - |
| 7 encoder call (all items in the step) | 0.08 | 1125.7 | 1941.4 | 920.2 | 879.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 35.5 | 44.4 | 36.3 | 35.3 |
| 7a sound encoder (per call) | 1.00 | 31.9 | 37.4 | 32.6 | 31.9 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'opencv'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  encoder calls: 10, items/call mean 25.6 max 52; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.1 / 0.1 | prefill 3195.4 / 3939.3 | decode 7983.4 / 10391.9 | e2e(server) 13477.3 / 14148.9 | frontend+IPC 2136.3 / 2788.0
  tokens: prompt 5438, generated 226.8, cached prompt tokens mean 4016 (max 4016), time/output token 35.2 ms
  API-server spread: 12 processes, requests per process [15, 14, 14, 14, 13, 13, 12, 11, 7, 6, 6, 3]
  client latency p50 13.48s p95 14.15s (128 ok), throughput per run 4.0, 4.6 req/s
  server CPU per request (cpu-s): api 0.421, engine 0.239, mps 0.000, vllm_main 0.000; total 0.660; pod cgroup 0.682

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 159.5 | 212.0 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 155.0 | 204.7 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 3.6 | 9.2 | - | - |
| 2-4 video load_bytes total | 1.00 | 139.9 | 187.8 | 51.6 | - |
| 3a OpenCV open | 1.00 | 12.3 | 42.0 | 4.5 | - |
| 3b OpenCV decode (all frames, keep sampled) | 1.00 | 117.3 | 154.6 | 41.6 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 209.3 | 419.9 | - | - |
| 5-6 processor (mm thread) | 1.00 | 59.7 | 124.3 | 64.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 52.7 | 112.1 | 56.3 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 46.2 | 101.5 | 49.0 | - |
| hash (blake3) | 1.00 | 0.2 | 0.8 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.07 | 194.7 | 490.4 | 223.2 | 194.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.07 | 162.5 | 430.4 | 172.2 | 158.3 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'opencv'}
  encoder calls: 9, items/call mean 14.2 max 31; vision calls 9, videos/call mean 14.2 max 31
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 1288.5 / 1621.6 | decode 7396.7 / 8155.4 | e2e(server) 9553.3 / 10070.0 | frontend+IPC 994.2 / 1448.2
  tokens: prompt 5356, generated 222.3, cached prompt tokens mean 4016 (max 4016), time/output token 33.1 ms
  API-server spread: 11 processes, requests per process [19, 15, 14, 14, 13, 12, 11, 11, 10, 5, 4]
  client latency p50 9.56s p95 10.07s (128 ok), throughput per run 6.5, 6.3 req/s
  server CPU per request (cpu-s): api 0.399, engine 0.161, mps 0.000, vllm_main 0.000; total 0.560; pod cgroup 0.580

# qwen-live360-nvdec-nomps

## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 38.8 | 42.1 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 30.5 | 34.1 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 1.8 | 2.8 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 27.2 | 31.6 | 15.9 | 18.5 | - |
| 2 remux TS->fMP4 | 1.00 | 4.5 | 7.5 | 4.3 | 6.2 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 2.0 | 2.7 | 1.4 | 2.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 19.6 | 22.4 | 9.0 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.2 | 0.3 | 0.2 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 7.0 | 8.3 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 4.4 | 5.1 | 4.4 | 4.4 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.1 | 0.2 | 0.2 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 4.0 | 4.6 | 4.0 | 4.0 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 58.4 | 71.2 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 58.0 | 70.7 | 57.9 | 57.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 50.3 | 59.9 | 48.8 | 48.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 44.2 | 53.7 | 42.2 | 42.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.2 | 2.6 | 2.2 | 2.2 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 70.4 | 73.1 | 70.9 | - | 70.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 35.6 | 37.6 | 35.9 | - | 35.4 |
| 7a sound encoder (per call) | 1.00 | 32.0 | 33.6 | 32.2 | - | 32.0 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.5 | prefill 160.9 / 166.4 | decode 1486.3 / 1652.8 | e2e(server) 1758.4 / 1936.4 | frontend+IPC 114.3 / 128.7
  tokens: prompt 5438, generated 235.6, cached prompt tokens mean 4016 (max 4016), time/output token 6.4 ms
  API-server spread: 9 processes, requests per process [9, 3, 3, 2, 2, 2, 1, 1, 1]
  client latency p50 1.76s p95 1.94s (24 ok), throughput per run 0.6 req/s
  server CPU per request (cpu-s): api 0.187, engine 1.705, vllm_main 0.000; total 1.893; pod cgroup 1.908

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 31.3 | 34.5 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 30.2 | 33.5 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 1.8 | 2.6 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 27.1 | 30.4 | 15.5 | 18.0 | - |
| 2 remux TS->fMP4 | 1.00 | 4.7 | 5.5 | 4.3 | 6.1 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.9 | 2.1 | 1.3 | 2.0 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 19.4 | 23.0 | 8.7 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 0.3 | 0.2 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 59.3 | 75.7 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 58.9 | 75.1 | 58.6 | 58.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 50.5 | 67.4 | 50.9 | 50.9 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 45.2 | 61.8 | 45.3 | 45.4 | - |
| hash (blake3) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 38.3 | 39.3 | 38.3 | - | 38.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 35.7 | 36.7 | 35.8 | - | 35.5 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.5 | prefill 124.5 / 128.4 | decode 1525.5 / 1579.7 | e2e(server) 1751.9 / 1808.1 | frontend+IPC 105.5 / 122.7
  tokens: prompt 5356, generated 235.5, cached prompt tokens mean 4016 (max 4016), time/output token 6.4 ms
  API-server spread: 6 processes, requests per process [9, 8, 3, 2, 1, 1]
  client latency p50 1.75s p95 1.81s (24 ok), throughput per run 0.6 req/s
  server CPU per request (cpu-s): api 0.181, engine 1.667, vllm_main 0.000; total 1.849; pod cgroup 1.863

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1934.9 | 2717.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1922.2 | 2704.8 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.7 | 24.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 1883.1 | 2681.5 | 625.7 | - |
| 2 remux TS->fMP4 | 1.00 | 62.0 | 104.7 | 14.7 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 871.4 | 1034.5 | 9.3 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 972.8 | 1778.8 | 600.1 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 2.0 | 0.3 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 8.7 | 46.0 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 5.5 | 21.8 | 5.6 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.1 | 0.6 | 0.1 | - |
| 6b'' PyAV AAC decode | 1.00 | 5.0 | 12.3 | 5.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 82.7 | 160.0 | - | - |
| 5-6 processor (mm thread) | 1.00 | 72.2 | 99.0 | 69.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 61.3 | 89.3 | 59.4 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 52.7 | 75.1 | 51.9 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.5 | 3.9 | 2.3 | - |
| hash (blake3) | 2.00 | 0.1 | 0.4 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.4 | 0.6 | 0.4 | - |
| 7 encoder call (all items in the step) | 0.06 | 1909.4 | 2728.7 | 1408.6 | 1524.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 34.7 | 40.5 | 45.9 | 34.5 |
| 7a sound encoder (per call) | 1.00 | 31.4 | 35.1 | 40.2 | 31.4 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 8, items/call mean 32.0 max 68; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.1 / 0.2 | prefill 3141.9 / 5885.3 | decode 9185.7 / 9993.6 | e2e(server) 15500.1 / 15826.7 | frontend+IPC 2720.5 / 5678.4
  tokens: prompt 5438, generated 231.7, cached prompt tokens mean 4016 (max 4016), time/output token 39.4 ms
  API-server spread: 12 processes, requests per process [14, 12, 11, 11, 11, 11, 11, 11, 10, 10, 9, 7]
  client latency p50 15.50s p95 15.83s (128 ok), throughput per run 4.0, 4.1 req/s
  server CPU per request (cpu-s): api 0.739, engine 0.249, vllm_main 0.000; total 0.988; pod cgroup 0.993

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 1888.6 | 2861.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 1887.6 | 2860.6 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.7 | 1038.5 | - | - |
| 2-4 video load_bytes total | 1.00 | 1847.6 | 2560.7 | 579.0 | - |
| 2 remux TS->fMP4 | 1.00 | 61.7 | 106.5 | 13.9 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 880.0 | 1499.8 | 8.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 900.6 | 1603.7 | 555.1 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 1.6 | 0.3 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 71.6 | 135.9 | - | - |
| 5-6 processor (mm thread) | 1.00 | 59.0 | 82.4 | 59.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 51.1 | 75.1 | 51.4 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 44.8 | 69.1 | 45.2 | - |
| hash (blake3) | 1.00 | 0.2 | 0.4 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.4 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.06 | 522.8 | 1024.9 | 458.1 | 430.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.06 | 519.9 | 932.5 | 417.4 | 393.3 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 8, items/call mean 16.0 max 36; vision calls 8, videos/call mean 16.0 max 36
  engine per request (p50 / p95 ms): queued 0.1 / 0.2 | prefill 1589.8 / 2444.9 | decode 7989.0 / 8564.9 | e2e(server) 12116.8 / 12454.2 | frontend+IPC 2270.4 / 3740.4
  tokens: prompt 5356, generated 236.7, cached prompt tokens mean 4016 (max 4016), time/output token 33.5 ms
  API-server spread: 12 processes, requests per process [16, 15, 13, 12, 11, 11, 11, 11, 10, 9, 6, 3]
  client latency p50 12.12s p95 12.46s (128 ok), throughput per run 5.1, 5.1 req/s
  server CPU per request (cpu-s): api 0.673, engine 0.190, vllm_main 0.000; total 0.863; pod cgroup 0.868

# qwen-live360-nvdec-nojson

## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 38.2 | 41.1 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 29.7 | 32.1 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 1.8 | 2.9 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 26.6 | 28.6 | 14.7 | 17.1 | - |
| 2 remux TS->fMP4 | 1.00 | 4.3 | 5.3 | 4.1 | 5.8 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.8 | 2.2 | 1.2 | 1.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 19.2 | 20.8 | 8.4 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.2 | 0.3 | 0.2 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 7.2 | 8.8 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 4.3 | 5.4 | 4.5 | 4.5 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.1 | 0.2 | 0.2 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 3.9 | 4.9 | 4.1 | 4.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 58.6 | 64.0 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 58.1 | 63.5 | 57.7 | 57.8 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 50.1 | 53.5 | 48.6 | 48.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 42.9 | 46.0 | 41.3 | 41.4 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.4 | 3.2 | 2.5 | 2.5 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 81.2 | 83.4 | 78.2 | - | 81.1 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 40.8 | 42.3 | 39.4 | - | 40.5 |
| 7a sound encoder (per call) | 1.00 | 37.5 | 38.2 | 35.8 | - | 37.3 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 183.1 / 186.5 | decode 1544.9 / 1707.6 | e2e(server) 1842.2 / 2003.5 | frontend+IPC 111.2 / 118.7
  tokens: prompt 5438, generated 232.0, cached prompt tokens mean 4016 (max 4016), time/output token 6.8 ms
  API-server spread: 6 processes, requests per process [6, 6, 5, 4, 2, 1]
  client latency p50 1.84s p95 2.01s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.176, engine 1.747, mps 0.000, vllm_main 0.000; total 1.924; pod cgroup 1.938

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 30.8 | 33.3 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 29.7 | 32.1 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 1.7 | 2.7 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 26.6 | 29.6 | 14.2 | 16.5 | - |
| 2 remux TS->fMP4 | 1.00 | 4.2 | 5.2 | 3.9 | 5.6 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.7 | 1.9 | 1.0 | 1.7 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 19.9 | 22.5 | 8.3 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.2 | 0.3 | 0.2 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 50.7 | 61.7 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 50.2 | 61.2 | 51.5 | 51.5 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 43.6 | 52.3 | 44.6 | 44.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 37.7 | 45.2 | 38.7 | 38.7 | - |
| hash (blake3) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 42.8 | 45.4 | 41.9 | - | 42.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 40.8 | 41.8 | 39.5 | - | 40.5 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 0.0 | prefill 140.3 / 147.7 | decode 20.3 / 33.4 | e2e(server) 255.8 / 270.2 | frontend+IPC 95.4 / 108.7
  tokens: prompt 5356, generated 4.3, cached prompt tokens mean 4016 (max 4016), time/output token 6.7 ms
  API-server spread: 7 processes, requests per process [8, 6, 4, 2, 2, 1, 1]
  client latency p50 0.26s p95 0.27s (24 ok), throughput per run 3.9 req/s
  server CPU per request (cpu-s): api 0.090, engine 0.167, mps 0.000, vllm_main 0.000; total 0.257; pod cgroup 0.265

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 174.1 | 254.6 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 154.2 | 233.6 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.6 | 9.0 | - | - |
| 2-4 video load_bytes total | 1.00 | 143.6 | 221.4 | 38.6 | - |
| 2 remux TS->fMP4 | 1.00 | 49.4 | 80.9 | 15.3 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 21.9 | 68.7 | 1.3 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 55.4 | 102.9 | 20.4 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 2.5 | 0.3 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 12.0 | 19.0 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 8.4 | 13.8 | 6.6 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.2 | 0.6 | 0.1 | - |
| 6b'' PyAV AAC decode | 1.00 | 7.8 | 13.3 | 6.2 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 181.4 | 348.5 | - | - |
| 5-6 processor (mm thread) | 1.00 | 68.4 | 96.4 | 68.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 57.6 | 83.6 | 58.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 48.6 | 75.2 | 50.0 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.9 | 5.0 | 2.5 | - |
| hash (blake3) | 2.00 | 0.2 | 0.4 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 1.3 | 0.4 | - |
| 7 encoder call (all items in the step) | 0.07 | 795.1 | 2663.8 | 1087.2 | 795.1 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 39.7 | 42.5 | 38.7 | 39.5 |
| 7a sound encoder (per call) | 1.00 | 36.0 | 38.8 | 35.2 | 36.0 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 9, items/call mean 28.4 max 66; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.1 / 0.2 | prefill 3258.7 / 3555.4 | decode 3903.0 / 6440.7 | e2e(server) 9749.0 / 10410.2 | frontend+IPC 2572.3 / 3619.8
  tokens: prompt 5438, generated 262.4, cached prompt tokens mean 4016 (max 4016), time/output token 16.1 ms
  API-server spread: 12 processes, requests per process [14, 14, 12, 12, 11, 11, 11, 10, 10, 8, 8, 7]
  client latency p50 9.75s p95 10.41s (128 ok), throughput per run 3.0, 2.8 req/s
  server CPU per request (cpu-s): api 0.160, engine 0.354, mps 0.000, vllm_main 0.000; total 0.514; pod cgroup 0.520

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 168.2 | 247.7 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 164.2 | 247.0 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.2 | 8.8 | - | - |
| 2-4 video load_bytes total | 1.00 | 156.1 | 229.3 | 40.2 | - |
| 2 remux TS->fMP4 | 1.00 | 47.9 | 76.8 | 15.1 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 25.2 | 56.4 | 1.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 57.5 | 112.4 | 22.3 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 2.2 | 0.3 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 161.7 | 331.4 | - | - |
| 5-6 processor (mm thread) | 1.00 | 62.8 | 100.5 | 65.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 53.9 | 86.6 | 56.8 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 47.1 | 79.3 | 49.7 | - |
| hash (blake3) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 1.0 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.08 | 232.7 | 473.5 | 206.6 | 225.8 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.08 | 184.8 | 400.3 | 162.1 | 173.6 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 10, items/call mean 12.8 max 22; vision calls 10, videos/call mean 12.8 max 22
  engine per request (p50 / p95 ms): queued 0.1 / 0.1 | prefill 1311.0 / 1591.5 | decode 819.5 / 21879.5 | e2e(server) 2695.3 / 23919.2 | frontend+IPC 929.2 / 1086.6
  tokens: prompt 5356, generated 517.3, cached prompt tokens mean 4016 (max 4016), time/output token 14.0 ms
  API-server spread: 12 processes, requests per process [15, 13, 12, 11, 11, 11, 11, 11, 10, 10, 8, 5]
  client latency p50 2.71s p95 23.92s (128 ok), throughput per run 2.7, 3.0 req/s
  server CPU per request (cpu-s): api 0.196, engine 0.361, mps 0.000, vllm_main 0.000; total 0.557; pod cgroup 0.563

# qwen-live360-nvdec-async

## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 38.6 | 41.5 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 30.3 | 32.7 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 1.7 | 2.7 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 27.1 | 30.2 | 15.5 | 17.4 | - |
| 2 remux TS->fMP4 | 1.00 | 4.3 | 4.9 | 3.9 | 5.1 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.9 | 2.2 | 1.3 | 2.0 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 19.5 | 22.9 | 9.1 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 0.3 | 0.3 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 7.3 | 8.0 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 4.4 | 5.5 | 4.5 | 4.5 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 4.0 | 5.0 | 4.0 | 4.1 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 58.2 | 85.5 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 57.8 | 85.2 | 60.9 | 60.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 49.7 | 75.9 | 52.1 | 52.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 43.0 | 69.0 | 45.0 | 45.0 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.4 | 2.6 | 2.4 | 2.4 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.3 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 72.8 | 74.7 | 73.0 | - | 72.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 36.6 | 37.8 | 36.7 | - | 36.3 |
| 7a sound encoder (per call) | 1.00 | 32.9 | 33.8 | 33.1 | - | 32.9 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.6 | prefill 165.7 / 168.3 | decode 1678.8 / 1866.0 | e2e(server) 1962.6 / 2150.0 | frontend+IPC 113.8 / 140.3
  tokens: prompt 5438, generated 240.8, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 5 processes, requests per process [9, 9, 3, 2, 1]
  client latency p50 1.97s p95 2.15s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.190, engine 1.892, mps 0.001, vllm_main 0.000; total 2.084; pod cgroup 2.143

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 33.0 | 35.1 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 31.9 | 34.1 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 2.2 | 2.9 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 28.1 | 31.3 | 15.2 | 17.3 | - |
| 2 remux TS->fMP4 | 1.00 | 4.5 | 4.8 | 4.1 | 5.4 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.9 | 2.1 | 1.3 | 2.0 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 21.1 | 23.1 | 8.7 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.2 | 0.3 | 0.3 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 57.7 | 83.3 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 57.3 | 82.9 | 58.6 | 58.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 48.9 | 74.9 | 51.3 | 51.3 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 43.2 | 68.9 | 45.3 | 45.4 | - |
| hash (blake3) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 39.5 | 43.4 | 40.0 | - | 39.4 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 36.5 | 40.6 | 37.1 | - | 36.3 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.7 | prefill 128.5 / 135.2 | decode 1667.6 / 1780.2 | e2e(server) 1903.5 / 2032.2 | frontend+IPC 106.0 / 133.9
  tokens: prompt 5356, generated 238.6, cached prompt tokens mean 4016 (max 4016), time/output token 7.0 ms
  API-server spread: 7 processes, requests per process [15, 3, 2, 1, 1, 1, 1]
  client latency p50 1.91s p95 2.03s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.181, engine 1.838, mps 0.001, vllm_main 0.000; total 2.020; pod cgroup 2.035

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 176.3 | 1101.4 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 159.1 | 1092.2 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.7 | 10.1 | - | - |
| 2-4 video load_bytes total | 1.00 | 146.9 | 215.3 | 38.9 | - |
| 2 remux TS->fMP4 | 1.00 | 46.4 | 74.5 | 14.5 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 22.5 | 58.4 | 1.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 56.1 | 99.1 | 20.7 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 2.9 | 0.3 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 11.8 | 22.3 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 8.3 | 18.8 | 6.9 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.2 | 0.7 | 0.1 | - |
| 6b'' PyAV AAC decode | 1.00 | 7.7 | 17.8 | 6.4 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 161.6 | 377.7 | - | - |
| 5-6 processor (mm thread) | 1.00 | 68.0 | 108.9 | 67.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 56.6 | 94.6 | 57.5 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 48.4 | 85.7 | 49.6 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.9 | 4.2 | 2.4 | - |
| hash (blake3) | 2.00 | 0.2 | 0.5 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.4 | 1.0 | 0.4 | - |
| 7 encoder call (all items in the step) | 0.07 | 775.6 | 2153.6 | 1006.1 | 775.6 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 35.5 | 42.3 | 35.9 | 35.3 |
| 7a sound encoder (per call) | 1.00 | 32.1 | 36.9 | 32.4 | 32.1 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 9, items/call mean 28.4 max 60; vision calls 128, videos/call mean 1.0 max 1; sound calls 128, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.1 / 0.1 | prefill 3187.9 / 3494.2 | decode 7726.4 / 10135.4 | e2e(server) 13251.3 / 13679.0 | frontend+IPC 2498.8 / 3017.4
  tokens: prompt 5438, generated 231.1, cached prompt tokens mean 4016 (max 4016), time/output token 33.2 ms
  API-server spread: 12 processes, requests per process [15, 13, 13, 12, 12, 12, 11, 10, 9, 9, 7, 5]
  client latency p50 13.26s p95 13.68s (128 ok), throughput per run 4.6, 4.7 req/s
  server CPU per request (cpu-s): api 0.152, engine 0.220, mps 0.000, vllm_main 0.000; total 0.373; pod cgroup 0.378

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 152.3 | 236.2 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 150.9 | 235.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.4 | 10.0 | - | - |
| 2-4 video load_bytes total | 1.00 | 140.3 | 210.7 | 38.9 | - |
| 2 remux TS->fMP4 | 1.00 | 42.3 | 76.2 | 13.9 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 4.7 | 87.6 | 1.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 56.3 | 106.9 | 22.1 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 3.6 | 0.4 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 149.1 | 376.8 | - | - |
| 5-6 processor (mm thread) | 1.00 | 66.0 | 111.1 | 66.3 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 56.8 | 96.8 | 57.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 49.9 | 89.6 | 50.9 | - |
| hash (blake3) | 1.00 | 0.2 | 0.4 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.08 | 256.3 | 303.5 | 187.2 | 244.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.08 | 202.1 | 240.9 | 147.2 | 186.5 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 10, items/call mean 12.8 max 20; vision calls 10, videos/call mean 12.8 max 20
  engine per request (p50 / p95 ms): queued 0.1 / 0.1 | prefill 1190.9 / 1444.5 | decode 7905.7 / 8732.5 | e2e(server) 9948.7 / 10260.3 | frontend+IPC 820.2 / 920.0
  tokens: prompt 5356, generated 238.3, cached prompt tokens mean 4016 (max 4016), time/output token 33.7 ms
  API-server spread: 12 processes, requests per process [15, 14, 13, 12, 12, 11, 9, 9, 9, 8, 8, 8]
  client latency p50 9.95s p95 10.26s (128 ok), throughput per run 6.2, 6.1 req/s
  server CPU per request (cpu-s): api 0.141, engine 0.167, mps 0.000, vllm_main 0.000; total 0.308; pod cgroup 0.313

# qwen-live360-nvdec-sortmm

## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 39.0 | 41.1 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 30.7 | 33.3 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 1.7 | 2.8 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 27.4 | 29.9 | 15.6 | 18.1 | - |
| 2 remux TS->fMP4 | 1.00 | 4.4 | 5.3 | 4.1 | 5.9 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.8 | 2.0 | 1.2 | 1.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 19.9 | 22.6 | 9.2 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 0.3 | 0.3 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 6.7 | 8.2 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 4.3 | 4.8 | 4.3 | 4.3 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.1 | 0.2 | 0.1 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 3.8 | 4.3 | 3.9 | 3.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 49.6 | 76.1 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 49.2 | 75.8 | 52.5 | 52.6 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 41.0 | 67.0 | 44.6 | 44.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 34.0 | 60.5 | 37.9 | 37.9 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.3 | 2.8 | 2.4 | 2.4 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.4 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 77.1 | 82.8 | 77.8 | - | 77.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 38.9 | 42.2 | 39.1 | - | 38.7 |
| 7a sound encoder (per call) | 1.00 | 35.1 | 37.7 | 35.6 | - | 35.1 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.8 | prefill 174.5 / 186.7 | decode 1658.7 / 1891.1 | e2e(server) 1930.5 / 2184.1 | frontend+IPC 106.9 / 128.9
  tokens: prompt 5438, generated 226.0, cached prompt tokens mean 4016 (max 4016), time/output token 7.2 ms
  API-server spread: 5 processes, requests per process [9, 8, 3, 2, 2]
  client latency p50 1.93s p95 2.19s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.169, engine 1.848, mps 0.000, vllm_main 0.000; total 2.017; pod cgroup 2.034

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 29.7 | 32.6 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 28.8 | 31.5 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 1.5 | 2.5 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 26.4 | 29.1 | 15.9 | 17.9 | - |
| 2 remux TS->fMP4 | 1.00 | 4.4 | 4.8 | 4.1 | 5.4 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.9 | 2.1 | 1.3 | 2.0 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 18.7 | 22.1 | 9.3 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 0.3 | 0.3 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 51.5 | 62.0 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 51.3 | 61.8 | 51.0 | 51.1 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 45.0 | 55.5 | 44.5 | 44.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 39.8 | 49.7 | 39.0 | 39.1 | - |
| hash (blake3) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 42.1 | 44.5 | 42.2 | - | 42.0 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 39.0 | 41.5 | 39.2 | - | 38.8 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.5 | prefill 135.0 / 141.8 | decode 1675.2 / 1836.2 | e2e(server) 1917.2 / 2061.7 | frontend+IPC 98.9 / 107.2
  tokens: prompt 5356, generated 232.2, cached prompt tokens mean 4016 (max 4016), time/output token 7.2 ms
  API-server spread: 1 processes, requests per process [24]
  client latency p50 1.92s p95 2.06s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.145, engine 1.847, mps 0.000, vllm_main 0.000; total 1.992; pod cgroup 2.006

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 176.4 | 248.3 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 156.9 | 227.8 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.5 | 8.6 | - | - |
| 2-4 video load_bytes total | 1.00 | 149.1 | 214.0 | 39.0 | - |
| 2 remux TS->fMP4 | 1.00 | 45.9 | 73.5 | 15.0 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 18.2 | 94.2 | 1.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 57.5 | 106.1 | 20.9 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 2.5 | 0.5 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 11.8 | 18.4 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 8.5 | 14.2 | 6.4 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.1 | 0.6 | 0.1 | - |
| 6b'' PyAV AAC decode | 1.00 | 7.7 | 12.8 | 5.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 147.4 | 320.4 | - | - |
| 5-6 processor (mm thread) | 1.00 | 63.5 | 91.9 | 62.8 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 55.3 | 79.8 | 54.0 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 46.8 | 71.4 | 46.3 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.8 | 4.8 | 2.4 | - |
| hash (blake3) | 2.00 | 0.2 | 0.5 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.4 | 0.7 | 0.4 | - |
| 7 encoder call (all items in the step) | 0.07 | 281.2 | 590.8 | 266.6 | 281.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.07 | 180.7 | 380.4 | 169.2 | 176.2 |
| 7a sound encoder (per call) | 0.07 | 55.2 | 83.4 | 53.0 | 55.2 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 9, items/call mean 28.4 max 68; vision calls 9, videos/call mean 14.2 max 34; sound calls 9, clips/call mean 14.2 max 34
  engine per request (p50 / p95 ms): queued 0.1 / 0.1 | prefill 1323.8 / 1610.2 | decode 8182.4 / 9142.0 | e2e(server) 10460.4 / 10979.9 | frontend+IPC 1066.4 / 1565.0
  tokens: prompt 5438, generated 232.3, cached prompt tokens mean 4016 (max 4016), time/output token 35.1 ms
  API-server spread: 12 processes, requests per process [13, 13, 12, 12, 12, 11, 11, 10, 10, 9, 9, 6]
  client latency p50 10.46s p95 10.98s (128 ok), throughput per run 6.0, 5.8 req/s
  server CPU per request (cpu-s): api 0.148, engine 0.177, mps 0.000, vllm_main 0.000; total 0.325; pod cgroup 0.329

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 157.9 | 244.2 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 151.2 | 243.0 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.6 | 9.9 | - | - |
| 2-4 video load_bytes total | 1.00 | 138.9 | 224.4 | 39.1 | - |
| 2 remux TS->fMP4 | 1.00 | 50.5 | 69.7 | 14.8 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 28.8 | 57.3 | 1.2 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 54.6 | 114.6 | 21.5 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 2.4 | 0.3 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 141.6 | 285.8 | - | - |
| 5-6 processor (mm thread) | 1.00 | 54.2 | 89.0 | 57.2 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 46.9 | 79.0 | 50.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 40.2 | 71.6 | 43.5 | - |
| hash (blake3) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.07 | 202.7 | 451.6 | 214.1 | 202.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.07 | 166.0 | 368.5 | 172.5 | 162.2 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 9, items/call mean 14.2 max 32; vision calls 9, videos/call mean 14.2 max 32
  engine per request (p50 / p95 ms): queued 0.1 / 0.1 | prefill 1194.4 / 1312.9 | decode 8368.7 / 9123.1 | e2e(server) 10372.7 / 10707.0 | frontend+IPC 1014.6 / 1261.0
  tokens: prompt 5356, generated 236.1, cached prompt tokens mean 4016 (max 4016), time/output token 35.7 ms
  API-server spread: 12 processes, requests per process [15, 14, 13, 13, 12, 12, 11, 9, 9, 8, 8, 4]
  client latency p50 10.38s p95 10.71s (128 ok), throughput per run 5.9, 6.0 req/s
  server CPU per request (cpu-s): api 0.133, engine 0.172, mps 0.000, vllm_main 0.000; total 0.305; pod cgroup 0.309

# qwen-live360-nvdec-sortmm-async

## seq-av: 24 requests (1 run(s)), concurrency 1, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 37.5 | 40.7 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 29.5 | 32.9 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 1.6 | 2.3 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 26.4 | 29.4 | 15.7 | 18.1 | - |
| 2 remux TS->fMP4 | 1.00 | 4.3 | 4.9 | 4.0 | 5.7 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.8 | 2.0 | 1.2 | 1.9 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 19.6 | 22.4 | 9.3 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.2 | 0.3 | 0.2 | - | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 6.6 | 7.6 | - | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 4.3 | 4.8 | 4.3 | 4.3 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| 6b'' PyAV AAC decode | 1.00 | 3.8 | 4.3 | 3.9 | 3.9 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 52.2 | 73.5 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 51.9 | 73.1 | 51.7 | 51.7 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 45.2 | 64.8 | 44.0 | 44.1 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 38.3 | 58.2 | 37.1 | 37.1 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.2 | 2.3 | 2.2 | 2.2 | - |
| hash (blake3) | 2.00 | 0.1 | 0.2 | 0.1 | 0.1 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.3 | 0.3 | 0.3 | 0.3 | - |
| 7 encoder call (all items in the step) | 1.00 | 76.7 | 78.0 | 76.5 | - | 76.7 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 38.6 | 39.4 | 38.5 | - | 38.4 |
| 7a sound encoder (per call) | 1.00 | 35.2 | 36.1 | 35.2 | - | 35.1 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 2.0 max 2; vision calls 24, videos/call mean 1.0 max 1; sound calls 24, clips/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.6 | prefill 173.5 / 176.3 | decode 1612.5 / 1817.4 | e2e(server) 1896.1 / 2108.5 | frontend+IPC 105.6 / 125.9
  tokens: prompt 5438, generated 228.4, cached prompt tokens mean 4016 (max 4016), time/output token 7.2 ms
  API-server spread: 4 processes, requests per process [17, 4, 2, 1]
  client latency p50 1.90s p95 2.11s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.163, engine 1.844, mps 0.001, vllm_main 0.000; total 2.008; pod cgroup 2.023

## seq-v: 24 requests (1 run(s)), concurrency 1, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | process-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 30.9 | 34.2 | - | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 29.9 | 32.9 | - | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 1.8 | 2.9 | - | - | - |
| 2-4 video load_bytes total | 1.00 | 26.5 | 29.5 | 15.9 | 17.9 | - |
| 2 remux TS->fMP4 | 1.00 | 4.4 | 4.9 | 4.1 | 5.3 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 1.9 | 2.0 | 1.3 | 2.0 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 19.1 | 22.0 | 9.4 | - | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 0.3 | 0.3 | - | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 43.0 | 63.4 | - | - | - |
| 5-6 processor (mm thread) | 1.00 | 42.5 | 63.0 | 44.4 | 44.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 37.2 | 57.6 | 38.6 | 38.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 31.8 | 51.5 | 32.8 | 32.8 | - |
| hash (blake3) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.2 | 0.2 | 0.2 | - |
| 7 encoder call (all items in the step) | 1.00 | 41.2 | 43.1 | 41.4 | - | 41.2 |
| 7v vision encoder (per call; 1 video/call unless batched) | 1.00 | 38.6 | 40.5 | 38.8 | - | 38.4 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 24, items/call mean 1.0 max 1; vision calls 24, videos/call mean 1.0 max 1
  engine per request (p50 / p95 ms): queued 0.0 / 1.5 | prefill 135.9 / 140.9 | decode 1759.4 / 1896.6 | e2e(server) 1974.5 / 2127.6 | frontend+IPC 92.9 / 111.4
  tokens: prompt 5356, generated 240.4, cached prompt tokens mean 4016 (max 4016), time/output token 7.3 ms
  API-server spread: 6 processes, requests per process [14, 3, 3, 2, 1, 1]
  client latency p50 1.98s p95 2.13s (24 ok), throughput per run 0.5 req/s
  server CPU per request (cpu-s): api 0.160, engine 1.922, mps 0.000, vllm_main 0.000; total 2.082; pod cgroup 2.096

## burst-av: 128 requests (2 run(s)), concurrency 64, audio+video
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 173.7 | 259.9 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 153.5 | 249.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 2.00 | 2.6 | 8.4 | - | - |
| 2-4 video load_bytes total | 1.00 | 142.3 | 220.9 | 39.7 | - |
| 2 remux TS->fMP4 | 1.00 | 50.6 | 82.3 | 15.1 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 18.8 | 65.1 | 1.4 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 53.4 | 99.6 | 21.4 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 2.4 | 0.4 | - |
| 6a fetch_audio total (2nd download + audio decode) | 1.00 | 11.0 | 18.5 | - | - |
| 6b audio decode (soundfile try + PyAV) | 1.00 | 7.9 | 13.3 | 6.2 | - |
| 6b' soundfile attempt (fails on TS) | 1.00 | 0.2 | 0.8 | 0.1 | - |
| 6b'' PyAV AAC decode | 1.00 | 7.3 | 12.5 | 5.8 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 158.5 | 383.6 | - | - |
| 5-6 processor (mm thread) | 1.00 | 64.1 | 100.9 | 64.9 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 55.7 | 87.5 | 55.7 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 45.4 | 78.1 | 47.7 | - |
| 6c resample to 16 kHz | 1.00 | 0.0 | 0.0 | 0.0 | - |
| 6d mel features (CPU) | 1.00 | 2.8 | 4.6 | 2.4 | - |
| hash (blake3) | 2.00 | 0.2 | 0.5 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.5 | 0.8 | 0.4 | - |
| 7 encoder call (all items in the step) | 0.07 | 229.3 | 557.9 | 272.1 | 229.3 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.07 | 147.1 | 436.1 | 183.6 | 143.4 |
| 7a sound encoder (per call) | 0.07 | 53.5 | 79.9 | 50.5 | 53.6 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  audio_decode: {'samples': 98304, 'sr': 16000}
  d2h: {'bytes': 8294400}
  encoder calls: 9, items/call mean 28.4 max 68; vision calls 9, videos/call mean 14.2 max 34; sound calls 9, clips/call mean 14.2 max 34
  engine per request (p50 / p95 ms): queued 0.1 / 0.1 | prefill 1405.2 / 1760.2 | decode 7952.4 / 8985.0 | e2e(server) 10443.7 / 11002.4 | frontend+IPC 1308.4 / 1493.8
  tokens: prompt 5438, generated 229.2, cached prompt tokens mean 4016 (max 4016), time/output token 35.0 ms
  API-server spread: 12 processes, requests per process [16, 14, 13, 12, 12, 10, 10, 9, 9, 9, 8, 6]
  client latency p50 10.45s p95 11.01s (128 ok), throughput per run 5.8, 6.0 req/s
  server CPU per request (cpu-s): api 0.150, engine 0.175, mps 0.000, vllm_main 0.000; total 0.325; pod cgroup 0.329

## burst-v: 128 requests (2 run(s)), concurrency 64, video-only
| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | GPU ms/call |
|---|---|---|---|---|---|
| 1-4,6a frontend: chat parse + media fetch (video+audio) | 1.00 | 160.3 | 1106.1 | - | - |
| 1-4 fetch_video total (download + decode, incl. thread-pool wait) | 1.00 | 158.8 | 1105.1 | - | - |
| 1 download (per HTTP GET; 2 per request with audio) | 1.00 | 4.9 | 1025.3 | - | - |
| 2-4 video load_bytes total | 1.00 | 138.5 | 208.4 | 40.2 | - |
| 2 remux TS->fMP4 | 1.00 | 42.1 | 77.5 | 14.5 | - |
| 3a NVDEC decoder reconfigure + stream scan | 1.00 | 20.1 | 68.1 | 1.3 | - |
| 3b NVDEC decode of sampled frames | 1.00 | 57.6 | 96.3 | 22.7 | - |
| 4 GPU->pinned host copy (+stack/permute) | 1.00 | 0.3 | 2.1 | 0.4 | - |
| 5-6 processor incl. wait for the 1 mm thread | 1.00 | 138.6 | 315.2 | - | - |
| 5-6 processor (mm thread) | 1.00 | 60.9 | 94.3 | 62.4 | - |
| 5-6 HF processor call (video + audio + tokenize) | 1.00 | 52.7 | 83.6 | 54.6 | - |
| 5 resize+normalize+patchify (CPU) | 1.00 | 45.2 | 76.5 | 47.9 | - |
| hash (blake3) | 1.00 | 0.2 | 0.4 | 0.2 | - |
| msgpack encode to engine (>=1 MB msgs) | 1.00 | 0.2 | 0.3 | 0.2 | - |
| 7 encoder call (all items in the step) | 0.07 | 210.2 | 400.6 | 197.9 | 210.1 |
| 7v vision encoder (per call; 1 video/call unless batched) | 0.07 | 176.7 | 339.6 | 167.2 | 172.3 |
  video_resize_norm: {'in': [1, 12, 3, 360, 640], 'out': [5280, 1536], 'grid_thw': [[6, 22, 40]]}
  video_decode_total: {'frames': [12, 360, 640, 3], 'backend': 'pynvvideocodec'}
  d2h: {'bytes': 8294400}
  encoder calls: 9, items/call mean 14.2 max 28; vision calls 9, videos/call mean 14.2 max 28
  engine per request (p50 / p95 ms): queued 0.0 / 0.1 | prefill 1151.6 / 1434.5 | decode 8362.8 / 9166.3 | e2e(server) 10342.2 / 10723.9 | frontend+IPC 780.9 / 1432.3
  tokens: prompt 5356, generated 238.5, cached prompt tokens mean 4016 (max 4016), time/output token 35.5 ms
  API-server spread: 12 processes, requests per process [15, 14, 13, 12, 11, 11, 10, 10, 9, 8, 8, 7]
  client latency p50 10.35s p95 10.73s (128 ok), throughput per run 5.9, 5.8 req/s
  server CPU per request (cpu-s): api 0.140, engine 0.176, mps 0.000, vllm_main 0.000; total 0.316; pod cgroup 0.320
