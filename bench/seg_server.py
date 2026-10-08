#!/usr/bin/env python3
"""Serve a distinct media file per request key over HTTP, so every request misses vLLM's caches.

GET /v/<key>.<ext>  -> the clip assigned to <key> (video);  GET /a/<key>.wav -> its companion audio, if any.
- <source> is a directory of .ts or .mp4 clips (make_variants.py, or VOD clips with sibling .wav files): each new
  key gets the next unused clip (same key -> same clip). When the clips run out it wraps around; a wrapped clip is
  served with a per-key trailing byte string (MPEG-TS null packet / MP4 `free` box) so its bytes, and with them
  vLLM's video hash, still differ per request while decoding is unchanged.
- <source> is one .ts file: the file followed by one MPEG-TS null packet (PID 0x1FFF) carrying <key>. Decoded video
  and audio are identical but the bytes differ; this defeats the video caches only (audio is hashed by waveform).

Usage: python seg_server.py <clips_dir | segment.ts> [port]
"""
import glob, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOURCE = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8890
MIME = {".ts": "video/mp2t", ".mp4": "video/mp4", ".wav": "audio/wav"}
if os.path.isdir(SOURCE):
    PATHS = sorted(glob.glob(os.path.join(SOURCE, "*.ts")) + glob.glob(os.path.join(SOURCE, "*.mp4")))
    assert PATHS, f"no .ts/.mp4 files in {SOURCE}"
    COPIES = [open(p, "rb").read() for p in PATHS]
    AUDIO = [open(os.path.splitext(p)[0] + ".wav", "rb").read() if os.path.exists(os.path.splitext(p)[0] + ".wav") else None for p in PATHS]
    EXT = os.path.splitext(PATHS[0])[1]
    BASE = None
else:
    COPIES, BASE, EXT = None, open(SOURCE, "rb").read(), ".ts"
    assert BASE[0] == 0x47 and len(BASE) % 188 == 0, "expects a 188-byte-aligned MPEG-TS segment"
assigned, lock = {}, threading.Lock()


def _tail(key: str) -> bytes:
    """Per-key trailing bytes that demuxers ignore: a TS null packet, or an MP4 `free` box."""
    if EXT == ".ts":
        return bytes([0x47, 0x1F, 0xFF, 0x10]) + key.encode()[:184].ljust(184, b"\xff")
    payload = key.encode()[:120].ljust(120, b"\0")
    return (8 + len(payload)).to_bytes(4, "big") + b"free" + payload


def _slot(key: str) -> tuple[int, bool]:
    with lock:
        if key not in assigned:
            assigned[key] = len(assigned)
        n = assigned[key]
    return n % len(COPIES), n >= len(COPIES)


def variant(key: str) -> bytes:
    if COPIES is None:
        return BASE + _tail(key)
    idx, wrapped = _slot(key)
    return COPIES[idx] + (_tail(key) if wrapped else b"")


def audio(key: str) -> bytes | None:
    if COPIES is None:
        return None
    idx, _ = _slot(key)
    return AUDIO[idx]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        key = os.path.splitext(self.path[3:])[0]
        if self.path.startswith("/a/"):
            body, ctype = audio(key), "audio/wav"
            if body is None:
                self.send_error(404)
                return
        elif self.path.startswith("/v/"):
            body, ctype = variant(key), MIME.get(EXT, "application/octet-stream")
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"seg_server: {len(COPIES) if COPIES else 'null-packet'} clips ({EXT}) of {SOURCE} on :{PORT}"
          + (f", {sum(a is not None for a in AUDIO)} with .wav audio" if COPIES else ""), file=sys.stderr)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
