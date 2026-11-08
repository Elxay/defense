#!/usr/bin/env bash
set -euo pipefail
cd /data/HZX/Def
source night/launch.sh
py=/home/kemove/anaconda3/envs/HZX_GLA/bin/python
base=results/audit/pair500
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu2.lock
exec 7>>logs/idle_gpu3.lock
release() { flock -u 7; flock -u 8; }
trap release EXIT
state() {
  python3 - "$1" "$$" <<'PY'
import datetime,json,os,sys
from pathlib import Path
p=Path('results/audit/pair500/public255/four_window_live.json')
t=p.with_suffix('.tmp')
t.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'pid':int(sys.argv[2]),'phase':sys.argv[1]}))
os.replace(t,p)
PY
}
# Wait for the current s5 target generation, then compete only at a safe lease
# boundary. Never terminate or overlap a target worker or bypass wait_gpu.
until test -f "$base/public255/stage_manifests/harmful_generation_old_s5.json"; do
  test -f "$base/frozen_prompt_snapshot.json" && exit 0
  state waiting_s5_generation
  sleep 15
done
while true; do
  test -f "$base/frozen_prompt_snapshot.json" && exit 0
  state waiting_exclusive_gpu2_gpu3_leases
  if flock -n 8 && flock -n 7 && wait_gpu cuda:2 && wait_gpu cuda:3; then break; fi
  release
  sleep 2
done
for stage in top2 guard; do
  test -f "$base/frozen_prompt_snapshot.json" && exit 0
  state "$stage"
  DEVICE=cuda:2 launch_job env CUDA_VISIBLE_DEVICES=2,3 DEVICE=cuda:2 "$py" -u tools/handoff_20261106/wjb_four_window.py "$stage"
done
release
state aggregating
NOGPU=1 launch_job "$py" tools/handoff_20261106/wjb_four_analysis.py
NOGPU=1 launch_job "$py" tools/handoff_20261106/wjb_four_export.py
state complete
