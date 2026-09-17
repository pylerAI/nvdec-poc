"""Raw decode throughput: NVDEC (PyNvVideoCodec, reused decoder) vs CPU (OpenCV/FFmpeg), all frames.

Usage: python raw_decode_bench.py <clip> [--procs N ...] [--reps R] [--backends cv2,nvdec]
Each worker process decodes the whole clip R times. Workers wait on a barrier after warm-up so the
timed window excludes interpreter/CUDA start-up. Reports aggregate frames/s (frames / slowest worker),
per-worker frames/s, CPU seconds and CPU cores consumed during the window.
"""
import argparse, multiprocessing as mp, os, resource, time


def timed(loop, reps, barrier, q):
    barrier.wait()
    r0 = resource.getrusage(resource.RUSAGE_SELF); t0 = time.perf_counter()
    n = sum(loop() for _ in range(reps))
    dt = time.perf_counter() - t0; r1 = resource.getrusage(resource.RUSAGE_SELF)
    q.put((n, dt, (r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime)))


def worker_nvdec(clip, reps, barrier, q):
    import PyNvVideoCodec as nvc, torch
    dmx = nvc.CreateDemuxer(filename=clip)
    dec = nvc.CreateDecoder(gpuid=0, codec=dmx.GetNvCodecId(), usedevicememory=True, outputColorType=nvc.OutputColorType.RGB)

    def loop():
        n = 0
        for pkt in nvc.CreateDemuxer(filename=clip):
            for _ in dec.Decode(pkt): n += 1
        torch.cuda.synchronize(); return n
    loop()  # warm-up (first decode carries the ~300 ms engine/context init)
    timed(loop, reps, barrier, q)


def worker_cv2(clip, reps, barrier, q):
    import cv2

    def loop():
        cap = cv2.VideoCapture(clip); n = 0
        while cap.read()[0]: n += 1
        cap.release(); return n
    loop()
    timed(loop, reps, barrier, q)


def run(backend, clip, procs, reps):
    fn = worker_nvdec if backend == "nvdec" else worker_cv2
    ctx = mp.get_context("spawn"); q = ctx.Queue(); barrier = ctx.Barrier(procs)
    ps = [ctx.Process(target=fn, args=(clip, reps, barrier, q)) for _ in range(procs)]
    for p in ps: p.start()
    res = [q.get() for _ in ps]
    for p in ps: p.join()
    frames = sum(r[0] for r in res); wall = max(r[1] for r in res); cpu = sum(r[2] for r in res)
    return frames, wall, cpu, [r[0] / r[1] for r in res]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("clip"); ap.add_argument("--procs", type=int, nargs="+", default=[1, 4, 8])
    ap.add_argument("--reps", type=int, default=3); ap.add_argument("--backends", default="cv2,nvdec"); a = ap.parse_args()
    import cv2
    cap = cv2.VideoCapture(a.clip); w, h, nf, fps = int(cap.get(3)), int(cap.get(4)), int(cap.get(7)), cap.get(5); cap.release()
    mps = "on" if os.popen("pgrep -c nvidia-cuda-mps").read().strip() not in ("", "0") else "off"
    print(f"clip={os.path.basename(a.clip)} {w}x{h} frames={nf} fps={fps:.2f} reps={a.reps} mps={mps}")
    print(f"{'backend':7s} {'procs':>5s} {'agg frames/s':>13s} {'per-proc frames/s':>18s} {'cpu-s':>7s} {'cpu cores':>10s} {'frames/s/core':>14s} {'x realtime':>11s}")
    for procs in a.procs:
        for b in a.backends.split(","):
            frames, wall, cpu, pp = run(b, a.clip, procs, a.reps)
            cores = cpu / wall
            print(f"{b:7s} {procs:5d} {frames/wall:13.0f} {sum(pp)/len(pp):18.0f} {cpu:7.1f} {cores:10.1f} {frames/wall/max(cores,1e-3):14.0f} {frames/wall/fps:11.1f}", flush=True)
