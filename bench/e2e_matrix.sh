#!/usr/bin/env bash
# End-to-end matrix on one B200: start vLLM (Nemotron 3 Nano Omni) with a given video decode config,
# run the live/VOD load matrix, stop. Usage: e2e_matrix.sh <label> <media-io-json> [extra vllm args...]
#   e2e_matrix.sh nvdec-mps '{"video":{"backend":"pynvvideocodec","hw_decoders":2,"fps":1,"num_frames":128}}'
#   e2e_matrix.sh cpu       '{"video":{"backend":"opencv","fps":1,"num_frames":128}}'
# Env: MPS=1 to start nvidia-cuda-mps-control; ASC (api-server-count, default 12); CPUSET (taskset list, optional).
set -u
LABEL=$1; MEDIA_IO=$2; shift 2
ASC=${ASC:-12}
MODEL=${MODEL:-nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16}
V=${VOD_DIR:-/data/vod}
LOG=/tmp/vllm_${LABEL}.log
source ~/miniconda3/etc/profile.d/conda.sh; conda activate nvdec-bench  # adjust to your env
export CUDA_VISIBLE_DEVICES=0 NVIDIA_DRIVER_CAPABILITIES=video,compute,utility OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1

cleanup() { pkill -f "^python -m vllm.entrypoints" 2>/dev/null; sleep 3; echo quit | nvidia-cuda-mps-control 2>/dev/null; }
cleanup
if [ "${MPS:-0}" = "1" ]; then nvidia-cuda-mps-control -d 2>/dev/null; sleep 1; echo "mps: $(pgrep -c nvidia-cuda-mps) procs"; fi
PIN=(); [ -n "${CPUSET:-}" ] && PIN=(taskset -c "$CPUSET")

nohup "${PIN[@]}" python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" --served-model-name omni-v1 --trust-remote-code \
  --host 0.0.0.0 --port 8000 --gpu-memory-utilization 0.85 --max-model-len 32768 \
  --api-server-count "$ASC" --max-num-batched-tokens 32768 \
  --limit-mm-per-prompt '{"video":1,"audio":1}' --media-io-kwargs "$MEDIA_IO" \
  --reasoning-parser nemotron_v3 "$@" > "$LOG" 2>&1 &
echo "server starting (asc=$ASC, media-io=$MEDIA_IO, cpuset=${CPUSET:-all}, extra: $*) -> $LOG"
for i in $(seq 1 180); do curl -sf -m 3 localhost:8000/v1/models >/dev/null 2>&1 && { echo "ready after ~$((i*10))s"; break; }; sleep 10; done
curl -sf -m 3 localhost:8000/v1/models >/dev/null || { echo "SERVER NOT READY"; grep -E "Error|Traceback" "$LOG" | tail -5; cleanup; exit 1; }

cpu() { awk '/^usage_usec/{printf "%s", $2}' /sys/fs/cgroup/cpu.stat; }
with_fps() { python -c 'import json,sys; d=json.loads(sys.argv[1]); d["video"]["fps"]=float(sys.argv[2]); print(json.dumps(d))' "$MEDIA_IO" "$1"; }
run() { # name video N audio fps   (per-request media_io_kwargs = server dict with fps overridden)
  local name=$1 video=$2 n=$3 audio=$4 fps=$5
  local u0; u0=$(cpu)
  nvidia-smi dmon -i 0 -s u -d 1 > /tmp/dmon_$LABEL.txt 2>&1 & local DM=$!
  ENDPOINT=http://localhost:8000 VIDEO=$video N=$n USE_AUDIO=$audio FPS=$fps MEDIA_IO="$(with_fps "$fps")" LABEL="$LABEL/$name" python /tmp/load_test.py 2>&1 | grep -E "===|ok=|latency|prompt_tokens|ERR"
  local u1; u1=$(cpu); kill $DM 2>/dev/null; wait $DM 2>/dev/null
  awk -v u0="$u0" -v u1="$u1" -v n="$n" 'BEGIN{printf "  server cpu: %.1f cpu-s total, %.2f cpu-s/req\n",(u1-u0)/1e6,(u1-u0)/1e6/n}'
  echo "  gpu samples (sm%/dec%): $(awk 'NR>2 && ($2>0||$5>0){printf "%s/%s ", $2, $5}' /tmp/dmon_$LABEL.txt | cut -c1-160)"
  sleep 5
}
echo "## warmup"; ENDPOINT=http://localhost:8000 VIDEO=/tmp/seg6.ts N=2 USE_AUDIO=1 MEDIA_IO="$(with_fps 2)" LABEL=warm python /tmp/load_test.py 2>&1 | grep -E "ok=|ERR"
ENDPOINT=http://localhost:8000 VIDEO=$V/enc_10s N=2 USE_AUDIO=0 MEDIA_IO="$(with_fps 1)" LABEL=warm python /tmp/load_test.py 2>&1 | grep -E "ok=|ERR"
for rep in 1 2 3; do
  echo "## rep $rep"
  run live-ts-6s-360p-audio  /tmp/seg6.ts   64 1 2
  run live-ts-6s-360p-video  /tmp/seg6.ts   64 0 2
  run vod-10s-1080p          $V/enc_10s     64 0 1
  run vod-30s-1080p          $V/enc_30s     32 0 1
  run vod-120s-1080p         $V/enc_120s     8 0 1
  run vod-10s-1080p-audio    $V/enc_10s     64 1 1
done
cleanup
echo "## done $LABEL"
