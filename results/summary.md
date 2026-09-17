
### A. raw decode, MPS off


`shot_010s_000.mp4 1920x1080 frames=307 fps=29.97 reps=3 mps=off`

| backend | procs | agg frames/s | per-proc frames/s | CPU cores | frames/s per core | × realtime |
|---|---|---|---|---|---|---|
| cv2 | 1 | 694 | 694 | 6.4 | 109 | 23.2 |
| nvdec | 1 | 2188 | 2188 | 0.2 | 12518 | 73.0 |
| cv2 | 2 | 1325 | 666 | 13.0 | 102 | 44.2 |
| nvdec | 2 | 2630 | 1320 | 1.7 | 1519 | 87.8 |
| cv2 | 4 | 2431 | 620 | 25.7 | 95 | 81.1 |
| nvdec | 4 | 2290 | 573 | 4.0 | 575 | 76.4 |
| cv2 | 8 | 4763 | 609 | 57.3 | 83 | 158.9 |
| nvdec | 8 | 2258 | 283 | 8.0 | 283 | 75.3 |
| cv2 | 16 | 2802 | 180 | 62.9 | 45 | 93.5 |
| nvdec | 16 | 2227 | 139 | 16.0 | 140 | 74.3 |

`seg6.ts 640x360 frames=182 fps=29.97 reps=5 mps=off`

| backend | procs | agg frames/s | per-proc frames/s | CPU cores | frames/s per core | × realtime |
|---|---|---|---|---|---|---|
| cv2 | 1 | 1616 | 1616 | 2.7 | 606 | 53.9 |
| nvdec | 1 | 8181 | 8181 | 0.5 | 16476 | 273.0 |
| cv2 | 4 | 7731 | 2094 | 12.7 | 610 | 258.0 |
| nvdec | 4 | 2320 | 581 | 4.0 | 581 | 77.4 |
| cv2 | 8 | 19690 | 2557 | 33.9 | 581 | 657.0 |
| nvdec | 8 | 2318 | 290 | 8.0 | 290 | 77.4 |
| cv2 | 16 | 32033 | 2064 | 62.5 | 513 | 1068.8 |
| nvdec | 16 | 2317 | 145 | 16.0 | 145 | 77.3 |

### A'. raw decode NVDEC, MPS on


`shot_010s_000.mp4 1920x1080 frames=307 fps=29.97 reps=3 mps=on`

| backend | procs | agg frames/s | per-proc frames/s | CPU cores | frames/s per core | × realtime |
|---|---|---|---|---|---|---|
| nvdec | 1 | 2189 | 2189 | 0.2 | 13496 | 73.0 |
| nvdec | 2 | 4274 | 2140 | 0.3 | 12535 | 142.6 |
| nvdec | 4 | 8242 | 2065 | 0.8 | 10881 | 275.0 |
| nvdec | 8 | 11823 | 1486 | 1.3 | 8915 | 394.5 |
| nvdec | 16 | 12178 | 774 | 2.0 | 6086 | 406.3 |

`seg6.ts 640x360 frames=182 fps=29.97 reps=5 mps=on`

| backend | procs | agg frames/s | per-proc frames/s | CPU cores | frames/s per core | × realtime |
|---|---|---|---|---|---|---|
| nvdec | 1 | 8681 | 8681 | 0.6 | 14129 | 289.6 |
| nvdec | 4 | 25772 | 6886 | 2.2 | 11766 | 859.9 |
| nvdec | 8 | 35628 | 5841 | 3.5 | 10063 | 1188.8 |
| nvdec | 16 | 51202 | 3549 | 6.3 | 8082 | 1708.4 |

### B. vLLM loader decode stage (sampled frames), 3 reps

Median per-clip latency (sequential) and 8-thread single-process throughput; mean ± range over 3 repetitions.

| Clip set | Frames | CPU (opencv) ms | NVDEC (pynvvideocodec) ms | Speed-up | CPU clips/s | NVDEC clips/s |
|---|---|---|---|---|---|---|
| enc_10s @ 1.0 fps | 10 | 258 (248–272) | 132 (130–133) | 2.0× | 18.8 | 9.9 |
| enc_30s @ 1.0 fps | 31 | 688 (680–702) | 350 (348–352) | 2.0× | 6.9 | 3.7 |
| enc_120s @ 1.0 fps | 32 | 2132 (2068–2221) | 404 (398–409) | 5.3× | 2.2 | 3.2 |
| seg6.ts @ 2.0 fps | 12 | 32 (29–34) | 28 (26–31) | 1.1× | 115.4 | 49.9 |

### C. E2E Nemotron 3 Nano Omni, NVDEC + MPS

Mean over repetitions (n = 3). Latency in seconds, CPU = server cgroup cpu-s per request, dec% = peak NVDEC utilization sampled.

| Workload | N | Config | ok/err | req/s | p50 | p95 | max | prompt tok | CPU s/req | dec% |
|---|---|---|---|---|---|---|---|---|---|---|
| live-ts-6s-360p-audio | 64 | nvdec-mps | 192/0 | 7.9 | 5.1 | 7.8 | 8.0 | 1783 | 0.29 | 24 |
| live-ts-6s-360p-video | 64 | nvdec-mps | 192/0 | 28.8 | 2.1 | 2.2 | 2.2 | 1705 | 0.07 | 21 |
| vod-10s-1080p | 64 | nvdec-mps | 192/0 | 7.9 | 7.7 | 11.7 | 12.2 | 1622 | 0.43 | 22 |
| vod-30s-1080p | 32 | nvdec-mps | 96/0 | 3.0 | 9.8 | 16.3 | 16.6 | 4533 | 0.97 | 28 |
| vod-120s-1080p | 8 | nvdec-mps | 24/0 | 0.6 | 12.9 | 18.3 | 18.3 | 17363 | 3.42 | 28 |
| vod-10s-1080p-audio | 64 | nvdec-mps | 192/0 | 2.5 | 14.2 | 23.4 | 24.3 | 1769 | 0.93 | 21 |

### C. E2E Nemotron 3 Nano Omni, CPU (OpenCV)

Mean over repetitions (n = 3). Latency in seconds, CPU = server cgroup cpu-s per request, dec% = peak NVDEC utilization sampled.

| Workload | N | Config | ok/err | req/s | p50 | p95 | max | prompt tok | CPU s/req | dec% |
|---|---|---|---|---|---|---|---|---|---|---|
| live-ts-6s-360p-audio | 64 | cpu-opencv | 192/0 | 7.8 | 5.0 | 7.9 | 8.1 | 1770 | 0.48 | 0 |
| live-ts-6s-360p-video | 64 | cpu-opencv | 192/0 | 32.4 | 1.9 | 2.0 | 2.0 | 1692 | 0.23 | 0 |
| vod-10s-1080p | 64 | cpu-opencv | 192/0 | 6.7 | 8.9 | 13.3 | 13.9 | 1627 | 3.34 | 0 |
| vod-30s-1080p | 32 | cpu-opencv | 96/0 | 2.6 | 14.3 | 20.4 | 21.1 | 4533 | 9.25 | 0 |
| vod-120s-1080p | 8 | cpu-opencv | 24/0 | 0.5 | 18.2 | 24.1 | 24.1 | 17363 | 36.45 | 0 |
| vod-10s-1080p-audio | 64 | cpu-opencv | 192/0 | 1.9 | 18.0 | 30.5 | 32.4 | 1773 | 3.97 | 0 |

### ALL DONE

