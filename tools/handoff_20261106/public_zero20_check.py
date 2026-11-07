"""Isolate zero-vector batch/single path differences on the fixed GPU2 prompt sample."""
import datetime
import os
import sys

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from pair500_generate import digest, load, write, official_functions
from wjb_eval255_run import EVAL, LLAMA, OUT, ROOT, public_rows, observed_public_batch

assert os.environ.get("DEVICE") == "cuda:2" and os.environ.get("CUDA_VISIBLE_DEVICES") == "2"
sys.path.insert(0, str(ROOT / "src"))
from gen.common import generate_with_injection
from judge.refusal import new_rule

plan = load(OUT / "public_single80_plan.json")
assert digest(OUT / "public_single80_plan.json") == "93fea548b17d1e4ca19b4d97934b3cff9bbad913fb37b93812668cba01b48cc8"
sources = public_rows()
tok = AutoTokenizer.from_pretrained(LLAMA, local_files_only=True)
tok.padding_side = "left"
tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(
    LLAMA, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"}, local_files_only=True,
).eval()
zero = np.zeros(4096, dtype=np.float32)
scope = official_functions(ROOT / "src/eval/legal_val_batch.py", {"run_batch"})
scope.update(tok=tok, mdl=model, DEV="cuda:0", LAYER=9, vec=zero, torch=torch)
batches = {}
rows = []
for sample in plan["rows"]:
    dataset, key, first = sample["dataset"], sample["id"], sample["batch_first_id"]
    batch_key = dataset, first
    if batch_key not in batches:
        dataset_rows = sources[dataset]
        offset = next(i for i, (k, _) in enumerate(dataset_rows) if k == first)
        batch = dataset_rows[offset:offset + 8]
        texts, norms = observed_public_batch(scope, [(i, dataset, p) for i, (_, p) in enumerate(batch)])
        assert all(x == 0 for x in norms)
        rendered = [tok.apply_chat_template([{"role": "user", "content": p}],
                                           add_generation_prompt=True, tokenize=False) for _, p in batch]
        enc = tok(rendered, padding=True, add_special_tokens=False, return_tensors="pt")
        length = enc.input_ids.shape[1]
        indices = (enc.attention_mask * torch.arange(length)).max(dim=1).values.tolist()
        assert all(i == length - 1 for i in indices)
        batches[batch_key] = dict(zip([k for k, _ in batch], texts, strict=True))
        write(EVAL / "zero_batch20.private" / f"{dataset}_{first}.json",
              {"items": dict(zip([k for k, _ in batch], texts, strict=True)),
               "injection_count": 1, "rho_runtime": 0.0, "last_nonpadding_indices": indices,
               "padded_length": length, "batch_hook_sha256": digest(ROOT / "src/eval/legal_val_batch.py")})
    prompt = dict(sources[dataset])[key]
    ids = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                 add_generation_prompt=True, return_tensors="pt").to("cuda:0")
    result = generate_with_injection(model, tok, ids, zero, layer=9, max_new_tokens=120, alpha=0.0)
    assert result["injection_count"] == 1
    write(EVAL / "zero_single20.private" / f"{dataset}_{key}.json", result)
    original_path = EVAL / "public.private/alpha0" / dataset / f"{first}.json"
    original = next(r["text"] for r in load(original_path)["items"] if r["id"] == key)
    batch_text = batches[batch_key][key]
    rows.append({"dataset": dataset, "id": key,
                 "batch_zero_vs_single_zero": batch_text.encode() == result["text"].encode(),
                 "batch_zero_vs_original_batch_none": batch_text.encode() == original.encode(),
                 "v2_batch_zero": new_rule(batch_text), "v2_single_zero": new_rule(result["text"]),
                 "single_injection_count": result["injection_count"], "single_delta_norm": result["delta_norm_runtime"]})
summary = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "n": len(rows),
           "byte_identical_batch_single": sum(r["batch_zero_vs_single_zero"] for r in rows),
           "byte_identical_batch_zero_original_none": sum(r["batch_zero_vs_original_batch_none"] for r in rows),
           "v2_label_discordant_batch_single": sum(r["v2_batch_zero"] != r["v2_single_zero"] for r in rows),
           "all_batch_last_nonpadding_indices_verified": True, "rows": rows}
path = EVAL / "public_zero20_results.json"
write(path, summary)
with (ROOT / "docs/PREREG_LOG.txt").open("a") as log:
    log.write(f"{summary['utc']} PUBLIC_ZERO20_COMPLETE SHA={digest(path)} n={len(rows)} batch_single={summary['byte_identical_batch_single']} zero_none={summary['byte_identical_batch_zero_original_none']}\n")
print({k: v for k, v in summary.items() if k != "rows"}, flush=True)
