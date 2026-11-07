"""Write operational stage transitions and content hashes without response text."""
import argparse
import datetime
import os

from pair500_generate import digest, write, load
from wjb_eval255_run import EVAL, ROOT

parser = argparse.ArgumentParser()
parser.add_argument("stage")
parser.add_argument("--detail", default="")
parser.add_argument("--complete", action="store_true")
args = parser.parse_args()
stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
state = {"utc": stamp, "pid": os.getpid(), "supervisor_pid": os.getppid(),
         "stage": args.stage, "detail": args.detail, "complete": args.complete}
if args.complete:
    paths = {
        "baseline_summary": ["native_alpha0_generation_summary.json"],
        "zero20": ["zero20_check.json", "zero20.private"],
        "baseline_frozen": ["alpha0_active_baseline.json", "alpha0_active_files.json", "zero20_check.json"],
        "reference_judge": ["judge20_gate.json", "reference_sensitivity_summary.json"],
        "public_generation": [f"public.private/{args.detail}"],
        "public_refusal_alpha0": ["public.private/alpha0"],
        "harmful_generation": [f"harmful.private/{args.detail}"],
        "harmful_judge": [f"mapped_scores/{args.detail}"],
    }[args.stage]
    files = []
    for name in paths:
        path = EVAL / name
        files.extend([path] if path.is_file() else sorted(path.rglob("*.json")))
    manifest = EVAL / "stage_manifests" / f"{args.stage}_{args.detail or 'all'}.json"
    hashes = {str(p.relative_to(EVAL)): digest(p) for p in files}
    if not manifest.exists() or load(manifest)["files"] != hashes:
        write(manifest, {"utc": stamp, "files": hashes})
    state["manifest_sha256"] = digest(manifest)
    with (ROOT / "docs/PREREG_LOG.txt").open("a") as log:
        log.write(f"{stamp} WJB_STAGE_FROZEN stage={args.stage} detail={args.detail} SHA={state['manifest_sha256']}\n")
write(EVAL / "stage_live.json", state)
