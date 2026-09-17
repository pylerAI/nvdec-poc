"""Cut a long-form MP4 into fixed-length 'shot' clips by stream copy (no re-encode), keyframe-aligned.

Usage: python cut_shots.py <src.mp4> <out_dir> <seconds> <count> [skip_seconds]
"""
import os, sys
import av

src, out_dir, seg_s, count = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
skip_s = float(sys.argv[5]) if len(sys.argv) > 5 else 60.0
os.makedirs(out_dir, exist_ok=True)

inp = av.open(src)
vin = inp.streams.video[0]
ain = inp.streams.audio[0] if inp.streams.audio else None
tb = vin.time_base

written = 0
out = None
seg_start_pts = None
streams = {}

def close_out():
    global out
    if out is not None:
        out.close(); out = None

def open_out(idx):
    global out, streams
    path = os.path.join(out_dir, f"shot_{int(seg_s):03d}s_{idx:03d}.mp4")
    out = av.open(path, "w", format="mp4")
    vo = out.add_stream_from_template(vin) if hasattr(out, "add_stream_from_template") else out.add_stream(template=vin)
    streams = {vin.index: vo}
    if ain is not None:
        ao = out.add_stream_from_template(ain) if hasattr(out, "add_stream_from_template") else out.add_stream(template=ain)
        streams[ain.index] = ao
    return path

demux_streams = [vin] + ([ain] if ain is not None else [])
started = False
for pkt in inp.demux(*demux_streams):
    if pkt.dts is None:
        continue
    t = float(pkt.pts * pkt.time_base) if pkt.pts is not None else None
    if t is None:
        continue
    if not started:
        if pkt.stream is vin and pkt.is_keyframe and t >= skip_s:
            started = True
            seg_start = t
            open_out(written)
        else:
            continue
    if pkt.stream is vin and pkt.is_keyframe and t - seg_start >= seg_s:
        close_out(); written += 1
        if written >= count:
            break
        seg_start = t
        open_out(written)
    pkt.stream = streams[pkt.stream.index]
    out.mux(pkt)
close_out()
inp.close()
sizes = sorted(os.listdir(out_dir))
print(f"wrote {written} clips of ~{seg_s:.0f}s to {out_dir}: {sizes[:3]} ... total {sum(os.path.getsize(os.path.join(out_dir, f)) for f in sizes)//(1024*1024)} MB")
