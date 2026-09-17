#!/usr/bin/env bash
# Full PoC chain on one B200 (GPU 0). Output: /tmp/run_all.log (+ per-stage logs).
set -u
source ~/miniconda3/etc/profile.d/conda.sh; conda activate nvdec-bench  # adjust to your env
export CUDA_VISIBLE_DEVICES=0 NVIDIA_DRIVER_CAPABILITIES=video,compute,utility OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1
V=${VOD_DIR:-/data/vod}
stage() { echo; echo "######## $(date -u +%H:%M:%S) $*"; }

stage "wait for model download"
while pgrep -f "hf download" >/dev/null; do sleep 15; done
echo "download done: $(du -sh ~/.cache/huggingface/hub/models--nvidia--Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 | cut -f1)"

echo quit | nvidia-cuda-mps-control 2>/dev/null; sleep 1
stage "A. raw decode, MPS off"
python /tmp/raw_decode_bench.py $V/enc_10s/$(ls $V/enc_10s | head -1) --procs 1 2 4 8 16 --reps 3
python /tmp/raw_decode_bench.py /tmp/seg6.ts --procs 1 4 8 16 --reps 5

stage "A'. raw decode NVDEC, MPS on"
nvidia-cuda-mps-control -d; sleep 1
python /tmp/raw_decode_bench.py $V/enc_10s/$(ls $V/enc_10s | head -1) --procs 1 2 4 8 16 --reps 3 --backends nvdec
python /tmp/raw_decode_bench.py /tmp/seg6.ts --procs 1 4 8 16 --reps 5 --backends nvdec
echo quit | nvidia-cuda-mps-control; sleep 1

stage "B. vLLM loader decode stage (sampled frames), 3 reps"
for rep in 1 2 3; do
  echo "--- rep $rep"
  HW_DECODERS=2 python /tmp/vod_loader_bench.py $V/enc_10s 1 32 8
  HW_DECODERS=2 python /tmp/vod_loader_bench.py $V/enc_30s 1 16 8
  HW_DECODERS=2 python /tmp/vod_loader_bench.py $V/enc_120s 1 8 8
  HW_DECODERS=2 python /tmp/vod_loader_bench.py /tmp/seg6.ts 2 32 8
done 2>&1 | grep -vE "^\s*$|Warning|warn"

stage "C. E2E Nemotron 3 Nano Omni, NVDEC + MPS"
MPS=1 bash /tmp/e2e_matrix.sh nvdec-mps '{"video":{"backend":"pynvvideocodec","hw_decoders":2,"fps":1,"num_frames":128}}'

stage "C. E2E Nemotron 3 Nano Omni, CPU (OpenCV)"
bash /tmp/e2e_matrix.sh cpu-opencv '{"video":{"backend":"opencv","fps":1,"num_frames":128}}'

stage "ALL DONE"
