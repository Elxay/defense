#!/usr/bin/env bash
set -euo pipefail
source /home/dell/Def/tools/handoff_20261106/node01_launch_round9.sh
exec 201>/home/dell/Def/logs/idle_gpu1.lock
flock -n 201 || exit 73
export DEVICE=cuda:1
unset NOGPU
for model in llama qwen; do
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES=1 DEVICE=cuda:0 /data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/unified300_parallel_device20.py /home/dell/Def "$model" 1 node01_gpu1
done
