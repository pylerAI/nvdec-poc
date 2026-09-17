#!/usr/bin/env python3
"""Concurrent load test against a vLLM OpenAI endpoint with video (data URL) requests.

Env: ENDPOINT (http://host:8000), VIDEO (file or directory; a directory is round-robined
per request), N (concurrent requests), USE_AUDIO (1 = use_audio_in_video), FPS (video_url.fps),
MAX_TOKENS, LABEL, MEDIA_IO (JSON for media_io_kwargs), PROMPT.
Prints ok/err counts, latency p50/p90/p95/max, mean prompt_tokens, client CPU seconds.
"""
import base64, glob, json, os, resource, statistics, threading, time, urllib.error, urllib.request

ENDPOINT = os.environ.get("ENDPOINT", "http://localhost:8000")
VIDEO = os.environ["VIDEO"]
N = int(os.environ.get("N", "64"))
USE_AUDIO = os.environ.get("USE_AUDIO", "1") == "1"
FPS = float(os.environ.get("FPS", "2.0"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "64"))
LABEL = os.environ.get("LABEL", "")
PROMPT = os.environ.get("PROMPT", "Describe this video briefly.")

paths = sorted(glob.glob(os.path.join(VIDEO, "*.mp4")) + glob.glob(os.path.join(VIDEO, "*.ts"))) if os.path.isdir(VIDEO) else [VIDEO]
urls, total_bytes = [], 0
for p in paths:
    raw = open(p, "rb").read(); total_bytes += len(raw)
    mime = "video/mp2t" if p.endswith(".ts") else "video/mp4"
    urls.append(f"data:{mime};base64,{base64.b64encode(raw).decode()}")


def make_body(i):
    body = {
        "model": "omni-v1",
        "messages": [{"role": "user", "content": [
            {"type": "video_url", "video_url": {"url": urls[i % len(urls)]}},
            {"type": "text", "text": PROMPT},
        ]}],
        "max_tokens": MAX_TOKENS, "temperature": 0.1,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if USE_AUDIO:
        body["mm_processor_kwargs"] = {"use_audio_in_video": True}
    if os.environ.get("MEDIA_IO"):
        body["media_io_kwargs"] = json.loads(os.environ["MEDIA_IO"])
    return json.dumps(body).encode()


results, lock = [], threading.Lock()


def one(i):
    req = urllib.request.Request(f"{ENDPOINT}/v1/chat/completions", data=make_body(i), headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=600).read())
        with lock: results.append((time.monotonic() - t0, r["usage"]["prompt_tokens"], None))
    except urllib.error.HTTPError as e:
        with lock: results.append((time.monotonic() - t0, None, f"HTTP {e.code} {e.read().decode()[:120]}"))
    except Exception as e:
        with lock: results.append((time.monotonic() - t0, None, str(e)[:120]))


t_start = time.monotonic()
threads = [threading.Thread(target=one, args=(i,)) for i in range(N)]
for t in threads: t.start()
for t in threads: t.join()
wall = time.monotonic() - t_start

ok = [r for r in results if r[2] is None]
lat = sorted(r[0] for r in ok)
pct = lambda p: lat[min(len(lat) - 1, int(p * len(lat)))] if lat else float("nan")
print(f"=== {LABEL} clips={len(paths)} ({total_bytes/len(paths)/1e6:.1f} MB avg) N={N} fps={FPS} audio={USE_AUDIO} ===")
print(f"  ok={len(ok)} err={len(results)-len(ok)} wall={wall:.1f}s throughput={len(ok)/wall:.1f} req/s")
if ok:
    print(f"  latency p50={pct(0.5):.1f}s p90={pct(0.9):.1f}s p95={pct(0.95):.1f}s max={lat[-1]:.1f}s min={lat[0]:.1f}s")
    print(f"  prompt_tokens avg={statistics.mean(r[1] for r in ok):.0f}")
ru = resource.getrusage(resource.RUSAGE_SELF)
print(f"  client cpu: user={ru.ru_utime:.1f}s sys={ru.ru_stime:.1f}s")
errs = {}
for r in results:
    if r[2]: errs[r[2]] = errs.get(r[2], 0) + 1
for e, c in errs.items(): print(f"  ERR x{c}: {e}")
