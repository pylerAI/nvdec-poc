#!/usr/bin/env python3
"""Side-by-side comparison of live_stage_matrix.sh runs (e.g. 360p vs 1080p, NVDEC vs CPU).

Usage: compare_runs.py <label>=<run_dir> [<label>=<run_dir> ...]
For each run and each group (seq-av, seq-v, burst-av, burst-v; repetitions pooled) prints per-request MEANS so that
stages add up: client p50 / throughput, phases (frontend+IPC, prefill, decode), stage times (download, remux,
decode, host copy, preprocess incl. wait, audio), encoder time per request, tokens, server CPU by role.
Warm-up first calls per (process, stage) are dropped as in stage_report.py.
"""
import collections, glob, json, os, sys


def load(d):
    recs = [json.loads(l) for p in glob.glob(os.path.join(d, "stages", "*.jsonl")) for l in open(p)]
    recs.sort(key=lambda r: r.get("ts", 0))
    seen, out = set(), []
    for r in recs:
        if r["stage"].startswith("_"):
            continue
        k = (r.get("pid"), r["stage"])
        if k in seen:
            out.append(r)
        else:
            seen.add(k)
    runs = [json.loads(l) for l in open(os.path.join(d, "runs.jsonl"))]
    reqs = [json.loads(l) for l in open(os.path.join(d, "requests.jsonl"))] if os.path.exists(
        os.path.join(d, "requests.jsonl")) else []
    return out, runs, reqs


def cpu_by_role(d, names):
    roles = collections.Counter()
    for name in names:
        try:
            a = json.load(open(os.path.join(d, f"cpu_{name}_0.json")))
            b = json.load(open(os.path.join(d, f"cpu_{name}_1.json")))
        except OSError:
            continue
        for pid, p in b["procs"].items():
            roles[p["role"]] += p["cpu_s"] - a["procs"].get(pid, {"cpu_s": 0})["cpu_s"]
    return roles


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")


import re
GROUP_OF = lambda n: re.sub(r"^burst\d+", "burst", n)  # burst1-av -> burst-av, burst2-c8-v -> burst-c8-v
GROUPS = [(g, (lambda n, g=g: GROUP_OF(n) == g)) for g in ("seq-av", "seq-v", "burst-c8-av", "burst-c8-v", "burst-av", "burst-v")]


def summarize(d):
    recs, runs, reqs = load(d)
    out = {}
    for gname, sel in GROUPS:
        grp = [r for r in runs if sel(r["name"])]
        if not grp:
            continue
        n = sum(r["n"] for r in grp)
        win = [r for r in recs if any(g["t0"] <= r.get("ts", 0) <= g["t1"] for g in grp)]
        tot = collections.defaultdict(float)
        for r in win:
            tot[r["stage"]] += r.get("wall", 0)
        s = {k: tot[k] / n * 1000 for k in tot}  # mean ms per request
        rq = [r for r in win if r["stage"] == "request"]
        m = lambda k: sum(r[k] for r in rq) / len(rq) * 1000 if rq else float("nan")
        e2e, queued, prefill, decode = m("e2e"), m("queued"), m("prefill"), m("decode")
        names = {g["name"] for g in grp}
        cl = [r for r in reqs if r["label"].split("/")[-1] in names and r.get("err") is None]
        lat = [r["latency"] for r in cl]
        tput = []
        for g in sorted(names):
            rr = [r for r in cl if r["label"].endswith("/" + g)]
            if rr:
                tput.append(len(rr) / (max(r["t_start"] + r["latency"] for r in rr) - min(r["t_start"] for r in rr)))
        roles = cpu_by_role(d, names)
        audio_pre = s.get("audio_preprocess", 0) or s.get("audio_mel", 0)
        out[gname] = {
            "n": n, "client p50 s": q(lat, .5), "client p95 s": q(lat, .95),
            "throughput req/s": sum(tput) / len(tput) if tput else float("nan"),
            "e2e mean ms": e2e, "frontend+IPC ms": e2e - queued - prefill - decode, "prefill ms": prefill, "decode ms": decode,
            "1 download ms": s.get("download", 0), "2 remux ms": s.get("remux", 0),
            "3 decode ms": s.get("nvdec_probe", 0) + s.get("nvdec_decode", 0) + s.get("opencv_open", 0) + s.get("opencv_read", 0),
            "4 d2h ms": s.get("d2h", 0), "5 preprocess incl. wait ms": s.get("process_for_engine", 0) - audio_pre,
            "5 resize compute ms": s.get("video_resize_norm", 0), "6 audio ms": s.get("fetch_audio", 0) + audio_pre,
            "7 encoder/req ms": s.get("encoder_video", 0) + s.get("encoder_audio", 0),
            "prompt tokens": sum(r["prompt_tokens"] for r in rq) / len(rq) if rq else float("nan"),
            "gen tokens": sum(r["gen_tokens"] for r in rq) / len(rq) if rq else float("nan"),
            "ms/output token": sum(r["tpot"] for r in rq) / len(rq) * 1000 if rq else float("nan"),
            "api cpu-s/req": roles.get("api", 0) / n, "engine cpu-s/req": roles.get("engine", 0) / n,
        }
    return out


labels, dirs = [], []
for a in sys.argv[1:]:
    label, d = a.split("=", 1) if "=" in a else (os.path.basename(a.rstrip("/")), a)
    labels.append(label); dirs.append(d)
sums = [summarize(d) for d in dirs]
for gname, _ in GROUPS:
    if not any(gname in s for s in sums):
        continue
    print(f"\n## {gname}")
    keys = next(s[gname] for s in sums if gname in s).keys()
    print("| metric | " + " | ".join(labels) + " |")
    print("|---|" + "---|" * len(labels))
    for k in keys:
        row = []
        for s in sums:
            v = s.get(gname, {}).get(k)
            row.append("-" if v is None else (f"{v:.0f}" if isinstance(v, float) and abs(v) >= 100 else f"{v:.2f}" if isinstance(v, float) else str(v)))
        print(f"| {k} | " + " | ".join(row) + " |")
