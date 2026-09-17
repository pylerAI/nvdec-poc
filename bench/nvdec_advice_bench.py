"""NVIDIA-advice microbench on PyNvVideoCodec 2.1.1: seek, decoder reuse, remux, concurrency.

Usage: CUDA_VISIBLE_DEVICES=0 python nvdec_advice_bench.py [/path/clip.ts] [fps=2]
"""
import io, os, statistics, subprocess, sys, tempfile, time, traceback
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch
import PyNvVideoCodec as nvc

TS = sys.argv[1] if len(sys.argv) > 1 else "test_10s_360p.ts"
FPS = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
MP4_TWIN = TS.replace(".ts", ".mp4")
GPU = 0
RGB = nvc.OutputColorType.RGB


def timeit(fn, n=5, warm=1):
    for _ in range(warm): fn()
    ts = []
    for _ in range(n):
        t0 = time.perf_counter(); out = fn(); torch.cuda.synchronize(); ts.append(time.perf_counter() - t0)
    return statistics.median(ts) * 1000, min(ts) * 1000, out


def section(name):
    print(f"\n=== {name} ===", flush=True)


def stream_info(path):
    d = nvc.CreateDemuxer(filename=path)
    return d.Width(), d.Height(), d.FrameRate(), d.GetNvCodecId()


W, H, SRC_FPS, CODEC = stream_info(TS)
DURATION = 10.0  # test clip; refine from frame count below
TARGET_TS = [i / FPS for i in range(int(DURATION * FPS))]
print(f"clip={os.path.basename(TS)} {W}x{H} @ {SRC_FPS:.2f}fps codec={CODEC}  sample fps={FPS} -> {len(TARGET_TS)} target frames")


# ---------- A. baseline: demux+decode ALL frames (our nvdec_mpegts patch path) ----------
def decode_all(path, dec=None, to_torch=True):
    d = nvc.CreateDemuxer(filename=path)
    own = dec is None
    if own:
        dec = nvc.CreateDecoder(gpuid=GPU, codec=d.GetNvCodecId(), usedevicememory=True, outputColorType=RGB)
    frames = []
    for pkt in d:
        for f in dec.Decode(pkt):
            # never keep DecodedFrame objects past the decoder's lifetime: copy out immediately
            frames.append(torch.from_dlpack(f).clone() if to_torch else None)
    return frames


section("A. baseline: CreateDemuxer+CreateDecoder, decode ALL frames + from_dlpack each (current TS patch)")
med, mn, frames = timeit(lambda: decode_all(TS))
n_all = len(frames); DURATION = n_all / SRC_FPS; TARGET_TS = [i / FPS for i in range(int(DURATION * FPS))]
print(f"  frames={n_all}  median={med:.1f} ms  min={mn:.1f} ms   (duration≈{DURATION:.1f}s, targets={len(TARGET_TS)})")
med, mn, _ = timeit(lambda: decode_all(TS, to_torch=False))
print(f"  same without per-frame from_dlpack: median={med:.1f} ms  min={mn:.1f} ms")


# ---------- B. seek: decode only the sampled frames ----------
def frame_ts_seconds(f, d):
    ts = getattr(f, "timestamp", None)
    if ts is None: return None
    return ts * d.GetTimebaseNum() / d.GetTimebaseDen()


def decode_by_seek(path, targets, reuse_decoder=True):
    d = nvc.CreateDemuxer(filename=path)
    dec = nvc.CreateDecoder(gpuid=GPU, codec=d.GetNvCodecId(), usedevicememory=True, outputColorType=RGB)
    out, decoded = [], 0
    for t in targets:
        if not reuse_decoder:
            dec = nvc.CreateDecoder(gpuid=GPU, codec=d.GetNvCodecId(), usedevicememory=True, outputColorType=RGB)
        idx = int(round(t * SRC_FPS))
        pkt = d.Seek(d.TimestampFromFrame(idx))  # Seek(pts:int) -> PacketData (first packet at/after seek point)
        got = None
        pkts = [pkt] if pkt is not None else []
        for pk in pkts + [p for p in d]:
            for f in dec.Decode(pk):
                decoded += 1
                fts = frame_ts_seconds(f, d)
                if fts is None or fts >= t - 1e-3:
                    got = torch.from_dlpack(f).clone(); break
            if got is not None: break
        out.append(got)
    return out, decoded


