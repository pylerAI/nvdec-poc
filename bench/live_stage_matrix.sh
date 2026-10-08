#!/usr/bin/env bash
# Live 6 s 360p MPEG-TS, per-stage matrix on one B200: start vLLM (Nemotron 3 Nano Omni) with the stage timers in
# bench/stagetime, serve a distinct copy of one segment per request over HTTP (bench/make_variants.py +
# bench/seg_server.py: every request misses every cache, like live-ingest), and run sequential requests (per-request
# stage cost) and 64-request bursts (latency under load), audio+video and video-only.
# Usage: live_stage_matrix.sh <label> <media-io-json> [extra vllm args...]
#   MPS=1 live_stage_matrix.sh nvdec-mps '{"video":{"backend":"pynvvideocodec","hw_decoders":2,"fps":2,"num_frames":128}}'
#         live_stage_matrix.sh cpu-opencv '{"video":{"backend":"opencv","fps":2,"num_frames":128}}'
# Env: MPS=1 to start CUDA MPS; ASC (api-server-count, default 12); SERVE=vllm (default, `vllm serve`: ASC API-server
#      processes) or SERVE=module (`python -m vllm.entrypoints.openai.api_server`, as bench/e2e_matrix.sh: vLLM 0.28.0
#      ignores --api-server-count there and runs ONE API-server process); SEG (variants dir or one .ts); VENV;
#      N1 (sequential requests, default 24); REPS (64-burst repetitions, default 3); STAGE_TIMING=0 to run without
#      timers. Output: $OUT (default ~/nvdec-runs/<label>-<time>/)
set -u
LABEL=$1; MEDIA_IO=$2; shift 2
ASC=${ASC:-12}; N1=${N1:-24}; REPS=${REPS:-3}; BURSTS=${BURSTS:-64}   # BURSTS="8 64": burst concurrency levels
MODEL=${MODEL:-nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16}
# Server shape; defaults reproduce bench/e2e_matrix.sh (Nemotron). For the production Qwen3-Omni shape set
# REASONING_PARSER= (empty), MAX_MODEL_LEN/MAX_BATCHED 49152, GPU_UTIL 0.9, MM_KWARGS, STRUCTURED (see values.yaml).
REASONING_PARSER=${REASONING_PARSER-nemotron_v3}; MAX_MODEL_LEN=${MAX_MODEL_LEN:-32768}; MAX_BATCHED=${MAX_BATCHED:-32768}
GPU_UTIL=${GPU_UTIL:-0.85}; MM_KWARGS=${MM_KWARGS:-}; STRUCTURED=${STRUCTURED:-}
SHAPE=(); [ -n "$REASONING_PARSER" ] && SHAPE+=(--reasoning-parser "$REASONING_PARSER")
[ -n "$MM_KWARGS" ] && SHAPE+=(--mm-processor-kwargs "$MM_KWARGS"); [ -n "$STRUCTURED" ] && SHAPE+=(--structured-outputs-config "$STRUCTURED")
SEG=${SEG:-$HOME/nvdec-runs/variants}; [ -e "$SEG" ] || SEG=/gpfs/private/garam/nvdec-bench-2026-09-17/seg6.ts
BENCH=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-$HOME/nvdec-runs/$LABEL-$(date +%m%d-%H%M)}; mkdir -p "$OUT/stages"
source "${VENV:-$HOME/venvs/nvdec-bench}/bin/activate"
export CUDA_VISIBLE_DEVICES=0 NVIDIA_DRIVER_CAPABILITIES=video,compute,utility OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1
export CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps-$USER CUDA_MPS_LOG_DIRECTORY=$HOME/nvdec-runs/mps-log
mkdir -p "$CUDA_MPS_PIPE_DIRECTORY" "$CUDA_MPS_LOG_DIRECTORY"
now() { date +%s.%N; }

cleanup() {
  pkill -f "vllm.entrypoints.openai.api_server|vllm serve" 2>/dev/null; pkill -f "seg_server.py" 2>/dev/null; sleep 5
  pkill -f "^VLLM::" 2>/dev/null; sleep 1
  echo quit | nvidia-cuda-mps-control 2>/dev/null; sleep 1
}
cleanup
if [ "${MPS:-0}" = "1" ]; then nvidia-cuda-mps-control -d; sleep 1; echo "mps: $(pgrep -fc nvidia-cuda-mps) procs"; fi
python "$BENCH/seg_server.py" "$SEG" 8890 & SEGSRV=$!

