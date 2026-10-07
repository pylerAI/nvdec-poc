#!/usr/bin/env python3
"""Concurrent load test against a vLLM OpenAI endpoint with video (data URL) requests.

Env: ENDPOINT (http://host:8000), VIDEO (file or directory; a directory is round-robined
per request), N (concurrent requests), USE_AUDIO (1 = use_audio_in_video), FPS (video_url.fps),
MAX_TOKENS, LABEL, MEDIA_IO (JSON for media_io_kwargs), PROMPT.
Prints ok/err counts, latency p50/p90/p95/max, mean prompt_tokens, client CPU seconds.

Paced live mode, when STREAMS > 0 (N is then ignored): STREAMS live streams each send one segment
every INTERVAL seconds (default 6), round(DURATION/INTERVAL) segments per stream (DURATION default
300), open loop -- a slow reply does not delay the stream's next segment. Stream starts are spread evenly over one INTERVAL; with a
directory, stream k starts at segment k*len/STREAMS and walks forward. UNIQUE=1 (default) gives every
request its own multimodal uuid, which vLLM uses as the cache key instead of a content hash, so its
processor, encoder and prefix caches miss as they would for unique live segments. Also prints
deadline misses (latency > INTERVAL), p95 of the first vs second half of the run (a rising p95 means
the server is falling behind) and the client's send lag.
"""
import base64, glob, json, os, resource, statistics, threading, time, urllib.error, urllib.request, uuid

ENDPOINT = os.environ.get("ENDPOINT", "http://localhost:8000")
VIDEO = os.environ["VIDEO"]
N = int(os.environ.get("N", "64"))
USE_AUDIO = os.environ.get("USE_AUDIO", "1") == "1"
FPS = float(os.environ.get("FPS", "2.0"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "64"))
LABEL = os.environ.get("LABEL", "")
PROMPT = os.environ.get("PROMPT", "Describe this video briefly.")
STREAMS = int(os.environ.get("STREAMS", "0"))
INTERVAL = float(os.environ.get("INTERVAL", "6.0"))
DURATION = float(os.environ.get("DURATION", "300"))
UNIQUE = os.environ.get("UNIQUE", "1") == "1"

paths = sorted(glob.glob(os.path.join(VIDEO, "*.mp4")) + glob.glob(os.path.join(VIDEO, "*.ts"))) if os.path.isdir(VIDEO) else [VIDEO]
urls, total_bytes = [], 0
for p in paths:
    raw = open(p, "rb").read(); total_bytes += len(raw)
    mime = "video/mp2t" if p.endswith(".ts") else "video/mp4"
    urls.append(f"data:{mime};base64,{base64.b64encode(raw).decode()}")


def make_body(i, mm_uuid=None):
    video = {"type": "video_url", "video_url": {"url": urls[i % len(urls)]}}
    if mm_uuid:
        video["uuid"] = mm_uuid  # vLLM keys its processor/encoder/prefix caches on this instead of the content hash
    body = {
        "model": "omni-v1",
        "messages": [{"role": "user", "content": [
            video,
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


def one(i, mm_uuid=None, off=None):  # off: scheduled send time relative to t_start (paced mode)
    req = urllib.request.Request(f"{ENDPOINT}/v1/chat/completions", data=make_body(i, mm_uuid), headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=600).read())
        with lock: results.append((time.monotonic() - t0, r["usage"]["prompt_tokens"], None, t0, off))
    except urllib.error.HTTPError as e:
        with lock: results.append((time.monotonic() - t0, None, f"HTTP {e.code} {e.read().decode()[:120]}", t0, off))
    except Exception as e:
        with lock: results.append((time.monotonic() - t0, None, str(e)[:120], t0, off))


t_start = time.monotonic()
if STREAMS > 0:
    # stream k sends its j-th segment at k*INTERVAL/STREAMS + j*INTERVAL, whether or not earlier replies are back
    run_id, sends = uuid.uuid4().hex[:8], max(1, round(DURATION / INTERVAL))
    span = sends * INTERVAL  # actual run length when DURATION is not a multiple of INTERVAL
    schedule =sorted((k * INTERVAL / STREAMS + j * INTERVAL, k, j) for k in range(STREAMS) for j in range(sends))
    threads = []
    for off, k, j in schedule:
        time.sleep(max(0.0, t_start + off - time.monotonic()))
        threads.append(threading.Thread(target=one, args=(k * len(urls) // STREAMS + j, f"{run_id}-{k}-{j}" if UNIQUE else None, off)))
        threads[-1].start()
else:
    threads = [threading.Thread(target=one, args=(i,)) for i in range(N)]
    for t in threads: t.start()
for t in threads: t.join()
wall = time.monotonic() - t_start

ok = [r for r in results if r[2] is None]
lat = sorted(r[0] for r in ok)
pct = lambda p, xs=lat: xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
head = f"=== {LABEL} clips={len(paths)} ({total_bytes/len(paths)/1e6:.1f} MB avg)"
if STREAMS > 0:
    print(f"{head} streams={STREAMS} interval={INTERVAL:g}s duration={span:g}s fps={FPS} audio={USE_AUDIO} unique={UNIQUE} ===")
    print(f"  sent={len(results)} ok={len(ok)} err={len(results)-len(ok)} wall={wall:.1f}s throughput={len(ok)/wall:.1f} req/s (offered {STREAMS/INTERVAL:.1f})")
    if ok:
        late = sum(x > INTERVAL for x in lat)
        half = lambda first: sorted(r[0] for r in ok if (r[4] < span / 2 - 1e-6) == first)  # a send due exactly mid-run counts as second half
        lag = sorted(r[3] - t_start - r[4] for r in results)
        print(f"  latency p50={pct(0.5):.1f}s p90={pct(0.9):.1f}s p95={pct(0.95):.1f}s p99={pct(0.99):.1f}s max={lat[-1]:.1f}s min={lat[0]:.1f}s")
        print(f"  late(>{INTERVAL:g}s)={late} ({100 * late / len(ok):.1f}%)  p95 first half={pct(0.95, half(True)):.1f}s second half={pct(0.95, half(False)):.1f}s")
        print(f"  send lag p50={1e3 * pct(0.5, lag):.0f}ms max={1e3 * lag[-1]:.0f}ms")
        print(f"  prompt_tokens avg={statistics.mean(r[1] for r in ok):.0f}")
else:
    print(f"{head} N={N} fps={FPS} audio={USE_AUDIO} ===")
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
