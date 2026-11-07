"""Queue the first full PAIR500 lane after the already scheduled evaluation jobs."""
import datetime
import fcntl
import json
import os
import subprocess
import time
from pathlib import Path

from pair500_generate import load, write

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/audit/pair500"
REMOTE = "/home/dell/Def"
PAIR = "results/audit/pair500"
PYTHON = "/home/kemove/anaconda3/envs/HZX_GLA/bin/python"


def pulse(phase, **extra):
    write(OUT / "full_queue_live.json", {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pid": os.getpid(), "phase": phase, **extra,
    })


def prior_node_status():
    paths = [
        "noise_B_launcher_live.json",
        "same_alpha_s3_launcher_live.json",
        "same_alpha_s5_launcher_live.json",
    ]
    code = (
        "from pathlib import Path; import json,sys; b=Path('/home/dell/Def/results/audit');"
        "print(json.dumps({p:json.loads((b/p).read_text())['phase']"
        " for p in sys.argv[1:] if (b/p).exists()}))"
    )
    remote_paths = [f"handoff_round{'11' if n.startswith('noise') else '12'}/{n}" for n in paths]
    result = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", "node01", "python3", "-", "--", *remote_paths],
        input=code, text=True, capture_output=True, check=True, timeout=20,
    )
    return json.loads(result.stdout), len(paths)


def wait_previous():
    plain_path = ROOT / "results/audit/handoff_round11/plain_pipeline_live.json"
    terminal = {"complete", "failed", "plain_incomparable"}
    while True:
        node, required = prior_node_status()
        plain = load(plain_path)["phase"]
        if plain in terminal and len(node) == required and all(v in terminal for v in node.values()):
            return
        pulse("waiting_existing_evaluations", plain_phase=plain, node_phases=node)
        time.sleep(60)


def run_node():
    script = r'''
set -euo pipefail
cd /home/dell/Def
source tools/handoff_20261106/node01_launch_round9.sh
exec 8>>logs/idle_gpu1.lock
exec 7>>logs/idle_gpu2.lock
while true; do
  if flock -n 8; then
    if flock -n 7; then
      if wait_gpu cuda:1 && wait_gpu cuda:2; then break; fi
      flock -u 7
    fi
    flock -u 8
  fi
  sleep 30
done
export DEVICE=cuda:1 CUDA_VISIBLE_DEVICES=1,2
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 TOKENIZERS_PARALLELISM=false
target=/data/ray/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
launch_job /data/ray/env/bin/python -u tools/handoff_20261106/pair500_generate.py --root /home/dell/Def --attacker /data/ray/pair500_models/qwen3_8b --target "$target" --limit 500
until wait_gpu cuda:1 && wait_gpu cuda:2; do sleep 10; done
launch_job /data/ray/env/bin/python -u tools/handoff_20261106/pair500_score.py --root /home/dell/Def --judge /data/ray/judge13b --mode classifier --limit 500
'''
    pulse("node_waiting_leases_or_running")
    with (ROOT / "logs/pair500_full_node.log").open("ab") as log:
        subprocess.run(["ssh", "node01", "bash", "-s"], input=script.encode(), stdout=log,
                       stderr=subprocess.STDOUT, check=True)


def collect():
    pulse("syncing_completed_alpha0")
    for name in ("generations.private", "scores"):
        subprocess.run(["rsync", "-a", f"node01:{REMOTE}/{PAIR}/{name}/", str(OUT / name) + "/"], check=True)
    subprocess.run(
        [PYTHON, str(Path(__file__).with_name("pair500_score.py")), "--root", str(ROOT),
         "--judge", str(ROOT / "local_judge13b"), "--mode", "hash", "--limit", "500"],
        env={**os.environ, "DEVICE": "cpu", "HF_HUB_OFFLINE": "1"}, check=True,
    )
    ids = load(OUT / "row_audit.json")["order"]
    labels = {identifier: load(OUT / "scores" / f"{identifier}.json")["label"] for identifier in ids}
    write(OUT / "alpha0_row_labels.json", {"alpha0": labels})
    subprocess.run([PYTHON, str(Path(__file__).with_name("pair500_report.py")), "pair500",
                    "--conditions", str(OUT / "alpha0_row_labels.json")], check=True)
    pulse("alpha0_complete", rows=len(labels), unavailable=sum(v is None for v in labels.values()))


def main():
    assert load(OUT / "pilot_timing.json")["pilot_n"] == 10
    with (OUT / "full_queue.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            wait_previous()
            run_node()
            collect()
        except Exception as exc:
            pulse("failed", error=str(exc))
            raise


if __name__ == "__main__":
    main()
