#!/bin/bash
set -euo pipefail
source /data/HZX/Def/night/launch.sh
cd /data/HZX/Def
card="$1"
seed="$2"
case "$card:$seed" in 2:2|3:3) ;; *) exit 2;; esac
exec 8>>"/data/HZX/Def/logs/idle_gpu${card}.lock"
flock 8
export DEVICE="cuda:$card"
while ! wait_gpu "$DEVICE"; do sleep 30; done
launch_job env CUDA_VISIBLE_DEVICES="$card" HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 python -u /data/HZX/Def/tools/handoff_20261106/round6_rand_generate.py --seed "$seed" --physical-card "$card"
