"""Decode-only benchmark through vLLM's VideoMediaIO: pynvvideocodec (MPEG-TS remux + decoder-slot path) vs opencv.

Usage: CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 python vod_loader_bench.py <clip_dir_or_file> <fps> [n_clips] [threads]
Reports per-clip decode latency (median) and throughput with N threads, for both backends.
"""
import glob, os, statistics, sys, time, warnings
warnings.filterwarnings("ignore")
from concurrent.futures import ThreadPoolExecutor
import torch
from vllm.multimodal.video import PyNvVideoCodecVideoBackend as B
from vllm.multimodal.media.video import VideoMediaIO
from vllm.multimodal.media.image import ImageMediaIO

target = sys.argv[1]; fps = float(sys.argv[2]); n_clips = int(sys.argv[3]) if len(sys.argv) > 3 else 16; threads = int(sys.argv[4]) if len(sys.argv) > 4 else 8
paths = sorted(glob.glob(os.path.join(target, "*.mp4")) + glob.glob(os.path.join(target, "*.ts"))) if os.path.isdir(target) else [target]
paths = (paths * ((n_clips // len(paths)) + 1))[:n_clips]
blobs = [open(p, "rb").read() for p in paths]
print(f"clips={len(blobs)} from {target} avg={sum(map(len, blobs))/len(blobs)/1e6:.1f} MB fps={fps} threads={threads}")

HW = int(os.environ.get("HW_DECODERS", "2"))
BACKENDS = os.environ.get("BACKENDS", "pynvvideocodec,opencv").split(",")
B._DEVICE_INDEX = 0; B._configure_decoder_slots(HW)
ios = {n: VideoMediaIO(ImageMediaIO(), **{"backend": n, "fps": fps}) for n in BACKENDS}

def frames_of(out):
    m = getattr(out, "media", out); fr = m[0] if isinstance(m, tuple) else m
    return getattr(fr, "shape", None)

def safe(vio, b):
    try:
        return vio.load_bytes(b), None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:60]}"

for name, vio in ios.items():
    safe(vio, blobs[0]); torch.cuda.synchronize()
    lat, errs, shape = [], 0, None
    for b in blobs[: min(8, len(blobs))]:
        t0 = time.perf_counter(); out, err = safe(vio, b); torch.cuda.synchronize()
        if err: errs += 1; last_err = err; continue
        lat.append(time.perf_counter() - t0); shape = frames_of(out)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(threads) as ex: res = list(ex.map(lambda b: safe(vio, b), blobs))
    torch.cuda.synchronize(); wall = time.perf_counter() - t0
    nerr = sum(1 for _, e in res if e)
    tag = f"{name}" + (f"[slots={HW}]" if name == "pynvvideocodec" else "")
    med = statistics.median(lat) * 1000 if lat else float("nan")
    print(f"  {tag:24s} frames={shape}  sequential median={med:7.1f} ms/clip  | {threads} threads: {(len(blobs)-nerr)/wall:6.1f} clips/s ({wall/len(blobs)*1000:.0f} ms/clip)  errors={errs}+{nerr}" + (f"  last_err={last_err}" if errs or nerr else ""))