section("B. seek per target (Demuxer.Seek + decode until target) — NVIDIA advice #1  [subprocess, SIGSEGV-safe]")
SEEK_CODE = r'''
import sys, time, statistics, torch, PyNvVideoCodec as nvc
path, fps, reuse = sys.argv[1], float(sys.argv[2]), sys.argv[3] == "1"
RGB = nvc.OutputColorType.RGB
d0 = nvc.CreateDemuxer(filename=path); src_fps = d0.FrameRate(); tb = d0.GetTimebaseNum() / d0.GetTimebaseDen()
# duration via a quick packet count
n_pk = sum(1 for _ in d0); duration = n_pk / src_fps
targets = [i / fps for i in range(int(duration * fps))]
def run():
    d = nvc.CreateDemuxer(filename=path)
    dec = nvc.CreateDecoder(gpuid=0, codec=d.GetNvCodecId(), usedevicememory=True, outputColorType=RGB)
    got, decoded = 0, 0
    for t in targets:
        if not reuse:
            dec = nvc.CreateDecoder(gpuid=0, codec=d.GetNvCodecId(), usedevicememory=True, outputColorType=RGB)
        idx = int(round(t * src_fps)); pk = d.Seek(d.TimestampFromFrame(idx))
        found = False
        for p in ([pk] if pk is not None else []) + [q for q in d]:
            for f in dec.Decode(p):
                decoded += 1
                fts = getattr(f, "timestamp", None)
                if fts is None or fts * tb >= t - 1e-3:
                    _ = torch.from_dlpack(f).clone(); got += 1; found = True; break
            if found: break
    torch.cuda.synchronize(); return got, decoded
run()
ts = []
for _ in range(3):
    t0 = time.perf_counter(); got, decoded = run(); ts.append(time.perf_counter() - t0)
print(f"got {got}/{len(targets)} target frames, decoded {decoded} frames total, median={statistics.median(ts)*1000:.1f} ms")
'''
for reuse in ("1", "0"):
    try:
        r = subprocess.run([sys.executable, "-c", SEEK_CODE, TS, str(FPS), reuse], capture_output=True, text=True, timeout=300)
        print(f"  reuse_decoder={reuse=='1'}: exit={r.returncode} {r.stdout.strip()[-200:]} {('STDERR: ' + r.stderr.strip()[-300:]) if r.returncode else ''}")
    except Exception as e:
        print(f"  reuse_decoder={reuse}: {type(e).__name__}: {e}")


# ---------- C. decoder reuse across clips — NVIDIA advice #2 ----------
section("C. decoder create-per-clip vs one reused decoder (full decode, 10 clips)")
def per_clip_new():
    return len(decode_all(TS))
shared = None
def per_clip_reused():
    global shared
    if shared is None:
        d = nvc.CreateDemuxer(filename=TS)
        shared = nvc.CreateDecoder(gpuid=GPU, codec=d.GetNvCodecId(), usedevicememory=True, outputColorType=RGB)
    return len(decode_all(TS, dec=shared))
for name, fn in (("new decoder each clip", per_clip_new), ("reused decoder", per_clip_reused)):
    try:
        med, mn, n = timeit(fn, n=10)
        print(f"  {name:24s}: frames={n} median={med:.1f} ms/clip  min={mn:.1f} ms")
    except Exception as e:
        print(f"  {name}: FAILED {type(e).__name__}: {e}")
t0 = time.perf_counter(); d = nvc.CreateDemuxer(filename=TS); dec = nvc.CreateDecoder(gpuid=GPU, codec=d.GetNvCodecId(), usedevicememory=True, outputColorType=RGB); first = next(iter(d)); list(dec.Decode(first)); torch.cuda.synchronize()
print(f"  cold create+first-packet decode: {(time.perf_counter()-t0)*1000:.1f} ms")


# ---------- D. remux TS->MP4 in memory (no re-encode) + SimpleDecoder index fetch ----------
def remux_ts_to_mp4(path):
    import av
    buf = io.BytesIO()
    with av.open(path) as inp, av.open(buf, "w", format="mp4", options={"movflags": "frag_keyframe+empty_moov+default_base_moof"}) as out:
        vin = inp.streams.video[0]
        vout = out.add_stream_from_template(vin) if hasattr(out, "add_stream_from_template") else out.add_stream(template=vin)
        for pkt in inp.demux(vin):
            if pkt.dts is None: continue
            pkt.stream = vout
            out.mux(pkt)
    return buf.getvalue()


def simple_decode_indices(path, indices):
    sd = nvc.SimpleDecoder(path, gpu_id=GPU, use_device_memory=True, output_color_type=RGB)
    frames = sd.get_batch_frames_by_index(indices)
    return [torch.from_dlpack(f).clone() for f in frames]


