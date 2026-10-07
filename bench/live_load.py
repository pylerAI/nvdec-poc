#!/usr/bin/env python3
"""Live-segment load generator: N requests, each with a byte-distinct copy of one MPEG-TS segment.

Env: ENDPOINT (http://localhost:8000), MODE (http = URL served by seg_server.py, like live-ingest;
data = base64 data URL, like load_test.py), SEG_URL (http://127.0.0.1:8890/v), SEG (segment path, data mode),
N (requests), CONCURRENCY (N = one burst like load_test.py, 1 = sequential), USE_AUDIO (1 = use_audio_in_video),
MEDIA_IO (JSON for media_io_kwargs), MAX_TOKENS, KEY (unique prefix for this run), LABEL, OUT (per-request jsonl).
Production request shape (live-ingest): SYSTEM_PROMPT (adds a system message), RESPONSE_FORMAT (JSON, or @path to a
JSON file; sent as response_format), VIDEO_URL_EXTRA (JSON merged into the video_url object, e.g. {"fps": 2.0}), PROMPT="" (no text part, video only).
Prints the same summary lines as load_test.py.
"""
import base64, json, os, statistics, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

ENDPOINT = os.environ.get("ENDPOINT", "http://localhost:8000")
MODE = os.environ.get("MODE", "http")
SEG_URL = os.environ.get("SEG_URL", "http://127.0.0.1:8890/v")
N = int(os.environ.get("N", "64"))
CONCURRENCY = int(os.environ.get("CONCURRENCY", str(N)))
USE_AUDIO = os.environ.get("USE_AUDIO", "1") == "1"
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "64"))
KEY = os.environ.get("KEY", f"run{int(time.time())}")
LABEL = os.environ.get("LABEL", KEY)
PROMPT = os.environ.get("PROMPT", "Describe this video briefly.")
OUT = os.environ.get("OUT")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")
RESPONSE_FORMAT = os.environ.get("RESPONSE_FORMAT")
if RESPONSE_FORMAT and RESPONSE_FORMAT.startswith("@"):
    RESPONSE_FORMAT = open(RESPONSE_FORMAT[1:]).read()
RESPONSE_FORMAT = json.loads(RESPONSE_FORMAT) if RESPONSE_FORMAT else None
VIDEO_URL_EXTRA = json.loads(os.environ.get("VIDEO_URL_EXTRA") or "{}")

if MODE == "data":
    BASE = open(os.environ["SEG"], "rb").read()
    null = lambda k: bytes([0x47, 0x1F, 0xFF, 0x10]) + k.encode()[:184].ljust(184, b"\xff")
    url_of = lambda k: "data:video/mp2t;base64," + base64.b64encode(BASE + null(k)).decode()
else:
    url_of = lambda k: f"{SEG_URL}/{k}.ts"


def body(i):
    b = {
        "model": "omni-v1",
        "messages": ([{"role": "system", "content": SYSTEM_PROMPT}] if SYSTEM_PROMPT else []) + [{"role": "user", "content": [
            {"type": "video_url", "video_url": {"url": url_of(f"{KEY}-{i}"), **VIDEO_URL_EXTRA}},
        ] + ([{"type": "text", "text": PROMPT}] if PROMPT else [])}],
        "max_tokens": MAX_TOKENS, "temperature": 0.1,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if RESPONSE_FORMAT:
        b["response_format"] = RESPONSE_FORMAT
    if USE_AUDIO:
        b["mm_processor_kwargs"] = {"use_audio_in_video": True}
    if os.environ.get("MEDIA_IO"):
        b["media_io_kwargs"] = json.loads(os.environ["MEDIA_IO"])
    return json.dumps(b).encode()


bodies = [body(i) for i in range(N)]
results, lock = [], threading.Lock()


def one(i):
    req = urllib.request.Request(f"{ENDPOINT}/v1/chat/completions", data=bodies[i], headers={"Content-Type": "application/json"})
    t_wall, t0 = time.time(), time.monotonic()
    rec = {"i": i, "key": f"{KEY}-{i}", "t_start": t_wall}
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=600).read())
        rec.update(latency=time.monotonic() - t0, prompt_tokens=r["usage"]["prompt_tokens"],
                   completion_tokens=r["usage"]["completion_tokens"], err=None)
    except urllib.error.HTTPError as e:
        rec.update(latency=time.monotonic() - t0, err=f"HTTP {e.code} {e.read().decode()[:160]}")
    except Exception as e:
        rec.update(latency=time.monotonic() - t0, err=str(e)[:160])
    with lock:
        results.append(rec)


t_start = time.monotonic()
with ThreadPoolExecutor(CONCURRENCY) as ex:
    list(ex.map(one, range(N)))
wall = time.monotonic() - t_start

if OUT:
    with open(OUT, "a") as f:
        for r in sorted(results, key=lambda r: r["i"]):
            f.write(json.dumps({"label": LABEL, **r}) + "\n")

ok = [r for r in results if r["err"] is None]
lat = sorted(r["latency"] for r in ok)
pct = lambda p: lat[min(len(lat) - 1, int(p * len(lat)))] if lat else float("nan")
print(f"=== {LABEL} mode={MODE} N={N} concurrency={CONCURRENCY} audio={USE_AUDIO} ===")
print(f"  ok={len(ok)} err={len(results)-len(ok)} wall={wall:.1f}s throughput={len(ok)/wall:.1f} req/s")
if ok:
    print(f"  latency p50={pct(0.5):.2f}s p90={pct(0.9):.2f}s p95={pct(0.95):.2f}s max={lat[-1]:.2f}s min={lat[0]:.2f}s")
    print(f"  prompt_tokens avg={statistics.mean(r['prompt_tokens'] for r in ok):.0f} completion_tokens avg={statistics.mean(r['completion_tokens'] for r in ok):.1f}")
errs = {}
for r in results:
    if r["err"]:
        errs[r["err"]] = errs.get(r["err"], 0) + 1
for e, c in errs.items():
    print(f"  ERR x{c}: {e}")
