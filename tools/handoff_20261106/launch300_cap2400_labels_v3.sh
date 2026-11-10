#!/usr/bin/env bash
set -euo pipefail
source /home/dell/Def/tools/handoff_20261106/node01_launch_round9.sh
exec 201>/home/dell/Def/logs/idle_gpu0.lock
flock -n 201 || exit 73
unset NOGPU
export DEVICE=cuda:0
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 /data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/unified300_acceptance_label_gate2400_v3.py
