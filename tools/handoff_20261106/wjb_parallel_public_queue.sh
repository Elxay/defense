#!/usr/bin/env bash
# Activate at a condition boundary after the current supervisor has yielded.
set -euo pipefail
cd /data/HZX/Def
source night/launch.sh
py=/home/kemove/anaconda3/envs/HZX_GLA/bin/python
worker=tools/handoff_20261106/wjb_eval255_run.py
export USE_TF=0 USE_FLAX=0 HF_HUB_OFFLINE=1
exec 8>>logs/idle_gpu2.lock
exec 7>>logs/idle_gpu3.lock
ready() { test -f results/audit/pair500/frozen_prompt_snapshot.json; }
release() { flock -u 7; flock -u 8; }
acquire() {
  while ! ready; do
    if flock -n 8 && flock -n 7 && wait_gpu cuda:2 && wait_gpu cuda:3; then return; fi
    release
    sleep 30
  done
  return 1
}
run() {
  local card="$1"
  shift
  until wait_gpu "cuda:$card"; do sleep 5; done
  DEVICE="cuda:$card" launch_job env CUDA_VISIBLE_DEVICES="$card" DEVICE="cuda:$card" "$py" -u "$worker" "$@"
}
harmful=(old_s3 rand0 old_s4 rand1 old_s5 rand2 old_s6 rand3 old_s7 old_s0 SYS_A SYS_B)
public=(old_s3 old_s4 old_s5 old_s6 old_s7 rand0 rand1 rand2 rand3)
for i in "${!harmful[@]}"; do
  acquire || break
  name="${harmful[$i]}"
  run 2 harmful "$name" --shard 0 &
  a=$!
  (
    if [ "$i" -lt "${#public[@]}" ]; then
      run 3 public "${public[$i]}" --shard 0
      ready || run 3 public "${public[$i]}" --shard 1
    fi
    ready || run 3 harmful "$name" --shard 1
  ) &
  b=$!
  ra=0; rb=0
  wait "$a" || ra=$?
  wait "$b" || rb=$?
  test "$ra" -eq 0 && test "$rb" -eq 0
  if ready; then release; break; fi
  "$py" tools/handoff_20261106/wjb_eval255_stage.py harmful_generation --detail "$name" --complete
  until wait_gpu cuda:2 && wait_gpu cuda:3; do sleep 5; done
  DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2,3 DEVICE=cuda:2 "$py" -u "$worker" score "$name"
  "$py" tools/handoff_20261106/wjb_eval255_stage.py harmful_judge --detail "$name" --complete
  release
  "$py" tools/handoff_20261106/wjb_eval255_report.py
done
