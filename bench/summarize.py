"""Summarize a run_all.sh log into markdown tables (raw decode, decode stage, E2E means over reps).

Usage: python bench/summarize.py results/run_all_<date>.log > results/summary.md
"""
import re, statistics, sys
from collections import defaultdict

log = open(sys.argv[1]).read()
sections = re.split(r"^######## \S+ ", log, flags=re.M)[1:]
out = []

for sec in sections:
    title, body = sec.split("\n", 1)
    if title.startswith("A"):
        out.append(f"\n### {title}\n")
        for clip in re.split(r"^clip=", body, flags=re.M)[1:]:
            head, *rows = clip.strip().splitlines()
            out.append(f"\n`{head}`\n\n| backend | procs | agg frames/s | per-proc frames/s | CPU cores | frames/s per core | × realtime |\n|---|---|---|---|---|---|---|")
            for r in rows:
                f = r.split()
                if len(f) == 8 and f[0] in ("cv2", "nvdec"):
                    out.append(f"| {f[0]} | {f[1]} | {f[2]} | {f[3]} | {f[5]} | {f[6]} | {f[7]} |")
    elif title.startswith("B"):
        stage = defaultdict(lambda: defaultdict(list))  # clipset -> backend -> [(seq_ms, clips_s)]
        cur = None
        for line in body.splitlines():
            m = re.match(r"clips=\d+ from (\S+) .* fps=([\d.]+)", line)
            if m: cur = f"{m.group(1).rstrip('/').split('/')[-1]} @ {m.group(2)} fps"
            m = re.match(r"\s+(pynvvideocodec|opencv)\S*\s+frames=\((\d+),.*median=\s*([\d.]+) ms/clip\s+\|\s+8 threads:\s+([\d.]+) clips/s", line)
            if m and cur: stage[cur][m.group(1)].append((float(m.group(3)), float(m.group(4)), int(m.group(2))))
        out.append(f"\n### {title}\n\nMedian per-clip latency (sequential) and 8-thread single-process throughput; mean ± range over 3 repetitions.\n")
        out.append("| Clip set | Frames | CPU (opencv) ms | NVDEC (pynvvideocodec) ms | Speed-up | CPU clips/s | NVDEC clips/s |\n|---|---|---|---|---|---|---|")
        for cs, b in stage.items():
            cpu, nv = b["opencv"], b["pynvvideocodec"]
            fmt = lambda xs: f"{statistics.mean(xs):.0f} ({min(xs):.0f}–{max(xs):.0f})"
            out.append(f"| {cs} | {nv[0][2]} | {fmt([x[0] for x in cpu])} | {fmt([x[0] for x in nv])} | {statistics.mean(x[0] for x in cpu)/statistics.mean(x[0] for x in nv):.1f}× | {statistics.mean(x[1] for x in cpu):.1f} | {statistics.mean(x[1] for x in nv):.1f} |")
    elif title.startswith("C"):
        e2e = defaultdict(list)  # (workload, config) -> dicts
        blocks = re.findall(r"^=== (\S+)/(\S+) clips=(\d+)[^\n]*N=(\d+)[^\n]*===\n(.*?)(?=^===|^## |\Z)", body, flags=re.M | re.S)
        for cfg, wl, clips, n, blk in blocks:
            g = lambda p: float(re.search(p, blk).group(1)) if re.search(p, blk) else float("nan")
            e2e[(wl, cfg)].append(dict(n=int(n), ok=g(r"ok=(\d+)"), err=g(r"err=(\d+)"), rps=g(r"throughput=([\d.]+)"), p50=g(r"p50=([\d.]+)"), p95=g(r"p95=([\d.]+)"), mx=g(r"max=([\d.]+)"), tok=g(r"prompt_tokens avg=(\d+)"), cpu=g(r"([\d.]+) cpu-s/req"), dec=max([int(x) for x in re.findall(r"\d+/(\d+)", blk)] or [0])))
        if not e2e: continue
        out.append(f"\n### {title}\n\nMean over repetitions (n = {len(next(iter(e2e.values())))}). Latency in seconds, CPU = server cgroup cpu-s per request, dec% = peak NVDEC utilization sampled.\n")
        out.append("| Workload | N | Config | ok/err | req/s | p50 | p95 | max | prompt tok | CPU s/req | dec% |\n|---|---|---|---|---|---|---|---|---|---|---|")
        for (wl, cfg), rs in e2e.items():
            m = lambda k: statistics.mean(r[k] for r in rs)
            out.append(f"| {wl} | {rs[0]['n']} | {cfg} | {int(sum(r['ok'] for r in rs))}/{int(sum(r['err'] for r in rs))} | {m('rps'):.1f} | {m('p50'):.1f} | {m('p95'):.1f} | {m('mx'):.1f} | {m('tok'):.0f} | {m('cpu'):.2f} | {max(r['dec'] for r in rs)} |")

print("\n".join(out))
