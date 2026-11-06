#!/bin/bash
# common launcher: source first. Provides launch_job, registry with flock, wait_gpu.
export PATH=/data/ray/env/bin:$PATH
export DSH_OWNER=/home/dell/Def
REG=/home/dell/Def/logs/pid_registry.txt
wait_gpu() {
  local dev="$1" idx="${1#cuda:}"
  local used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$idx" 2>/dev/null)
  if [ -n "$used" ] && [ "$used" -gt 2000 ]; then echo "WAIT_GPU_REFUSE $dev used=${used}MiB"; return 1; fi
  return 0
}
launch_job() {
  if [ "${NOGPU:-0}" != "1" ]; then wait_gpu "${DEVICE:-cuda:0}" || return 1; fi
  "$@" &
  local pid=$!
  local ls=$(ps -o lstart= -p $pid | tr -s ' ')
  ( flock 9; echo "$pid|$ls|$*" >> $REG ) 9>>$REG
  echo "LAUNCHED pid=$pid lstart=$ls"
  wait $pid
}
