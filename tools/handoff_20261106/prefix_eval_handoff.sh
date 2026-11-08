#!/usr/bin/env bash
set -euo pipefail
cd /data/HZX/Def
py=/home/kemove/anaconda3/envs/HZX_GLA/bin/python
while [ ! -f results/audit/pair500/prefix254/generation_hb_guard_complete.json ]; do
  "$py" - <<'PY'
import json
from pathlib import Path
p=Path('results/audit/pair500/prefix254/controller_live.json')
if p.exists() and json.loads(p.read_text()).get('phase')=='failed':
    raise SystemExit('Prefix/portable evaluator failed; retain checkpoints, no gate relaxation.')
PY
  sleep 30
done
# The original parent controller can now run its native-alpha0 diagnostic and
# record completion. No report or outcome aggregation is invoked by this shim.
