#!/usr/bin/env bash
set -euo pipefail
cd /data/HZX/Def
source night/launch.sh
export NOGPU=1
deadline=$(date -u -d '2026-11-09 15:00:00 UTC' +%s)
base=results/audit/pair500
before_stop() { test "$(date -u +%s)" -lt "$deadline"; }
ready() {
  local phase
  phase=$(python3 -c 'import json; print(json.load(open("results/audit/pair500/full_queue_live.json"))["phase"])')
  case "$phase" in
    prompts_frozen|canonical_innet_evaluation_queued|complete) return 0;;
    *) return 1;;
  esac
}
while before_stop && ! ready; do sleep 60; done
if ! before_stop; then
  printf '%s deferred work reached original cutoff before node01 release\n' "$(date -u +%FT%TZ)"
  exit 0
fi
printf '%s node01 search released; resuming third-arm grid on the same host and cards\n' "$(date -u +%FT%TZ)"
launch_job env USE_TF=0 USE_FLAX=0 /home/kemove/anaconda3/envs/HZX_GLA/bin/python -u tools/handoff_20261106/round11_plain_pipeline.py
if before_stop; then
  ssh node01 'cd /home/dell/Def; source tools/handoff_20261106/node01_launch_round9.sh; export NOGPU=1; launch_job python3 -u tools/handoff_20261106/round12_same_alpha_launcher.py --seed 5'
fi
