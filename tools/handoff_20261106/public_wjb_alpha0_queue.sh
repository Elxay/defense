#!/usr/bin/env bash
set -eu
cd /data/HZX/Def
source night/launch.sh
exec 8>>logs/idle_gpu2.lock
exec 7>>logs/idle_gpu3.lock
flock -n 8
flock -n 7
wait_gpu cuda:2
wait_gpu cuda:3
py=/home/kemove/anaconda3/envs/HZX_GLA/bin/python
worker=tools/handoff_20261106/public_wjb_alpha0_gate.py
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
seconds=$(( $(date -u -d '2026-11-07 14:50:00 UTC' +%s) - $(date -u +%s) ))
test "$seconds" -gt 0
DEVICE=cuda:2 launch_job timeout --foreground "$seconds" env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:2 "$py" -u "$worker" gen --shard 0 &
a=$!
DEVICE=cuda:3 launch_job timeout --foreground "$seconds" env CUDA_VISIBLE_DEVICES=3 DEVICE=cuda:3 "$py" -u "$worker" gen --shard 1 &
b=$!
ra=0; wait "$a" || ra=$?
rb=0; wait "$b" || rb=$?
printf 'generation exits %s %s\n' "$ra" "$rb"
seconds=$(( $(date -u -d '2026-11-07 14:50:00 UTC' +%s) - $(date -u +%s) ))
test "$seconds" -gt 30
DEVICE=cuda:2 launch_job timeout --foreground "$seconds" env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:2 "$py" -u "$worker" proxy
