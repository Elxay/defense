#!/usr/bin/env bash
set -euo pipefail
cd /data/HZX/Def
source night/launch.sh
exec 8>>logs/idle_gpu2.lock
exec 7>>logs/idle_gpu3.lock
# Wait for the row-count controller's decision, including the one-condition
# exemption, before acquiring the cards from an unfinished WJB tail.
while ! test -f results/audit/pair500/pair_priority_trigger.json; do sleep 5; done
while ! python3 - <<'PY'
import json
from pathlib import Path
x=json.loads(Path('results/audit/pair500/pair_priority_trigger.json').read_text())
raise SystemExit(int(bool(x.get('last_condition_exemption')) and not x.get('exemption_completed_utc')))
PY
do sleep 5; done
while true; do
  if flock -n 8 && flock -n 7 && wait_gpu cuda:2 && wait_gpu cuda:3; then break; fi
  flock -u 7
  flock -u 8
  sleep 30
done
py=/home/kemove/anaconda3/envs/HZX_GLA/bin/python
worker=tools/handoff_20261106/pair500_eval254.py
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
generate() {
  local condition="$1" a b ra=0 rb=0
  DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:2 "$py" -u "$worker" gen --condition "$condition" --shard 0 &
  a=$!
  DEVICE=cuda:3 launch_job env CUDA_VISIBLE_DEVICES=3 DEVICE=cuda:3 "$py" -u "$worker" gen --condition "$condition" --shard 1 &
  b=$!
  wait "$a" || ra=$?
  wait "$b" || rb=$?
  test "$ra" -eq 0 && test "$rb" -eq 0
}
evaluate() {
  until wait_gpu cuda:2 && wait_gpu cuda:3; do sleep 5; done
  DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2,3 DEVICE=cuda:2 "$py" -u "$worker" classifier "$@"
  NOGPU=1 launch_job env DEVICE=cpu "$py" -u "$worker" hash "$@"
}
generate alpha0
evaluate --condition alpha0
DEVICE=cpu "$py" tools/handoff_20261106/pair500_read_gate.py --prepare-baseline
conditions=()
for condition in old_s3 rand0 old_s4 rand1 old_s5 rand2 old_s6 rand3 old_s7 old_s0 SYS_A SYS_B; do
  generate "$condition"
  conditions+=(--condition "$condition")
done
evaluate "${conditions[@]}"
until wait_gpu cuda:2; do sleep 5; done
DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:2 "$py" -u "$worker" guard
# Conditional summaries require all nine units under BOTH judges. The previous
# automatic HB-only full report is intentionally not invoked here.
DEVICE=cpu "$py" tools/handoff_20261106/pair500_read_gate.py --status
