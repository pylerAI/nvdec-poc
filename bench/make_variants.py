#!/usr/bin/env python3
"""Make N content-distinct copies of one MPEG-TS segment: video packets stream-copied, audio re-encoded with a
per-copy inaudible noise floor (~-80 dBFS).

Why: vLLM hashes the video item by its encoded bytes but the audio item (use_audio_in_video) by its decoded waveform,
so byte-distinct copies with identical audio still hit the engine's encoder cache for audio. Live-ingest segments
are always new content; these copies make every request miss every cache (processor, encoder, prefix).

Usage: python make_variants.py <segment.ts> <out_dir> [n=800]
"""
import io, os, sys

import av
import numpy as np

src, out_dir = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 800
data = open(src, "rb").read()
os.makedirs(out_dir, exist_ok=True)


def variant(seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    buf = io.BytesIO()
    with av.open(io.BytesIO(data), format="mpegts") as inp, av.open(buf, "w", format="mpegts") as out:
        vin, ain = inp.streams.video[0], inp.streams.audio[0]
        vout = out.add_stream_from_template(vin)
        aout = out.add_stream("aac", rate=ain.rate, layout=ain.layout.name)
        aout.bit_rate = ain.bit_rate or 64000
        for pkt in inp.demux(vin, ain):
            if pkt.stream is vin:
                if pkt.dts is None:
                    continue
                pkt.stream = vout
                out.mux(pkt)
                continue
            for frame in pkt.decode():
                arr = frame.to_ndarray()
                arr = arr + rng.normal(0.0, 1e-4, arr.shape).astype(arr.dtype)
                nf = av.AudioFrame.from_ndarray(arr, format=frame.format.name, layout=frame.layout.name)
                nf.sample_rate, nf.pts, nf.time_base = frame.sample_rate, frame.pts, frame.time_base
                for p in aout.encode(nf):
                    out.mux(p)
        for p in aout.encode(None):
            out.mux(p)
    return buf.getvalue()


for i in range(n):
    with open(os.path.join(out_dir, f"v{i:04d}.ts"), "wb") as f:
        f.write(variant(i))
print(f"wrote {n} variants of {src} ({len(data)} B) to {out_dir}")
