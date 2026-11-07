"""Compare fixed GPU2 public batches with same-GPU single-row injection replays."""
import datetime
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from pair500_generate import digest, load, write
from wjb_eval255_run import CFG, EVAL, LLAMA, OUT, ROOT, public_rows, vector_for

assert os.environ.get("DEVICE") == "cuda:2" and os.environ.get("CUDA_VISIBLE_DEVICES") == "2"
import sys
sys.path.insert(0, str(ROOT / "src"))
from gen.common import generate_with_injection

plan_path = OUT / "public_single80_plan.json"
plan = load(plan_path)
assert digest(plan_path) == "93fea548b17d1e4ca19b4d97934b3cff9bbad913fb37b93812668cba01b48cc8"
assert digest(CFG) == plan["config_sha256"]
config = load(CFG)
prompts = {dataset: dict(rows) for dataset, rows in public_rows().items()}
tok = AutoTokenizer.from_pretrained(LLAMA, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    LLAMA, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"}, local_files_only=True,
).eval()
rows = []
for condition in plan["same_twenty_for_conditions"]:
    spec = config["conditions"][condition]
    vector = vector_for(spec)
    for sample in plan["rows"]:
        key, dataset = sample["id"], sample["dataset"]
        original = EVAL / "public.private" / condition / dataset / f"{sample['batch_first_id']}.json"
        assert digest(original) == sample["original_batch_sha256"][condition]
        batch = load(original)
        assert batch["signature"]["config_sha256"] == digest(CFG)
        old = next(r["text"] for r in batch["items"] if r["id"] == key)
        signature = {"plan_sha256": digest(plan_path), "original_batch_sha256": digest(original),
                     "vector_sha256": spec["file_sha256"], "common_sha256": digest(ROOT / "src/gen/common.py")}
        target = EVAL / "public_single80.private" / condition / f"{dataset}_{key}.json"
        if target.exists():
            saved = load(target)
            assert saved["signature"] == signature
            result = saved["generation"]
        else:
            ids = tok.apply_chat_template([{"role": "user", "content": prompts[dataset][key]}],
                                         add_generation_prompt=True, return_tensors="pt").to("cuda:0")
            result = generate_with_injection(
                model, tok, ids, vector, layer=9, max_new_tokens=120,
                src_vec_sha256=spec["file_sha256"], alpha=spec["alpha"])
            result.update(host=__import__("socket").gethostname(), physical_device="cuda:2",
                          rho_runtime=float(np.linalg.norm(vector)))
            write(target, {"signature": signature, "generation": result})
        assert result["injection_count"] == 1 and abs(result["rho_runtime"]-5.21) < 1e-4
        rows.append({"condition": condition, "dataset": dataset, "id": key,
                     "byte_identical": old.encode() == result["text"].encode(),
                     "original_sha256": hashlib.sha256(old.encode()).hexdigest(),
                     "replay_sha256": hashlib.sha256(result["text"].encode()).hexdigest(),
                     "injection_count": result["injection_count"], "rho_runtime": result["rho_runtime"],
                     "new_tokens": result["new_tokens"], "eos": result["eos"]})
        write(EVAL / "public_single80_live.json", {
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "pid": os.getpid(),
            "device": "cuda:2", "n": len(rows), "total": 80})
summary = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "plan_sha256": digest(plan_path),
           "conditions": {name: {"n": 20, "byte_identical": sum(r["byte_identical"] for r in rows if r["condition"] == name)}
                          for name in plan["same_twenty_for_conditions"]},
           "scope": "Same GPU2 and vector; fixed prompts, single versus original batch8. Matching is sample evidence only.",
           "rows": rows}
path = EVAL / "public_single80_results.json"
write(path, summary)
with (ROOT / "docs/PREREG_LOG.txt").open("a") as log:
    log.write(f"{summary['utc']} PUBLIC_SINGLE80_COMPLETE SHA={digest(path)} counts={summary['conditions']} original batch rows retained.\n")
print(json.dumps(summary["conditions"]), flush=True)
