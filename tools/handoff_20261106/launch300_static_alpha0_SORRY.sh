#!/usr/bin/env bash
set -euo pipefail
source /data/HZX/Def/night/launch.sh
exec 201>/data/HZX/Def/logs/idle_gpu0.lock
flock -n 201 || exit 73
unset NOGPU
export DEVICE=cuda:0
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 /home/kemove/anaconda3/envs/HZX_GLA/bin/python /data/HZX/Def/tools/handoff_20261106/unified300_static_alpha0_sorry.py
