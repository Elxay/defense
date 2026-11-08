#!/usr/bin/env bash
set -euo pipefail
cd /data/HZX/Def
source night/launch.sh
py=/home/kemove/anaconda3/envs/HZX_GLA/bin/python
worker=tools/handoff_20261106/wjb_eval255_run.py
stage=tools/handoff_20261106/wjb_eval255_stage.py
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu2.lock
exec 7>>logs/idle_gpu3.lock
names=(old_s7 old_s0 SYS_A SYS_B)
export WJB_POST_SNAPSHOT_MODE=post_pair
if [ "$#" -gt 0 ]; then
  names=("$@")
  export WJB_POST_SNAPSHOT_MODE=last_condition
fi
for name in "${names[@]}"; do
  case "$name" in old_s7|old_s0|SYS_A|SYS_B) ;; *) exit 2 ;; esac
  while true; do
    if flock -n 8 && flock -n 7 && wait_gpu cuda:2 && wait_gpu cuda:3; then break; fi
    flock -u 7; flock -u 8; sleep 30
  done
  "$py" "$stage" harmful_generation --detail "$name"
  DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:2 "$py" -u "$worker" harmful "$name" --shard 0 &
  a=$!
  DEVICE=cuda:3 launch_job env CUDA_VISIBLE_DEVICES=3 DEVICE=cuda:3 "$py" -u "$worker" harmful "$name" --shard 1 &
  b=$!
  ra=0; rb=0
  wait "$a" || ra=$?
  wait "$b" || rb=$?
  test "$ra" -eq 0 && test "$rb" -eq 0
  "$py" "$stage" harmful_generation --detail "$name" --complete
  until wait_gpu cuda:2 && wait_gpu cuda:3; do sleep 5; done
  "$py" "$stage" harmful_judge --detail "$name"
  DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2,3 DEVICE=cuda:2 "$py" -u "$worker" score "$name"
  "$py" "$stage" harmful_judge --detail "$name" --complete
  flock -u 7; flock -u 8
done
