#!/usr/bin/env bash
set -euo pipefail
cd /home/dell/Def
source tools/handoff_20261106/node01_launch_round9.sh
out=results/audit/pair500
exec 8>>logs/idle_gpu1.lock
exec 7>>logs/idle_gpu2.lock
flock 8
flock 7
export DEVICE=cuda:1 CUDA_VISIBLE_DEVICES=1,2
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 TOKENIZERS_PARALLELISM=false
until wait_gpu cuda:1 && wait_gpu cuda:2; do sleep 10; done
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/pilot_leases_held"
trap 'code=$?; if [ "$code" -ne 0 ]; then printf "%s\n" "$code" > "$out/pilot_failed"; fi' EXIT
target=/data/ray/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
launch_job /data/ray/env/bin/python -u tools/handoff_20261106/pair500_generate.py --root /home/dell/Def --attacker /data/ray/pair500_models/qwen3_8b --target "$target" --limit 10
launch_job /data/ray/env/bin/python -u tools/handoff_20261106/pair500_score.py --root /home/dell/Def --judge /data/ray/judge13b --mode classifier --limit 10
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/pilot_node_complete"
