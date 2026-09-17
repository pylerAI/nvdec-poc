"""TS -> in-memory MP4 (stream copy) -> vLLM-exact SimpleDecoder pattern, reconfigure reuse, 2-slot concurrency."""
import io, os, sys, time, subprocess, tempfile, threading, traceback
from concurrent.futures import ThreadPoolExecutor
import av, torch, PyNvVideoCodec as nvc

RGB = nvc.OutputColorType.RGB
CLIPS = {"TS 10s": "test_10s_360p.ts", "TS 6s+audio (live-like)": "/tmp/seg6.ts"}


def remux(path, fragmented):
    buf = io.BytesIO()
    opts = {"movflags": "frag_keyframe+empty_moov+default_base_moof"} if fragmented else {}
    with av.open(path) as inp, av.open(buf, "w", format="mp4", options=opts) as out:
        vin = inp.streams.video[0]
        vout = out.add_stream_from_template(vin) if hasattr(out, "add_stream_from_template") else out.add_stream(template=vin)
        for pkt in inp.demux(vin):
            if pkt.dts is None:
                continue
            pkt.stream = vout
            out.mux(pkt)
    return buf.getvalue()


def write_tmp(b):
    fd, p = tempfile.mkstemp(suffix=".mp4"); os.write(fd, b); os.close(fd); return p


VLLM = r'''
import sys, time, torch, PyNvVideoCodec as nvc
path, n = sys.argv[1], int(sys.argv[2]); st = torch.cuda.Stream(device=0)
t0 = time.perf_counter()
dec = nvc.SimpleDecoder(path, output_color_type=nvc.OutputColorType.RGB, use_device_memory=True,
                        need_scanned_stream_metadata=True, gpu_id=0, cuda_stream=st.cuda_stream, decoder_cache_size=2)
md = dec.get_stream_metadata(); total = len(dec); t1 = time.perf_counter()
idx = [min(total - 1, int(round(i * total / n))) for i in range(n)]
fr = [torch.from_dlpack(f).clone() for f in dec.get_batch_frames_by_index(idx)]; torch.cuda.synchronize(); t2 = time.perf_counter()
ts = []
for _ in range(5):
    a = time.perf_counter(); dec.reconfigure_decoder(path); total = len(dec)
    fr = [torch.from_dlpack(f).clone() for f in dec.get_batch_frames_by_index(idx)]; torch.cuda.synchronize(); ts.append(time.perf_counter() - a)
fps = float(getattr(md, "average_fps", 0) or 0)
print("ok total=%d fps=%.2f got=%d shape=%s construct+meta=%.0fms first_fetch=%.0fms reconfigure+fetch_median=%.1fms"
      % (total, fps, len(fr), tuple(fr[0].shape), (t1 - t0) * 1000, (t2 - t1) * 1000, sorted(ts)[2] * 1000))
'''

tmps = {}
print("=== vLLM-exact SimpleDecoder pattern on remuxed MP4 (subprocess each) ===", flush=True)
for name, path in CLIPS.items():
    for frag in (True, False):
        t0 = time.perf_counter(); b = remux(path, frag); dt = (time.perf_counter() - t0) * 1000
        p = write_tmp(b); tmps[(name, frag)] = p
        n = "20" if "10s" in name else "12"
        r = subprocess.run([sys.executable, "-c", VLLM, p, n], capture_output=True, text=True, timeout=180)
        kind = "fMP4" if frag else "MP4 "
        err = ("ERR: " + r.stderr.strip()[-160:]) if r.returncode else ""
        print("  %-24s %s remux=%.1fms %dKB -> exit=%d %s %s" % (name, kind, dt, len(b) // 1024, r.returncode, r.stdout.strip()[-170:], err), flush=True)

print("\n=== concurrency: 2 reused decoder slots (hw_decoders=2), 8 threads x 32 clips, remux+fetch end-to-end, live-like 6s ===", flush=True)
try:
    src = CLIPS["TS 6s+audio (live-like)"]
    seed = tmps[("TS 6s+audio (live-like)", True)]

    def make_slot():
        st = torch.cuda.Stream(device=0)
        d = nvc.SimpleDecoder(seed, output_color_type=RGB, use_device_memory=True, need_scanned_stream_metadata=True,
                              gpu_id=0, cuda_stream=st.cuda_stream, decoder_cache_size=2)
        return (threading.Lock(), st, d)

    slots = [make_slot(), make_slot()]

    def job(i):
        b = remux(src, True); p = write_tmp(b)
        try:
            lock, st, d = slots[i % 2]
            with lock, torch.cuda.stream(st):
                d.reconfigure_decoder(p); total = len(d)
                idx = [min(total - 1, int(round(k * total / 12))) for k in range(12)]
                out = [torch.from_dlpack(f).clone() for f in d.get_batch_frames_by_index(idx)]
                st.synchronize(); return len(out)
        finally:
            os.unlink(p)

    job(0)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(job, range(32)))
    wall = time.perf_counter() - t0
    print("  32 clips: %.2fs -> %.1f clips/s, %.0f ms/clip amortized, frames/clip=%d" % (wall, 32 / wall, wall / 32 * 1000, res[0]), flush=True)
    t0 = time.perf_counter(); [job(i) for i in range(8)]; wall = time.perf_counter() - t0
    print("  sequential: %.0f ms/clip (remux + reconfigure + 12-frame fetch)" % (wall / 8 * 1000), flush=True)
except Exception:
    traceback.print_exc()
