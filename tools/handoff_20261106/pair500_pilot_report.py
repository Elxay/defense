"""Collect the completed pilot, score copyright on CPU, and report measured throughput."""
import argparse
import datetime
import json
import os
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from pair500_generate import digest, load, write

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/audit/pair500"
NODE = "/home/dell/Def/results/audit/pair500"
PYTHON = "/home/kemove/anaconda3/envs/HZX_GLA/bin/python"


def remote_state():
    code = (
        "from pathlib import Path; import json; "
        f"p=Path({NODE!r}); "
        "print(json.dumps({"
        "'complete':(p/'pilot_node_complete').exists(),"
        "'failed':(p/'pilot_failed').exists(),"
        "'generation':json.loads((p/'generation_live.json').read_text())"
        " if (p/'generation_live.json').exists() else None}))"
    )
    result = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", "node01", "python3", "-"],
        input=code, capture_output=True, text=True, check=True, timeout=20,
    )
    return json.loads(result.stdout)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--wait", action="store_true")
    args = p.parse_args()
    while True:
        state = remote_state()
        assert not state["failed"], "node pilot failed, inspect its log"
        if state["complete"]:
            break
        if not args.wait:
            print(json.dumps(state))
            return
        time.sleep(30)

    for name in ("generations.private", "scores"):
        (OUT / name).mkdir(exist_ok=True)
        subprocess.run(["rsync", "-a", f"node01:{NODE}/{name}/", str(OUT / name) + "/"], check=True)
    for name in ("generation_load.json", "classifier_load.json", "pilot_leases_held", "pilot_node_complete"):
        subprocess.run(["rsync", "-a", f"node01:{NODE}/{name}", str(OUT / name)], check=True)
    start = time.monotonic()
    subprocess.run(
        [PYTHON, str(Path(__file__).with_name("pair500_score.py")), "--root", str(ROOT),
         "--judge", str(ROOT / "local_judge13b"), "--mode", "hash", "--limit", "10"],
        env={**os.environ, "DEVICE": "cpu", "HF_HUB_OFFLINE": "1", "USE_TF": "0", "USE_FLAX": "0"},
        check=True,
    )
    hash_wall = time.monotonic() - start
    audit = load(OUT / "row_audit.json")
    config_sha = digest(OUT / "config.json")
    timed = []
    for identifier in audit["pilot"]:
        generation = OUT / "generations.private" / f"{identifier}.json"
        record = load(generation)
        score = load(OUT / "scores" / f"{identifier}.json")
        assert score["generation_sha256"] == digest(generation)
        assert score["config_sha256"] == record["config_sha256"] == config_sha
        timed.append({
            "id": identifier, "layer": record["layer"], "search_seconds": record["search_seconds"],
            "alpha0_seconds": record["alpha0_seconds"], "generation_seconds": record["seconds"],
            "score_seconds": score["seconds"], "score_method": score["method"],
            "alpha0_label": score["label"], "valid_candidates": record["valid_candidates"],
            "fallback": record["fallback"], "target_search_calls": record["target_search_calls"],
        })
    groups = defaultdict(list)
    for row in timed:
        groups[row["layer"]].append(row)
    layer_seconds = {}
    for layer, rows in groups.items():
        layer_seconds[layer] = {
            "pilot_n": len(rows), "total_n": audit["counts"]["layers"][layer]["rows"],
            **{key: statistics.mean(row[key] for row in rows) for key in
               ("search_seconds", "generation_seconds", "score_seconds")},
        }
    all_search = sum(v["total_n"] * v["search_seconds"] for v in layer_seconds.values())
    all_generation = sum(v["total_n"] * v["generation_seconds"] for v in layer_seconds.values())
    all_scoring = sum(v["total_n"] * v["score_seconds"] for v in layer_seconds.values())
    model_load = sum(load(OUT / p)["seconds"] for p in ("generation_load.json", "classifier_load.json"))
    wall_times = [datetime.datetime.fromisoformat((OUT / n).read_text().strip().replace("Z", "+00:00"))
                  for n in ("pilot_leases_held", "pilot_node_complete")]
    report = {
        "config_sha256": config_sha, "pilot_n": len(timed), "timings": timed, "per_layer": layer_seconds,
        "node_wall_seconds": (wall_times[1] - wall_times[0]).total_seconds(),
        "cpu_hash_wall_seconds_including_startup": hash_wall,
        "estimated_500_search_hours": all_search / 3600,
        "estimated_500_search_plus_alpha0_hours": all_generation / 3600,
        "estimated_500_search_alpha0_scoring_hours": (all_generation + all_scoring + model_load) / 3600,
        "eta_scope": "Pilot stratum means weighted by fixed source rows, excludes queue, later intervention conditions, transfers and repeated model starts.",
    }
    write(OUT / "pilot_timing.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
