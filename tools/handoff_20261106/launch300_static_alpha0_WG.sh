#!/usr/bin/env bash
set -euo pipefail
source /home/dell/Def/tools/handoff_20261106/node01_launch_round9.sh
while ! find /home/dell/Def/results/audit/unified300/static_alpha0_WG/incoming.private -maxdepth 1 -name '*.json' -print -quit | grep -q .; do sleep 10; done
exec 201>/home/dell/Def/logs/idle_gpu0.lock
flock -n 201 || exit 73
unset NOGPU
export DEVICE=cuda:0
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True /data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/unified300_static_alpha0_wg.py
