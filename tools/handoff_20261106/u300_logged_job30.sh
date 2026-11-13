#!/usr/bin/env bash
set -o pipefail
root=$1
plan=$2
gpu=$3
shift 3
log="${DEF_LEASE_DIR:?}/execution.log"
host=$(hostname)
uuid=$(nvidia-smi -i "$gpu" --query-gpu=uuid --format=csv,noheader)
gitrev=$(git -C "$root/prereg_repo" rev-parse HEAD)
plansha=$(sha256sum "$root/$plan" | cut -d ' ' -f 1)
printf 'START utc=%s host=%s physical_gpu=%s uuid=%s git=%s plan_sha256=%s CUDA_VISIBLE_DEVICES=%s\n' "$(date -u +%FT%TZ)" "$host" "$gpu" "$uuid" "$gitrev" "$plansha" "${CUDA_VISIBLE_DEVICES:-unset}" | tee -a "$log"
export DEF_GENERATION_PLAN_RELATIVE="$plan"
"$@" 2>&1 | tee -a "$log"
task_exit=${PIPESTATUS[0]}
printf 'EXIT=%s utc=%s\n' "$task_exit" "$(date -u +%FT%TZ)" | tee -a "$log"
exit "$task_exit"
