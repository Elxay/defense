#!/usr/bin/env bash
set -euo pipefail
cd /data/HZX/Def
source night/launch.sh
py=/home/kemove/anaconda3/envs/HZX_GLA/bin/python
base=results/audit/pair500
stage=tools/handoff_20261106/wjb_eval255_stage.py
coverage=tools/handoff_20261106/wjb_generation_coverage.py
worker=tools/handoff_20261106/wjb_eval255_run.py
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
paused() {
  python3 - <<'PY'
import json
from pathlib import Path
p=Path('results/audit/pair500/pair_priority_trigger.json')
raise SystemExit(0 if p.exists() and json.loads(p.read_text()).get('active') else 1)
PY
}
until "$py" "$coverage" rand3 generation && "$py" "$coverage" old_s7 generation; do
  paused && exit 75
  sleep 30
done
exec 8>>logs/idle_gpu2.lock
exec 7>>logs/idle_gpu3.lock
while true; do
  paused && exit 75
  if flock -n 8 && flock -n 7 && wait_gpu cuda:2 && wait_gpu cuda:3; then break; fi
  flock -u 7; flock -u 8; sleep 30
done
"$py" "$stage" harmful_generation --detail old_s7 --complete
"$py" "$stage" harmful_judge --detail old_s7
# One load, one fresh model preflight and reference20 gate; fixed scoring order.
DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2,3 DEVICE=cuda:2 "$py" -u "$worker" score rand3 old_s7
for name in rand3 old_s7; do
  "$py" "$coverage" "$name" score
  "$py" "$stage" harmful_judge --detail "$name" --complete
done
flock -u 7; flock -u 8
"$py" - <<'PY'
from pathlib import Path
import datetime,json
p=Path('results/audit/pair500/prefix254/wjb_primary_hb_window_complete.json')
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'s0_systems_deferred_until_PAIR_evaluation':True},indent=2)+'\n')
PY
