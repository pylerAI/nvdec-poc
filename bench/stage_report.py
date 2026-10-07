#!/usr/bin/env python3
"""Turn one or more live_stage_matrix.sh run directories into per-stage tables.

Usage: stage_report.py <run_dir> [<run_dir> ...]   (e.g. ~/nvdec-runs/nvdec-mps-1007-1900 ~/nvdec-runs/cpu-opencv-...)
Repetitions of a run (burst1-av, burst2-av, ...) are pooled into one group (burst-av); per-run tables with --per-run.
For every group it slices the stage records by the runs' time windows and prints, per stage:
count per request, median/p95 wall ms, mean thread-CPU ms (and process-CPU ms for sequential runs), GPU ms for
encoder stages; then per-request engine times (queued/prefill/decode), the frontend share, server CPU by process
role, API-server spread, and cache checks (cached prompt tokens). The first call of every stage in every process
is dropped as warm-up (torch.compile, decoder creation).
"""
import collections, glob, json, os, re, statistics, sys

STAGES = [  # (stage, table row)
    ("render_messages", "1-4,6a frontend: chat parse + media fetch (video+audio)"),
    ("fetch_video", "1-4 fetch_video total (download + decode, incl. thread-pool wait)"),
    ("download", "1 download (per HTTP GET; 2 per request with audio)"),
    ("video_decode_total", "2-4 video load_bytes total"),
    ("remux", "2 remux TS->fMP4"),
    ("nvdec_probe", "3a NVDEC decoder reconfigure + stream scan"),
    ("nvdec_decode", "3b NVDEC decode of sampled frames"),
    ("opencv_open", "3a OpenCV open"),
    ("opencv_read", "3b OpenCV decode (all frames, keep sampled)"),
    ("d2h", "4 GPU->pinned host copy (+stack/permute)"),
    ("fetch_audio", "6a fetch_audio total (2nd download + audio decode)"),
    ("audio_decode", "6b audio decode (soundfile try + PyAV)"),
    ("audio_decode_soundfile", "6b' soundfile attempt (fails on TS)"),
    ("audio_decode_pyav", "6b'' PyAV AAC decode"),
    ("process_for_engine", "5-6 processor incl. wait for the 1 mm thread"),
    ("mm_process", "5-6 processor (mm thread)"),
    ("hf_processor", "5-6 HF processor call"),
    ("video_preprocess", "5 video preprocess"),
    ("video_resize_norm", "5 resize+normalize (torch.compile, CPU)"),
    ("audio_resample", "6c resample to 16 kHz"),
    ("audio_preprocess", "6d audio preprocess"),
    ("audio_mel", "6d mel (ParakeetExtractor)"),
    ("mm_hash", "hash (blake3)"),
    ("msgpack_encode", "msgpack encode to engine (>=1 MB msgs)"),
    ("encoder", "7 encoder call (all items in the step)"),
    ("encoder_video", "7v vision encoder (per video)"),
    ("encoder_audio", "7a sound encoder (per call)"),
]


def load(run_dir):
    recs = []
    for p in glob.glob(os.path.join(run_dir, "stages", "*.jsonl")):
        with open(p) as f:
            for line in f:
                try:
                    recs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    recs.sort(key=lambda r: r.get("ts", 0))
    runs = [json.loads(l) for l in open(os.path.join(run_dir, "runs.jsonl"))]
    reqs = [json.loads(l) for l in open(os.path.join(run_dir, "requests.jsonl"))] if os.path.exists(
        os.path.join(run_dir, "requests.jsonl")) else []
    return recs, runs, reqs


def drop_warmup(recs):
    seen, out = set(), []
    for r in recs:
        key = (r.get("pid"), r.get("stage"))
        if key in seen:
            out.append(r)
        else:
            seen.add(key)
    return out


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")


def ms(x):
    return "-" if x != x else f"{x * 1000:.1f}"


def cpu_by_role(run_dir, name):
    try:
        a = json.load(open(os.path.join(run_dir, f"cpu_{name}_0.json")))
        b = json.load(open(os.path.join(run_dir, f"cpu_{name}_1.json")))
    except OSError:
        return {}, None
    roles = collections.Counter()
    for pid, p in b["procs"].items():
        roles[p["role"]] += p["cpu_s"] - a["procs"].get(pid, {"cpu_s": 0})["cpu_s"]
    cg = b.get("cgroup_cpu_s", 0) - a.get("cgroup_cpu_s", 0) if "cgroup_cpu_s" in a else None
    return roles, cg


def groups(runs, per_run):
    out = collections.OrderedDict()
    for run in runs:
        if run["name"].startswith("warm"):
            continue
        out.setdefault(run["name"] if per_run else re.sub(r"\d+", "", run["name"]), []).append(run)
    return out


