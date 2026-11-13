#!/usr/bin/env bash
source /home/dell/Def/night/launch_node01.sh
declare -F wait_gpu >/dev/null && declare -F launch_job >/dev/null || exit 1
set -e
export DEVICE=cuda:2
while ! wait_gpu "$DEVICE"; do sleep 10; done
mkdir -p /home/dell/Def/results/audit/unified300/followup34/leases/Mistral_alpha150_reference20
launch_job env DEF_ROOT=/home/dell/Def DEF_SITE=node01 DEF_LEASE_DIR=/home/dell/Def/results/audit/unified300/followup34/leases/Mistral_alpha150_reference20 CUDA_VISIBLE_DEVICES=2 DEF_FROZEN_GIT_REV=7505b04b2f712074a92f7ea6c7b154240eddbc42 bash /home/dell/Def/tools/handoff_20261106/u300_logged_job31.sh /home/dell/Def results/audit/unified300/Mistral_calibration32_plan.json 2 /data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/u300_mistral_diag34.py
while ! wait_gpu "$DEVICE"; do sleep 10; done
mkdir -p /home/dell/Def/results/audit/unified300/followup34/leases/qwen_translate-mr_alpha0
launch_job env DEF_ROOT=/home/dell/Def DEF_SITE=node01 DEF_LEASE_DIR=/home/dell/Def/results/audit/unified300/followup34/leases/qwen_translate-mr_alpha0 CUDA_VISIBLE_DEVICES=2 DEF_FROZEN_GIT_REV=7505b04b2f712074a92f7ea6c7b154240eddbc42 bash /home/dell/Def/tools/handoff_20261106/u300_logged_job31.sh /home/dell/Def results/audit/unified300/language_execution33.json 2 /data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/u300_language_translate33.py qwen_translate-mr_alpha0
