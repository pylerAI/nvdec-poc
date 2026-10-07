#!/usr/bin/env python3
"""Serve a distinct MPEG-TS segment per request key over HTTP, so every request misses vLLM's caches.

GET /v/<key>.ts
- <source> is a directory (from make_variants.py): each new key gets the next unused copy (same key -> same copy),
  so video bytes and audio waveform both differ per request. Wraps around with a warning when the copies run out.
- <source> is one .ts file: the file followed by one MPEG-TS null packet (PID 0x1FFF) carrying <key>. Decoded video
  and audio are identical but the bytes differ; this defeats the video caches only (audio is hashed by waveform).

Usage: python seg_server.py <variants_dir | segment.ts> [port]
"""
import glob, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOURCE = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8890
if os.path.isdir(SOURCE):
    COPIES = [open(p, "rb").read() for p in sorted(glob.glob(os.path.join(SOURCE, "*.ts")))]
    assert COPIES, f"no .ts files in {SOURCE}"
    BASE = None
else:
    COPIES, BASE = None, open(SOURCE, "rb").read()
    assert BASE[0] == 0x47 and len(BASE) % 188 == 0, "expects a 188-byte-aligned MPEG-TS segment"
assigned, lock = {}, threading.Lock()


def variant(key: str) -> bytes:
    if COPIES is None:
        return BASE + bytes([0x47, 0x1F, 0xFF, 0x10]) + key.encode()[:184].ljust(184, b"\xff")
    with lock:
        if key not in assigned:
            if len(assigned) == len(COPIES):
                print(f"seg_server: all {len(COPIES)} copies used, reusing (cache hits possible)", file=sys.stderr)
            assigned[key] = len(assigned) % len(COPIES)
        return COPIES[assigned[key]]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        if not self.path.startswith("/v/"):
            self.send_error(404)
            return
        body = variant(self.path[3:])
        self.send_response(200)
        self.send_header("Content-Type", "video/mp2t")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"seg_server: {len(COPIES) if COPIES else 'null-packet'} copies of {SOURCE} on :{PORT}", file=sys.stderr)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
