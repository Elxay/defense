#!/usr/bin/env bash
set -euo pipefail
model="$1"
card="$2"
source /data/HZX/Def/night/launch.sh
exec 201>"/data/HZX/Def/logs/idle_gpu${card}.lock"
flock -n 201 || exit 73
export DEVICE="cuda:${card}"
unset NOGPU
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES="$card" DEVICE=cuda:0 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True /home/kemove/anaconda3/envs/HZX_GLA/bin/python /data/HZX/Def/tools/handoff_20261106/unified300_throughput.py "$model" "$card"