TIMERS=(); [ "${STAGE_TIMING:-1}" = "1" ] && TIMERS=(env "STAGE_TIMING_DIR=$OUT/stages" "PYTHONPATH=$BENCH/stagetime${PYTHONPATH:+:$PYTHONPATH}")
if [ "${SERVE:-vllm}" = "module" ]; then LAUNCH=(python -m vllm.entrypoints.openai.api_server --model "$MODEL"); else LAUNCH=(vllm serve "$MODEL"); fi
nohup "${TIMERS[@]}" "${LAUNCH[@]}" --served-model-name omni-v1 --trust-remote-code \
  --host 0.0.0.0 --port 8000 --gpu-memory-utilization "$GPU_UTIL" --max-model-len "$MAX_MODEL_LEN" \
  --api-server-count "$ASC" --max-num-batched-tokens "$MAX_BATCHED" \
  --limit-mm-per-prompt '{"video":1,"audio":1}' --media-io-kwargs "$MEDIA_IO" \
  "${SHAPE[@]}" "$@" > "$OUT/vllm.log" 2>&1 &
echo "server starting (label=$LABEL model=$MODEL serve=${SERVE:-vllm} asc=$ASC seg=$SEG media-io=$MEDIA_IO shape: ${SHAPE[*]} timers=${STAGE_TIMING:-1} extra: $*) -> $OUT"
echo "request shape: SYSTEM_PROMPT=${SYSTEM_PROMPT:+set} PROMPT=${PROMPT:-default} MAX_TOKENS=${MAX_TOKENS:-64} RESPONSE_FORMAT=${RESPONSE_FORMAT:+set} VIDEO_URL_FPS=${VIDEO_URL_FPS:-}"
for i in $(seq 1 180); do curl -sf -m 3 localhost:8000/v1/models >/dev/null 2>&1 && { echo "ready after ~$((i*10))s"; break; }; sleep 10; done
curl -sf -m 3 localhost:8000/v1/models >/dev/null || { echo "SERVER NOT READY"; grep -E "Error|Traceback" "$OUT/vllm.log" | tail -5; cleanup; exit 1; }

run() { # name n concurrency audio
  local name=$1 n=$2 c=$3 audio=$4 t0 t1
  python "$BENCH/proc_cpu.py" "$OUT/cpu_${name}_0.json"; curl -s localhost:8000/metrics > "$OUT/metrics_${name}_0.txt"
  nvidia-smi dmon -i 0 -s u -d 1 > "$OUT/dmon_${name}.txt" 2>&1 & local DM=$!
  t0=$(now)
  N=$n CONCURRENCY=$c USE_AUDIO=$audio MEDIA_IO="$MEDIA_IO" KEY="$LABEL-$name-$(date +%s)" LABEL="$LABEL/$name" \
    OUT="$OUT/requests.jsonl" python "$BENCH/live_load.py"
  t1=$(now); kill $DM 2>/dev/null; wait $DM 2>/dev/null
  python "$BENCH/proc_cpu.py" "$OUT/cpu_${name}_1.json"; curl -s localhost:8000/metrics > "$OUT/metrics_${name}_1.txt"
  echo "{\"name\": \"$name\", \"n\": $n, \"concurrency\": $c, \"audio\": $audio, \"t0\": $t0, \"t1\": $t1}" >> "$OUT/runs.jsonl"
  echo "  gpu samples (sm%/dec%): $(awk 'NR>2 && ($2>0||$5>0){printf "%s/%s ", $2, $5}' "$OUT/dmon_${name}.txt" | cut -c1-160)"
  sleep 5
}
echo "## warmup (bursts so that every API server compiles its video/audio paths)"
for w in 1 2; do run warm${w}-av 64 64 1; run warm${w}-v 64 64 0; done
echo "## sequential: per-request stage cost"
run seq-av "$N1" 1 1
run seq-v "$N1" 1 0
for rep in $(seq 1 "$REPS"); do
  for c in $BURSTS; do
    echo "## burst rep $rep, concurrency $c"
    if [ "$c" = 64 ]; then sfx=""; else sfx="-c$c"; fi
    run burst${rep}${sfx}-av "$c" "$c" 1
    run burst${rep}${sfx}-v "$c" "$c" 0
  done
done
cp "$BENCH"/stagetime/sitecustomize.py "$OUT/" 2>/dev/null
kill $SEGSRV 2>/dev/null
cleanup
echo "## done $LABEL -> $OUT"
