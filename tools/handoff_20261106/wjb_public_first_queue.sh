#!/usr/bin/env bash
set -euo pipefail
cd /data/HZX/Def
source night/launch.sh
base=results/audit/pair500
py=/home/kemove/anaconda3/envs/HZX_GLA/bin/python
worker=tools/handoff_20261106/wjb_eval255_run.py
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu2.lock
exec 7>>logs/idle_gpu3.lock
ready() { test -f "$base/frozen_prompt_snapshot.json"; }
release() { flock -u 7; flock -u 8; }
stage() {
  "$py" tools/handoff_20261106/wjb_eval255_stage.py "$@"
}
trap 'stage failed --detail "line=$LINENO exit=$?"; release' ERR
acquire() {
  while ! ready; do
    if flock -n 8 && flock -n 7 && wait_gpu cuda:2 && wait_gpu cuda:3; then return 0; fi
    release
    sleep 30
  done
  return 1
}
report() { "$py" tools/handoff_20261106/wjb_eval255_report.py; }
dual() {
  local stage="$1" name="$2" a b ra=0 rb=0
  DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:2 "$py" -u "$worker" "$stage" "$name" --shard 0 &
  a=$!
  DEVICE=cuda:3 launch_job env CUDA_VISIBLE_DEVICES=3 DEVICE=cuda:3 "$py" -u "$worker" "$stage" "$name" --shard 1 &
  b=$!
  wait "$a" || ra=$?
  wait "$b" || rb=$?
  test "$ra" -eq 0 && test "$rb" -eq 0
}
score() {
  DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2,3 DEVICE=cuda:2 "$py" -u "$worker" score "$@"
}
stage public_first_priority
for name in old_s3 old_s4 old_s5 old_s6 old_s7 rand0 rand1 rand2 rand3; do
  acquire || exit 0
  stage public_generation --detail "$name"
  dual public "$name"
  stage public_generation --detail "$name" --complete
  release
  report
done
for name in old_s3 rand0 old_s4 rand1 old_s5 rand2 old_s6 rand3 old_s7 old_s0 SYS_A SYS_B; do
  acquire || break
  stage harmful_generation --detail "$name"
  dual harmful "$name"
  stage harmful_generation --detail "$name" --complete
  release
  ready && break
  acquire || break
  stage harmful_judge --detail "$name"
  score "$name"
  stage harmful_judge --detail "$name" --complete
  release
  report
done
report
