#!/usr/bin/env python3
"""Snapshot CPU seconds of the vLLM server by process role, plus the pod cgroup total.

Usage: proc_cpu.py <out.json>
Roles come from the process titles vLLM sets (API server processes, EngineCore) and the MPS server.
Diff two snapshots to get server CPU per run without the load generator's own CPU.
"""
import json, os, sys, time

TCK = os.sysconf("SC_CLK_TCK")


def role(comm, cmd):
    s = f"{comm} {cmd}"
    if "EngineCore" in s:
        return "engine"
    if "APIServer" in s:
        return "api"
    if "mps-server" in s or "mps-control" in s:
        return "mps"
    if "compile_worker" in s:
        return "compile"
    if "vllm" in s.lower():
        return "vllm_main"
    return None


snap = {"t": time.time(), "procs": {}}
for pid in filter(str.isdigit, os.listdir("/proc")):
    try:
        cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace").strip()
        stat = open(f"/proc/{pid}/stat").read()
    except OSError:
        continue
    comm = stat[stat.index("(") + 1: stat.rindex(")")]
    r = role(comm, cmd)
    if r is None:
        continue
    f = stat[stat.rindex(")") + 2:].split()
    snap["procs"][pid] = {"role": r, "comm": comm, "cmd": cmd[:120], "cpu_s": (int(f[11]) + int(f[12])) / TCK}
try:
    snap["cgroup_cpu_s"] = int(next(l.split()[1] for l in open("/sys/fs/cgroup/cpu.stat") if l.startswith("usage_usec"))) / 1e6
except OSError:
    pass
json.dump(snap, open(sys.argv[1], "w"))
