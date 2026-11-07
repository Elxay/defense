"""Run one frozen PAIR-style search lane and snapshot the completed prefix."""
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from pair500_generate import digest, load, write

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/audit/pair500"
REMOTE = "/home/dell/Def"
PAIR = "results/audit/pair500"


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def pulse(phase, **extra):
    write(OUT / "full_queue_live.json", {
        "utc": now().isoformat(), "pid": os.getpid(), "phase": phase, **extra,
    })


def run_node(deadline):
    epoch = int(deadline.timestamp())
    script = f"deadline={epoch}\n" + r'''
set -euo pipefail
cd /home/dell/Def
source tools/handoff_20261106/node01_launch_round9.sh
exec 8>>logs/idle_gpu1.lock
exec 7>>logs/idle_gpu2.lock
while [ "$(date -u +%s)" -lt "$deadline" ]; do
  if flock -n 8 && flock -n 7 && wait_gpu cuda:1 && wait_gpu cuda:2; then
    break
  fi
  flock -u 7
  flock -u 8
  sleep 1
done
seconds=$((deadline - $(date -u +%s)))
if [ "$seconds" -le 0 ]; then exit 124; fi
export DEVICE=cuda:1 CUDA_VISIBLE_DEVICES=1,2
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
target=/data/ray/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
if [ ! -f results/audit/pair500/full_start_utc ]; then
  date -u +%Y-%m-%dT%H:%M:%SZ > results/audit/pair500/full_start_utc
fi
launch_job timeout --foreground --kill-after=20s "$seconds" /data/ray/env/bin/python -u tools/handoff_20261106/pair500_search_telemetry.py --root /home/dell/Def --attacker /data/ray/pair500_models/qwen3_8b --target "$target" --limit 500
'''
    pulse("node_waiting_leases_or_running", stop_utc=deadline.isoformat())
    with (ROOT / "logs/pair500_full_node.log").open("ab") as log:
        proc = subprocess.run(["ssh", "node01", "bash", "-s"], input=script.encode(), stdout=log,
                              stderr=subprocess.STDOUT, check=False)
    if proc.returncode not in (0, 124, 137):
        raise subprocess.CalledProcessError(proc.returncode, "node01 frozen PAIR-style search")
    if proc.returncode == 137 and now() < deadline:
        raise RuntimeError("Search worker terminated before the scheduled cutoff")
    return proc.returncode


def collect(code):
    pulse("syncing_completed_prompt_prefix")
    local = OUT / "generations.private"
    subprocess.run(["rsync", "-a", f"node01:{REMOTE}/{PAIR}/generations.private/", str(local) + "/"], check=True)
    telemetry = OUT / "search_cap.private"
    telemetry.mkdir(exist_ok=True)
    subprocess.run(["rsync", "-a", f"node01:{REMOTE}/{PAIR}/search_cap.private/", str(telemetry) + "/"], check=True)
    order = load(OUT / "row_audit.json")["order"]
    config_sha = digest(OUT / "config.json")
    records = []
    counts = {}
    for identifier in order:
        path = local / f"{identifier}.json"
        if not path.exists():
            break
        data = load(path)
        assert data["id"] == identifier and data["config_sha256"] == config_sha
        records.append({"id": identifier, "file_sha256": digest(path),
                        "prompt_sha256": hashlib.sha256(data["best"]["prompt"].encode()).hexdigest()})
        counts[data["layer"]] = counts.get(data["layer"], 0) + 1
    assert len(records) >= 10 and len(list(local.glob("*.json"))) == len(records)
    path = OUT / "frozen_prompt_snapshot.json"
    assert not path.exists()
    write(path, {
        "utc": now().isoformat(), "config_sha256": config_sha, "rows": records,
        "planned_rows": 500, "layer_n": counts, "exit_status": code,
        "scope": "complete census" if len(records) == 500 else "fixed stratified pilot plus randomized prefix",
    })
    from pair500_search_telemetry import cap_summary
    cap_path = OUT / "search_cap_summary.json"
    write(cap_path, cap_summary(OUT, records))
    with (ROOT / "docs/PREREG_LOG.txt").open("a") as f:
        f.write(f"{now().isoformat()} PAIR500_PROMPTS_FROZEN n={len(records)}/500 layer_n={counts} SHA={digest(path)} before canonical generation.\n")
    pulse("prompts_frozen", rows=len(records), layer_n=counts, snapshot_sha256=digest(path))


def compare_alpha0():
    snapshot = load(OUT / "frozen_prompt_snapshot.json")
    rows = []
    for entry in snapshot["rows"][:50]:
        key = entry["id"]
        search = load(OUT / "generations.private" / f"{key}.json")
        canonical = load(OUT / "canonical254/generation.private/alpha0" / f"{key}.json")
        assert hashlib.sha256(search["best"]["prompt"].encode()).hexdigest() == entry["prompt_sha256"]
        assert canonical["id"] == key and canonical["signature"]["snapshot_sha256"] == digest(OUT / "frozen_prompt_snapshot.json")
        a = search["alpha0"].encode("utf-8")
        b = canonical["result"]["text"].encode("utf-8")
        rows.append({"id": key, "byte_identical": a == b, "node01_bytes": len(a), "innet_bytes": len(b),
                     "node01_sha256": hashlib.sha256(a).hexdigest(), "innet_sha256": hashlib.sha256(b).hexdigest()})
    write(OUT / "alpha0_first50_cross_node.json", {"utc": now().isoformat(), "n": len(rows),
          "identical": sum(row["byte_identical"] for row in rows), "rows": rows,
          "paths": ["node01 HF native greedy", "innet HF canonical zero injection hook"]})


def main():
    assert load(OUT / "pilot_timing.json")["pilot_n"] == 10
    cfg = load(OUT / "eval254_config.json")
    assert load(OUT / "eval254_publication.json")["config_sha256"] == digest(OUT / "eval254_config.json")
    deadline = datetime.datetime.fromisoformat(cfg["search_stop_utc"])
    with (OUT / "full_queue.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            if not (OUT / "frozen_prompt_snapshot.json").exists():
                code = run_node(deadline)
                collect(code)
            pulse("canonical_innet_evaluation_queued", rows=len(load(OUT / "frozen_prompt_snapshot.json")["rows"]))
            with (ROOT / "logs/pair500_canonical_eval.log").open("ab") as log:
                subprocess.run(["bash", "tools/handoff_20261106/pair500_eval254_queue.sh"],
                               cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
            compare_alpha0()
            pulse("complete", rows=len(load(OUT / "frozen_prompt_snapshot.json")["rows"]))
        except Exception as exc:
            pulse("failed", error=str(exc))
            raise


if __name__ == "__main__":
    main()
