#!/usr/bin/env bash
set -euo pipefail
source /data/HZX/Def/night/launch.sh
exec 201>/data/HZX/Def/logs/idle_gpu2.lock
flock -n 201 || exit 73
unset NOGPU
export DEVICE=cuda:2
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:0 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True /home/kemove/anaconda3/envs/HZX_GLA/bin/python /data/HZX/Def/tools/handoff_20261106/unified300_language_alpha0.py llama 2