section("D. remux TS->fMP4 (stream copy, PyAV) then SimpleDecoder.get_batch_frames_by_index — TS workaround")
try:
    med_r, mn_r, mp4_bytes = timeit(lambda: remux_ts_to_mp4(TS), n=5)
    print(f"  remux: {len(mp4_bytes)//1024} KB, median={med_r:.1f} ms")
    fd, tmp_mp4 = tempfile.mkstemp(suffix=".mp4"); os.write(fd, mp4_bytes); os.close(fd)
    indices = [int(round(t * SRC_FPS)) for t in TARGET_TS]
    indices = [min(i, n_all - 1) for i in indices]
    med_d, mn_d, fr = timeit(lambda: simple_decode_indices(tmp_mp4, indices), n=5)
    print(f"  SimpleDecoder on remuxed fMP4: got {len(fr)} frames (shape {tuple(fr[0].shape)}), median={med_d:.1f} ms  → remux+decode ≈ {med_r+med_d:.1f} ms")
except Exception as e:
    print(f"  FAILED {type(e).__name__}: {e}"); traceback.print_exc(limit=2)

section("E. reference: SimpleDecoder.get_batch_frames_by_index on the native MP4 twin (vLLM upstream path)")
try:
    med, mn, fr = timeit(lambda: simple_decode_indices(MP4_TWIN, indices), n=5)
    print(f"  got {len(fr)} frames, median={med:.1f} ms  min={mn:.1f} ms")
except Exception as e:
    print(f"  FAILED {type(e).__name__}: {e}")

section("E2. SimpleDecoder directly on MPEG-TS (expected unsupported) — run in subprocess")
code = f"import PyNvVideoCodec as nvc; sd=nvc.SimpleDecoder({TS!r}, gpu_id=0, use_device_memory=True, output_color_type=nvc.OutputColorType.RGB); fr=sd.get_batch_frames_by_index([0,15,30]); print('ok', len(fr))"
try:
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    print(f"  exit={r.returncode} stdout={r.stdout.strip()[:120]!r} stderr_tail={r.stderr.strip()[-160:]!r}")
except Exception as e:
    print(f"  {type(e).__name__}: {e}")


# ---------- F. concurrency: 8 workers x 32 clips ----------
section("F. concurrency: 8 threads x 32 clips — throughput (B200 has 7 NVDEC engines)")
def bench_conc(fn, label, conc=8, n=32):
    t0 = time.perf_counter()
    with ThreadPoolExecutor(conc) as ex: list(ex.map(lambda _: fn(), range(n)))
    torch.cuda.synchronize(); wall = time.perf_counter() - t0
    print(f"  {label:44s}: {n} clips in {wall:.2f}s → {n/wall:.1f} clips/s, {wall/n*1000:.0f} ms/clip amortized")
try:
    bench_conc(lambda: decode_all(TS), "A full decode (current patch)")
    bench_conc(lambda: simple_decode_indices(tmp_mp4, indices), "D SimpleDecoder on remuxed fMP4 (no remux)")
    def remux_and_decode():
        b = remux_ts_to_mp4(TS); fd, p = tempfile.mkstemp(suffix=".mp4"); os.write(fd, b); os.close(fd)
        try: return simple_decode_indices(p, indices)
        finally: os.unlink(p)
    bench_conc(remux_and_decode, "D remux+SimpleDecoder end-to-end")
    bench_conc(lambda: simple_decode_indices(MP4_TWIN, indices), "E native MP4 SimpleDecoder")
    bench_conc(lambda: decode_all(TS), "A full decode, 1 thread (sequential ref)", conc=1, n=8)
except Exception as e:
    print(f"  FAILED {type(e).__name__}: {e}"); traceback.print_exc(limit=2)


