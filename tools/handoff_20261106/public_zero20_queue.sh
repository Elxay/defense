#!/usr/bin/env bash
set -euo pipefail
cd /data/HZX/Def
source night/launch.sh
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
result=results/audit/pair500/public255/public_zero20_results.json
test ! -f "$result" || exit 0
while [ ! -f results/audit/pair500/public255/stage_manifests/harmful_judge_old_s3.json ]; do
  sleep 30
done
exec 8>>logs/idle_gpu2.lock
while true; do
  test ! -f results/audit/pair500/frozen_prompt_snapshot.json || exit 0
  if flock -n 8 && wait_gpu cuda:2; then break; fi
  flock -u 8
  sleep 1
done
DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:2 /home/kemove/anaconda3/envs/HZX_GLA/bin/python -u tools/handoff_20261106/public_zero20_check.py
