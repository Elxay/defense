#!/usr/bin/env bash
set -euo pipefail
source /data/HZX/Def/night/launch.sh
exec 201>/data/HZX/Def/logs/idle_gpu0.lock
flock -n 201 || exit 73
export DEVICE=cuda:0
unset NOGPU
for model in llama qwen; do
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 /home/kemove/anaconda3/envs/HZX_GLA/bin/python /data/HZX/Def/tools/handoff_20261106/unified300_parallel_device20.py /data/HZX/Def "$model" 0 innet_gpu0
done
