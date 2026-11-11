#!/usr/bin/env bash
set -euo pipefail
source /home/dell/Def/tools/handoff_20261106/node01_launch_round9.sh
exec 201>/home/dell/Def/logs/idle_gpu2.lock
flock -n 201 || exit 73
export DEVICE=cuda:2
unset NOGPU
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:0 /data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/unified300_translation_diagnostic.py