# ---------- G. vLLM-exact upstream pattern on MPEG-TS (subprocess: SIGSEGV-safe) ----------
section("G. vLLM upstream SimpleDecoder pattern (need_scanned_stream_metadata=True, cuda_stream, cache=2) on TS vs MP4")
VLLM_PATTERN = r'''
import sys, time, torch, PyNvVideoCodec as nvc
path, n_targets = sys.argv[1], int(sys.argv[2])
stream = torch.cuda.Stream(device=0)
t0 = time.perf_counter()
dec = nvc.SimpleDecoder(path, output_color_type=nvc.OutputColorType.RGB, use_device_memory=True,
                        need_scanned_stream_metadata=True, gpu_id=0, cuda_stream=stream.cuda_stream, decoder_cache_size=2)
md = dec.get_stream_metadata(); total = len(dec); t1 = time.perf_counter()
fps = float(getattr(md, "average_fps", 0) or getattr(md, "avg_frame_rate", 0) or 30.0)
idx = [min(total-1, int(round(i * total / n_targets))) for i in range(n_targets)]
frames = dec.get_batch_frames_by_index(idx); tf = [torch.from_dlpack(f) for f in frames]; torch.cuda.synchronize(); t2 = time.perf_counter()
print(f"ok total_frames={total} w={getattr(md,'width',None)} h={getattr(md,'height',None)} fps={fps:.2f} got={len(tf)} construct+meta={ (t1-t0)*1000:.0f}ms decode={ (t2-t1)*1000:.0f}ms")
'''
for label, path in (("TS 10s", TS), ("MP4 twin", MP4_TWIN), ("TS 6s w/ audio (live-like)", "/tmp/seg6.ts")):
    if not os.path.exists(path): print(f"  {label}: missing {path}"); continue
    try:
        r = subprocess.run([sys.executable, "-c", VLLM_PATTERN, path, str(len(TARGET_TS))], capture_output=True, text=True, timeout=120, env={**os.environ})
        print(f"  {label:28s}: exit={r.returncode} {r.stdout.strip()[:200]} {('STDERR: ' + r.stderr.strip()[-200:]) if r.returncode else ''}")
    except Exception as e:
        print(f"  {label}: {type(e).__name__}: {e}")


# ---------- H. reconfigure_decoder reuse (vLLM decoder-slot behaviour) ----------
section("H. SimpleDecoder reuse via reconfigure_decoder across clips (what vLLM's decoder slot does)")
def make_sd(path, stream):
    return nvc.SimpleDecoder(path, output_color_type=RGB, use_device_memory=True, need_scanned_stream_metadata=True,
                             gpu_id=GPU, cuda_stream=stream.cuda_stream, decoder_cache_size=2)
for label, path in (("TS 10s", TS), ("MP4 twin", MP4_TWIN), ("TS 6s w/ audio", "/tmp/seg6.ts")):
    if not os.path.exists(path): continue
    try:
        st = torch.cuda.Stream(device=GPU)
        t0 = time.perf_counter(); sd = make_sd(path, st); total = len(sd); torch.cuda.synchronize(); t_construct = (time.perf_counter() - t0) * 1000
        idx = [min(total - 1, int(round(i * total / len(TARGET_TS)))) for i in range(len(TARGET_TS))]
        def fetch():
            return [torch.from_dlpack(f) for f in sd.get_batch_frames_by_index(idx)]
        med_f, _, fr = timeit(fetch, n=5)
        def reconf_and_fetch():
            sd.reconfigure_decoder(path); _ = len(sd)
            return [torch.from_dlpack(f) for f in sd.get_batch_frames_by_index(idx)]
        med_r, _, fr2 = timeit(reconf_and_fetch, n=5)
        print(f"  {label:16s}: construct+meta={t_construct:.0f}ms | fetch {len(fr)} frames (same decoder)={med_f:.1f}ms | reconfigure+meta+fetch={med_r:.1f}ms  (total_frames={total})")
    except Exception as e:
        print(f"  {label}: FAILED {type(e).__name__}: {e}")

section("I. concurrency with reconfigure-reuse: 2 decoder slots (vLLM default hw_decoders=2) x 32 clips")
try:
    import threading
    slots = []
    for _ in range(2):
        st = torch.cuda.Stream(device=GPU); slots.append((threading.Lock(), st, make_sd(TS, st)))
    def slot_fetch(i):
        lock, st, sd = slots[i % 2]
        with lock, torch.cuda.stream(st):
            sd.reconfigure_decoder(TS); total = len(sd)
            idx = [min(total - 1, int(round(k * total / len(TARGET_TS)))) for k in range(len(TARGET_TS))]
            out = [torch.from_dlpack(f) for f in sd.get_batch_frames_by_index(idx)]; st.synchronize(); return out
    t0 = time.perf_counter()
    with ThreadPoolExecutor(8) as ex: list(ex.map(slot_fetch, range(32)))
    wall = time.perf_counter() - t0
    print(f"  32 clips via 2 reused slots: {wall:.2f}s → {32/wall:.1f} clips/s, {wall/32*1000:.0f} ms/clip")
except Exception as e:
    print(f"  FAILED {type(e).__name__}: {e}"); traceback.print_exc(limit=2)
