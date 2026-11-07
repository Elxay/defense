"""Verify preserved harmful rows before and after resuming the paused condition."""
import argparse
import datetime
from pathlib import Path

from pair500_generate import digest, load, write

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/audit/pair500"


def verify(shard, phase):
    marker = OUT / "public_first_handoff.json"
    if not marker.exists():
        return
    saved = load(marker)["file_sha256"]
    folder = OUT / "public255/harmful.private/old_s3/wildjailbreak_harmful"
    current = {key: digest(folder / f"{key}.json") for key in saved}
    assert current == saved, "Preserved harmful rows changed across public-first handoff"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    path = OUT / f"resume_old_s3_{shard}_{phase}.json"
    write(path, {"utc": now, "shard": shard, "phase": phase, "preserved_rows": len(saved),
                 "all_hashes_equal": True, "pause_manifest_sha256": digest(marker)})
    with (ROOT / "docs/PREREG_LOG.txt").open("a") as log:
        log.write(f"{now} WJB_OLD_S3_RESUME_{phase.upper()} shard={shard} n={len(saved)} all_hashes_equal=True SHA={digest(path)}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", default="controller")
    parser.add_argument("--phase", choices=("before", "after"), default="before")
    args = parser.parse_args()
    verify(args.shard, args.phase)