def report(run_dir, per_run=False):
    recs, runs, reqs = load(run_dir)
    print(f"\n# {run_dir}")
    patched = [r for r in recs if r["stage"] == "_patched"]
    failed = sorted({f for r in patched for f in r["failed"]})
    if failed:
        print("PATCH FAILURES:", *failed, sep="\n  ")
    recs = drop_warmup([r for r in recs if not r["stage"].startswith("_")])
    for name, grp in groups(runs, per_run).items():
        run = grp[0]
        n, seq = sum(r["n"] for r in grp), run["concurrency"] == 1
        win = [r for r in recs if any(g["t0"] <= r.get("ts", 0) <= g["t1"] for g in grp)]
        by = collections.defaultdict(list)
        for r in win:
            by[r["stage"]].append(r)
        audio = "audio+video" if run["audio"] else "video-only"
        print(f"\n## {name}: {n} requests ({len(grp)} run(s)), concurrency {run['concurrency']}, {audio}")
        print("| stage | calls/req | wall p50 ms | wall p95 ms | thread-CPU ms/call | " +
              ("process-CPU ms/call | " if seq else "") + "GPU ms/call |")
        print("|---|---|---|---|---|" + ("---|" if seq else "") + "---|")
        for stage, label in STAGES:
            rs = by.get(stage)
            if not rs:
                continue
            wall = [r["wall"] for r in rs]
            tcpu = [r["tcpu"] for r in rs if "tcpu" in r]
            pcpu = [r["pcpu"] for r in rs if "pcpu" in r]
            gpu = [r["gpu"] for r in rs if "gpu" in r]
            row = f"| {label} | {len(rs) / n:.2f} | {ms(q(wall, .5))} | {ms(q(wall, .95))} | " \
                  f"{ms(statistics.mean(tcpu)) if tcpu else '-'} | "
            if seq:
                row += f"{ms(statistics.mean(pcpu)) if pcpu else '-'} | "
            row += f"{ms(statistics.median(gpu)) if gpu else '-'} |"
            print(row)
        extras = {s: by[s][0] for s in ("video_resize_norm", "video_decode_total", "audio_decode", "d2h") if by.get(s)}
        for s, r in extras.items():
            shown = {k: r[k] for k in ("in", "out", "dtype", "frames", "backend", "samples", "sr", "bytes") if k in r}
            print(f"  {s}: {shown}")
        enc = by.get("encoder", [])
        if enc:
            items = [r["n_items"] for r in enc]
            print(f"  encoder calls: {len(enc)}, items/call mean {statistics.mean(items):.1f} max {max(items)}")
        rq = by.get("request", [])
        if rq:
            def stat(k):
                xs = [r[k] for r in rq]
                return f"{ms(q(xs, .5))} / {ms(q(xs, .95))}"
            front = [r["e2e"] - r["queued"] - r["inference"] for r in rq]
            print(f"  engine per request (p50 / p95 ms): queued {stat('queued')} | prefill {stat('prefill')} | "
                  f"decode {stat('decode')} | e2e(server) {stat('e2e')} | frontend+IPC {ms(q(front, .5))} / {ms(q(front, .95))}")
            print(f"  tokens: prompt {statistics.mean(r['prompt_tokens'] for r in rq):.0f}, generated "
                  f"{statistics.mean(r['gen_tokens'] for r in rq):.1f}, cached prompt tokens mean "
                  f"{statistics.mean(r['cached_tokens'] for r in rq):.0f} (max {max(r['cached_tokens'] for r in rq)}), "
                  f"time/output token {ms(statistics.median(r['tpot'] for r in rq))} ms")
            per_pid = collections.Counter(r["pid"] for r in rq)
            print(f"  API-server spread: {len(per_pid)} processes, requests per process {sorted(per_pid.values(), reverse=True)}")
        names = {g["name"] for g in grp}
        cl = [r for r in reqs if r["label"].split("/")[-1] in names and r.get("err") is None]
        if cl:
            lat = [r["latency"] for r in cl]
            tput = [sum(1 for r in cl if r["label"].endswith("/" + g)) /
                    (max(r["t_start"] + r["latency"] for r in cl if r["label"].endswith("/" + g)) -
                     min(r["t_start"] for r in cl if r["label"].endswith("/" + g))) for g in sorted(names)]
            print(f"  client latency p50 {q(lat, .5):.2f}s p95 {q(lat, .95):.2f}s ({len(cl)} ok), "
                  f"throughput per run {', '.join(f'{t:.1f}' for t in tput)} req/s")
        roles, cg = collections.Counter(), 0.0
        for g in grp:
            r1, c1 = cpu_by_role(run_dir, g["name"])
            roles.update(r1)
            cg = cg + c1 if (c1 is not None and cg is not None) else None
        if roles:
            parts = ", ".join(f"{k} {v / n:.3f}" for k, v in sorted(roles.items()))
            print(f"  server CPU per request (cpu-s): {parts}; total {sum(roles.values()) / n:.3f}"
                  + (f"; pod cgroup {cg / n:.3f}" if cg is not None else ""))


per_run = "--per-run" in sys.argv
for d in (a for a in sys.argv[1:] if not a.startswith("--")):
    report(d, per_run)
