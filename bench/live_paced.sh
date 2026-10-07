#!/usr/bin/env bash
# Paced live-stream load on one B200: start vLLM (Nemotron 3 Nano Omni) with a given video decode config, then
# for each stream count K run K live streams that each send one segment every INTERVAL s for DURATION s (open
# loop, load_test.py STREAMS mode), and record latency, deadline misses, server CPU and GPU utilization.
# Usage: live_paced.sh <label> <media-io-json> [extra vllm args...]
#   MPS=1 live_paced.sh nvdec-mps '{"video":{"backend":"pynvvideocodec","hw_decoders":2,"fps":1,"num_frames":128}}'
#   live_paced.sh cpu       '{"video":{"backend":"opencv","fps":1,"num_frames":128}}'
# Env: STREAMS_LIST ("32 64 128 192"), DURATION (300), INTERVAL (6), VIDEO (/tmp/seg6.ts; file or directory of
#      segments), FPS (2), USE_AUDIO (0), UNIQUE (1 = per-request uuid, so vLLM's caches miss as for unique live
#      segments); MPS, ASC, CPUSET as in e2e_matrix.sh; PORT (8000), CGROUP_CPU (/sys/fs/cgroup/cpu.stat).
# Server CPU = pod cgroup delta minus load_test.py's own CPU (the client runs in the same pod).
set -u
LABEL=$1; MEDIA_IO=$2; shift 2
ASC=${ASC:-12}
MODEL=${MODEL:-nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16}
STREAMS_LIST=${STREAMS_LIST:-32 64 128 192}
DURATION=${DURATION:-300}; INTERVAL=${INTERVAL:-6}; FPS=${FPS:-2}
VIDEO=${VIDEO:-/tmp/seg6.ts}; USE_AUDIO=${USE_AUDIO:-0}; UNIQUE=${UNIQUE:-1}
PORT=${PORT:-8000}; CGROUP_CPU=${CGROUP_CPU:-/sys/fs/cgroup/cpu.stat}
HERE=$(cd "$(dirname "$0")" && pwd)
LOG=/tmp/vllm_paced_${LABEL}.log; DMON=/tmp/dmon_paced_${LABEL}.txt
source ~/miniconda3/etc/profile.d/conda.sh; conda activate nvdec-bench  # adjust to your env
export CUDA_VISIBLE_DEVICES=0 NVIDIA_DRIVER_CAPABILITIES=video,compute,utility OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1
[ -r "$CGROUP_CPU" ] || echo "WARN: $CGROUP_CPU not readable; server cpu below will be wrong"

cleanup() { pkill -f "^python -m vllm.entrypoints" 2>/dev/null; sleep 3; echo quit | nvidia-cuda-mps-control 2>/dev/null; }
cleanup
if [ "${MPS:-0}" = "1" ]; then nvidia-cuda-mps-control -d 2>/dev/null; sleep 1; echo "mps: $(pgrep -c nvidia-cuda-mps) procs"; fi
PIN=(); [ -n "${CPUSET:-}" ] && PIN=(taskset -c "$CPUSET")

nohup "${PIN[@]}" python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" --served-model-name omni-v1 --trust-remote-code \
  --host 0.0.0.0 --port "$PORT" --gpu-memory-utilization 0.85 --max-model-len 32768 \
  --api-server-count "$ASC" --max-num-batched-tokens 32768 \
  --limit-mm-per-prompt '{"video":1,"audio":1}' --media-io-kwargs "$MEDIA_IO" \
  --reasoning-parser nemotron_v3 "$@" > "$LOG" 2>&1 &
echo "server starting (asc=$ASC, media-io=$MEDIA_IO, cpuset=${CPUSET:-all}, extra: $*) -> $LOG"
for i in $(seq 1 180); do curl -sf -m 3 "localhost:$PORT/v1/models" >/dev/null 2>&1 && { echo "ready after ~$((i*10))s"; break; }; sleep 10; done
curl -sf -m 3 "localhost:$PORT/v1/models" >/dev/null || { echo "SERVER NOT READY"; grep -E "Error|Traceback" "$LOG" | tail -5; cleanup; exit 1; }

cpu() { awk '/^usage_usec/{printf "%s", $2}' "$CGROUP_CPU"; }
with_fps() { python -c 'import json,sys; d=json.loads(sys.argv[1]); d["video"]["fps"]=float(sys.argv[2]); print(json.dumps(d))' "$MEDIA_IO" "$1"; }
run() { # K   (one sweep step: K streams for DURATION s)
  local k=$1 u0 u1 out DM
  echo "## K=$k streams, $(awk -v k="$k" -v i="$INTERVAL" 'BEGIN{printf "%.1f", k/i}') req/s offered for ${DURATION}s"
  u0=$(cpu)
  nvidia-smi dmon -i 0 -s u -d 1 > "$DMON" 2>&1 & DM=$!
  out=$(ENDPOINT=http://localhost:$PORT VIDEO=$VIDEO STREAMS=$k INTERVAL=$INTERVAL DURATION=$DURATION UNIQUE=$UNIQUE \
        USE_AUDIO=$USE_AUDIO FPS=$FPS MEDIA_IO="$(with_fps "$FPS")" LABEL="$LABEL/live-paced-k$k" python "$HERE/load_test.py" 2>&1)
  u1=$(cpu); kill $DM 2>/dev/null; wait $DM 2>/dev/null
  echo "$out" | grep -E "===|sent=|latency|late|send lag|prompt_tokens|ERR|Error"
  # key=value tokens of load_test.py's summary -> sent, wall, user, sys (client cpu)
  echo "$out" | awk -v u0="$u0" -v u1="$u1" '
    { for (i = 1; i <= NF; i++) if (split($i, kv, "=") == 2) { v = kv[2]; sub(/s$/, "", v); f[kv[1]] = v } }
    END { if (f["sent"] > 0) { c = f["user"] + f["sys"]; s = (u1 - u0) / 1e6 - c
          printf "  server cpu: %.2f cpu-s total (client %.2f excluded), %.3f cpu-s/req, %.2f cores avg\n", s, c, s / f["sent"], s / f["wall"] } }'
  awk '$1 !~ /^#/ && NF >= 5 { n++; sm += $2; dec += $5; if ($2 > msm) msm = $2; if ($5 > mdec) mdec = $5 }
       END { if (n) printf "  gpu sm%% avg %.0f max %d, dec%% avg %.0f max %d (%d samples)\n", sm / n, msm, dec / n, mdec, n }' "$DMON"
  sleep 5
}
echo "## warmup ($((2*ASC)) requests across the API servers)"
ENDPOINT=http://localhost:$PORT VIDEO=$VIDEO STREAMS=0 N=$((2*ASC)) USE_AUDIO=$USE_AUDIO FPS=$FPS MEDIA_IO="$(with_fps "$FPS")" \
  LABEL=warm python "$HERE/load_test.py" 2>&1 | grep -E "ok=|ERR"
for k in $STREAMS_LIST; do run "$k"; done
cleanup
echo "## done $LABEL"
