"""Build-time patch: MPEG-TS support for the pynvvideocodec video backend.

PyNvVideoCodec 2.1.1's ``SimpleDecoder`` cannot index MPEG-TS: with
``need_scanned_stream_metadata=True`` it raises IndexError or SIGSEGVs, and the
demuxer's ``Seek``/``TimestampFromFrame`` crash on .ts input.  HLS live segments
feeds exactly those segments.

Instead of decoding the whole segment ourselves (the 0.4.x approach: a fresh
``CreateDemuxer``+``CreateDecoder`` per request, ~300 ms for a 6 s clip because
decoder warm-up dominates), this patch stream-copies the video track into a
fragmented MP4 in memory (PyAV, no re-encode, ~5 ms CPU) and lets the request
fall through to vLLM's normal MP4 path, which samples only the requested frames
and reuses cached decoder slots via ``reconfigure_decoder`` (~20 ms for a 6 s
clip on B200).

Run once during ``docker build``:
    RUN python3 /tmp/patches/nvdec_mpegts.py
"""

from __future__ import annotations

import importlib.util
import re
import site
import textwrap
from pathlib import Path

MARKER = "_remux_mpegts_to_mp4"


def _find_video_py() -> Path:
    for d in site.getsitepackages() + [site.getusersitepackages()]:
        p = Path(d) / "vllm" / "multimodal" / "video.py"
        if p.exists():
            return p
    spec = importlib.util.find_spec("vllm.multimodal.video")
    if spec and spec.origin:
        return Path(spec.origin)
    raise FileNotFoundError("Cannot find vllm/multimodal/video.py")


HELPERS = textwrap.dedent(r'''
def _is_mpegts(data: bytes) -> bool:
    """MPEG-TS: 188-byte packets, each starting with sync byte 0x47."""
    return len(data) >= 376 and data[0] == 0x47 and data[188] == 0x47


def _remux_mpegts_to_mp4(data: bytes) -> bytes:
    """Stream-copy the video track of an MPEG-TS buffer into fragmented MP4.

    No re-encode. SimpleDecoder cannot index MPEG-TS, but the same H.264/HEVC
    elementary stream inside fMP4 takes the normal random-access path with
    decoder-slot reuse. Audio is dropped here on purpose: vLLM's audio loader
    reads it from the original request bytes.
    """
    import io

    import av

    src, dst = io.BytesIO(data), io.BytesIO()
    with av.open(src, format="mpegts") as inp, av.open(
        dst,
        "w",
        format="mp4",
        options={"movflags": "frag_keyframe+empty_moov+default_base_moof"},
    ) as out:
        vin = inp.streams.video[0]
        vout = (
            out.add_stream_from_template(vin)
            if hasattr(out, "add_stream_from_template")
            else out.add_stream(template=vin)
        )
        for pkt in inp.demux(vin):
            if pkt.dts is None:
                continue
            pkt.stream = vout
            out.mux(pkt)
    return dst.getvalue()
''')

GUARD = (
    "        if _is_mpegts(data):\n"
    "            data = _remux_mpegts_to_mp4(data)\n"
)
ANCHOR_CLASS = "class PyNvVideoCodecVideoBackendMixin:"
ANCHOR_TMP = '        temp_fd, temp_path = tempfile.mkstemp(suffix=".mp4")\n'


def patch() -> None:
    video_py = _find_video_py()
    src = video_py.read_text()

    if MARKER in src:
        print(f"[nvdec_mpegts] already patched: {video_py}")
        return

    if ANCHOR_CLASS not in src:
        raise RuntimeError(f"Cannot find '{ANCHOR_CLASS}' in {video_py}")
    src = src.replace(ANCHOR_CLASS, HELPERS + "\n\n" + ANCHOR_CLASS, 1)

    m = re.search(r"    def decode_frames_pynvvideocodec\b", src)
    if not m:
        raise RuntimeError("Cannot find decode_frames_pynvvideocodec in video.py")
    i = src.find(ANCHOR_TMP, m.end())
    if i < 0:
        raise RuntimeError("Cannot find mkstemp(.mp4) inside decode_frames_pynvvideocodec")
    src = src[:i] + GUARD + src[i:]

    video_py.write_text(src)
    print(f"[nvdec_mpegts] patched: {video_py}")


if __name__ == "__main__":
    patch()
