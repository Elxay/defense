#!/usr/bin/env bash
set -euo pipefail
cd /data/HZX/Def
source night/launch.sh
py=/home/kemove/anaconda3/envs/HZX_GLA/bin/python
worker=tools/handoff_20261106/wjb_eval255_run.py
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu2.lock
flock 8
until wait_gpu cuda:2; do sleep 15; done
for shard in 0 1; do
  DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:2 "$py" -u "$worker" harmful old_s7 --shard "$shard"
done
# The original queue still owns the normal judge stages. This wrapper neither
# judges nor reads effects, and releases GPU2 before any dual-card classifier.
