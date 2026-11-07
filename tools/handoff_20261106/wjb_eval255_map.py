"""Infer WildJailbreak reference behavior IDs without opening generation or judge files."""
import collections
import csv
import json
import os
import random
from pathlib import Path

import numpy as np
from pair500_generate import digest, load, write

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/audit/pair500"
MODEL = Path("/data/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41")


def csv_rows(path, delimiter=","):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def audit_xstest(path):
    official = [(x["prompt"], x["label"]) for x in csv_rows(path)]
    local_path = ROOT / "data/public/records.jsonl"
    local = []
    with local_path.open() as f:
        for line in f:
            x = json.loads(line)
            if x["group"].startswith("xstest_"):
                local.append((x["text"], x["group"].split("_", 1)[1]))
    assert len(official) == len(local) == 450
    return {
        "official_source": "https://raw.githubusercontent.com/paul-rottger/xstest/main/xstest_prompts.csv",
        "official_sha256": digest(path), "local_inventory_sha256": digest(local_path),
        "same_order_prompt_and_label": official == local,
        "counts": {label: sum(a[1] == label and a == b for a, b in zip(official, local))
                   for label in ("safe", "unsafe")},
    }


def main():
    from sentence_transformers import SentenceTransformer

    os.umask(0o077)
    protocol = ROOT / "docs/255_WJB_PUBLIC_EVAL_PROTOCOL.md"
    plan = load(OUT / "public_wjb_gate_plan.json")
    source = Path(plan["source"])
    assert digest(source) == plan["source_sha256"]
    prompts = {str(i): r["adversarial"] for i, r in enumerate(csv_rows(source, "\t"))
               if r["data_type"] == "adversarial_harmful"}
    hb_path = ROOT / "repos/HarmBench/data/behavior_datasets/harmbench_behaviors_text_all.csv"
    behaviors = {r["BehaviorID"]: r["Behavior"] for r in csv_rows(hb_path)
                 if r["FunctionalCategory"] == "standard"}
    flags = {r["id"]: r for r in load(OUT / "row_audit.json")["flags"] if r["layer"] == "standard"}
    assert len(prompts) == 2000 and len(behaviors) == len(flags) == 200
    behavior_ids = sorted(behaviors)
    def flag_for(key):
        return flags[key] if key in flags else flags["hb_" + key]

    model = SentenceTransformer(str(MODEL), device="cpu", local_files_only=True)
    tokenizer = model.tokenizer
    cap = model.max_seq_length - tokenizer.num_special_tokens_to_add()
    assert cap > 128
    refs = model.encode(list(behaviors[k] for k in behavior_ids), normalize_embeddings=True)
    items = list(prompts.items())
    result = []
    for offset in range(0, len(items), 100):
        chunk = items[offset:offset + 100]
        window_texts = []
        boundaries = []
        for _, prompt in chunk:
            tokens = tokenizer.encode(prompt, add_special_tokens=False, verbose=False)
            for start in range(0, max(1, len(tokens)), 128):
                window_texts.append(tokenizer.decode(tokens[start:start + cap]))
                if start + cap >= len(tokens):
                    break
            boundaries.append(len(window_texts))
        embeddings = model.encode(window_texts, batch_size=48, normalize_embeddings=True)
        cosines = embeddings @ refs.T
        begin = 0
        for (key, _), end in zip(chunk, boundaries):
            scores = cosines[begin:end].max(axis=0)
            begin = end
            ranked = np.argsort(-scores, kind="stable")[:5]
            candidates = [{"behavior_id": behavior_ids[j], "cosine": float(scores[j])} for j in ranked]
            top, second = candidates[:2]
            margin = top["cosine"] - second["cosine"]
            audit = flag_for(top["behavior_id"])
            result.append({
                "id": key, "candidates": candidates, "margin": margin,
                "low_similarity": top["cosine"] < .45, "low_margin": margin < .05,
                "group": audit["group"], "direct_flags": audit["direct_flags"],
                "group_flags": audit["group_flags"], "historical_group_used": not audit["untouched"],
                "legacy_group_manifest_used": audit["historical_group_used"],
            })
        print(f"mapped {len(result)}/{len(items)}", flush=True)

    sample = random.Random(20261107).sample(list(prompts), 30)
    by_id = {row["id"]: row for row in result}
    review = []
    for key in sample:
        row = by_id[key]
        best = row["candidates"][0]["behavior_id"]
        review.append({"id": key, "full_prompt": prompts[key], "candidate_behavior": behaviors[best],
                       "human_verdict": None, "human_note": None})
    write(OUT / "wjb_mapping_review30.private.json", review)
    mapping_path = OUT / "wjb_mapping255.json"
    write(mapping_path, {"rows": result, "protocol_sha256": digest(protocol),
                         "source_sha256": digest(source), "hb_sha256": digest(hb_path),
                         "model_revision": MODEL.name, "token_window": cap, "stride": 128,
                         "review_sample_ids": sample})
    counts = collections.Counter(flag for row in result for flag in row["group_flags"])
    summary = {
        "rows": len(result), "behavior_ids": len({row["candidates"][0]["behavior_id"] for row in result}),
        "behavior_groups": len({row["group"] for row in result}), "low_similarity": sum(x["low_similarity"] for x in result),
        "low_margin": sum(x["low_margin"] for x in result),
        "uncertain_union": sum(x["low_margin"] or x["low_similarity"] for x in result),
        "historical_group_used": sum(x["historical_group_used"] for x in result), "group_flag_counts": dict(counts),
        "human_review_n": 0, "human_review_requested_n": len(sample),
        "review_sample_ids": sample, "mapping_sha256": digest(mapping_path),
        "xstest": audit_xstest(OUT / "xstest_official.csv"),
    }
    write(OUT / "wjb_mapping255_summary.json", summary)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
