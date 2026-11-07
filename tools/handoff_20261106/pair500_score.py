"""Score fixed PAIR completions with HarmBench's text and copyright protocols."""
import argparse
import ast
import hashlib
import os
import time
from pathlib import Path

from pair500_generate import digest, gpu_roles, load, write


def harmbench_scope(source, mode):
    tree = ast.parse(source.read_text())
    nodes = [
        node for node in tree.body
        if isinstance(node, ast.Assign) and any(
            isinstance(key, ast.Name) and key.id == "LLAMA2_CLS_PROMPT" for key in node.targets
        )
    ]
    scope = {}
    if mode == "hash":
        import spacy
        from datasketch import MinHash

        names = {"tokenize", "compute_hashes_with_sliding_window",
                 "check_output_with_sliding_window", "compute_results_hashing"}
        nodes.extend(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names)
        nlp = spacy.load("en_core_web_sm")
        nlp.max_length = 10000000
        scope.update(nlp=nlp, MinHash=MinHash, tqdm=lambda items: items)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), scope)
    return scope


def clip(tokenizer, generation, cap):
    tokens = tokenizer.encode(generation, max_length=cap, truncation=True)
    return tokenizer.decode(tokens, skip_special_tokens=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--judge", required=True, type=Path)
    p.add_argument("--mode", required=True, choices=("classifier", "hash"))
    p.add_argument("--limit", required=True, type=int)
    a = p.parse_args()
    if a.mode == "classifier":
        physical = gpu_roles("HarmBench classifier")
    else:
        if os.environ.get("DEVICE") != "cpu":
            raise SystemExit("Set DEVICE=cpu for copyright hash scoring")
        physical = []
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch

    directory = a.root / "results/audit/pair500"
    config_path = directory / "config.json"
    config = load(config_path)
    config_sha = digest(config_path)
    assert digest(Path(__file__)) == config["scorer_sha256"]
    assert digest(a.judge / "model.safetensors.index.json") == config["judge_index_sha256"]
    assert digest(a.root / "docs/253_PAIR500_ROW_PROTOCOL.md") == load(directory / "publication.json")["doc_sha256"]
    rows_path = directory / "rows.private.json"
    assert digest(rows_path) == config["rows_sha256"]
    rows = load(rows_path)[:a.limit]
    source = a.root / "repos/HarmBench/eval_utils.py"
    assert digest(source) == config["source_sha256"]["repos/HarmBench/eval_utils.py"]
    scope = harmbench_scope(source, a.mode)
    tokenizer = AutoTokenizer.from_pretrained(a.judge, local_files_only=True)
    candidates = [row for row in rows if (row["layer"] == "copyright") == (a.mode == "hash")]
    assert candidates
    items = []
    for row in candidates:
        path = directory / "generations.private" / f"{row['id']}.json"
        record = load(path)
        assert record["id"] == row["id"] and record["config_sha256"] == config_sha
        items.append((row, path, record))
    if a.mode == "classifier":
        start = time.monotonic()
        model = AutoModelForCausalLM.from_pretrained(
            a.judge, torch_dtype=torch.bfloat16, device_map="auto",
            max_memory={0: "14GiB", 1: "14GiB", "cpu": "0GiB"}, local_files_only=True,
        ).eval()
        assert not {"cpu", "disk"} & set(model.hf_device_map.values())
        write(directory / "classifier_load.json", {"seconds": time.monotonic() - start, "gpus": physical})
    else:
        hashes = load(directory / "copyright_hash_manifest.json")

    for row, path, record in items:
        out = directory / "scores" / f"{row['id']}.json"
        if out.exists():
            saved = load(out)
            assert saved["config_sha256"] == config_sha and saved["generation_sha256"] == digest(path)
            continue
        start = time.monotonic()
        generation = clip(tokenizer, record["alpha0"], config["judge_completion_cap"])
        if a.mode == "hash":
            behavior = row["hb_row"]
            directory_hb = a.root / "repos/HarmBench"
            reference = directory_hb / "data/copyright_classifier_hashes" / f"{behavior['BehaviorID']}.pkl"
            assert digest(reference) == hashes[behavior["BehaviorID"]]
            os.chdir(directory_hb)
            label = scope["compute_results_hashing"](behavior, [{"generation": generation}])[0]["label"]
            method = "HarmBench_MinHash"
        else:
            kind = "prompt_contextual" if row["context"] else "prompt"
            template = scope["LLAMA2_CLS_PROMPT"][kind]
            prompt = template.format(behavior=row["behavior"], generation=generation, context=row["context"])
            encoded = tokenizer(prompt, return_tensors="pt").to(model.device)
            if encoded.input_ids.shape[1] > model.config.max_position_embeddings:
                raise RuntimeError(f"{row['id']} contextual classifier prompt exceeds the frozen context budget")
            with torch.inference_mode():
                output = model.generate(**encoded, max_new_tokens=1, do_sample=False,
                                        pad_token_id=tokenizer.eos_token_id)
            token = tokenizer.decode(output[0, -1:], skip_special_tokens=True).strip().lower()
            label = {"yes": 1, "no": 0}.get(token)
            method = "HarmBench_13B_contextual" if row["context"] else "HarmBench_13B_standard"
        write(out, {
            "id": row["id"], "layer": row["layer"], "method": method, "label": label,
            "config_sha256": config_sha, "generation_sha256": digest(path),
            "seconds": time.monotonic() - start,
        })
        print(f"SCORE_COMPLETE {row['id']} {method}", flush=True)


if __name__ == "__main__":
    main()
