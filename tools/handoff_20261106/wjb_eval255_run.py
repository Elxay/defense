"""Run public refusal generation or the mapped-reference WildJailbreak evaluator."""
import argparse
import collections
import datetime
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from pair500_eval254 import CFG, OUT, ROOT, clip, harmbench_scope, require_cards, signed
from pair500_generate import digest, load, official_functions, write
from public_wjb_alpha0_gate import LLAMA, PLAN, rows as harmful_rows
from wjb_eval255_map import csv_rows

EVAL = OUT / "public255"
PROTOCOL = ROOT / "docs/255_WJB_PUBLIC_EVAL_PROTOCOL.md"
SNAPSHOT = OUT / "frozen_prompt_snapshot.json"


def pulse(stage, done, total, start, condition, shard=0):
    write(EVAL / f"live_{stage}_{condition}_{shard}.json", {
        "pid": os.getpid(), "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "device": os.environ["DEVICE"], "n": done, "total": total,
        "seconds_per_row": (time.monotonic() - start) / max(1, done),
    })


def public_rows():
    out = collections.defaultdict(list)
    with (ROOT / "data/public/records.jsonl").open() as f:
        for line in f:
            row = json.loads(line)
            if row["group"] in {"xstest_safe", "xstest_unsafe", "or_hard"}:
                out[row["group"]].append((row["id"], row["text"]))
    for i, row in enumerate(csv_rows(Path(load(PLAN)["source"]), "\t")):
        if row["data_type"] == "adversarial_benign":
            out["wildjailbreak_benign"].append((str(i), row["adversarial"]))
    assert sorted(map(len, out.values())) == [200, 210, 250, 1319], [(k, len(v)) for k, v in out.items()]
    return out


def vector_for(spec):
    if "vector" not in spec:
        return None
    path = ROOT / spec["vector"]
    assert digest(path) == spec["file_sha256"]
    vector = np.load(path).astype(np.float32)
    if spec["renormalize"]:
        vector = vector / np.linalg.norm(vector) * 5.21
    import hashlib
    assert hashlib.sha256((vector + 0.0).tobytes()).hexdigest() == spec["injection_sha256"]
    return vector


def generate(kind, name, shard, config):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from gen.common import generate_with_injection
    from judge.refusal import new_rule

    require_cards()
    spec = config["conditions"][name]
    vec = vector_for(spec)
    system = spec.get("system_prompt")
    protocol_sha = digest(PROTOCOL)
    config_sha = digest(CFG)
    if kind == "public":
        datasets = list(public_rows().items())
    else:
        plan = load(PLAN)
        data = harmful_rows(plan)
        datasets = [("wildjailbreak_harmful", [(k, data[k]) for k in plan["ids"][shard::2]])]
    start = time.monotonic()
    n_new = 0
    total = sum(len(rows) for _, rows in datasets) if kind == "harmful" else sum(
        len(rows[offset:offset + 8]) for _, rows in datasets for offset in range(shard * 8, len(rows), 16)
    )
    tok = AutoTokenizer.from_pretrained(LLAMA, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        LLAMA, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"}, local_files_only=True,
    ).eval()
    if kind == "public":
        tok.padding_side = "left"
        tok.pad_token = tok.eos_token
        scope = official_functions(ROOT / "src/eval/legal_val_batch.py", {"run_batch"})
        # Use the original batch and injection function for all settings. Only render
        # the frozen system message for the two system-prompt conditions.
        def render(messages, **kwargs):
            prefix = [{"role": "system", "content": system}] if system else []
            return tok.apply_chat_template(prefix + messages, **kwargs)

        class ChatTokenizer:
            apply_chat_template = staticmethod(render)

            def __getattr__(self, key):
                return getattr(tok, key)

            def __call__(self, *args, **kwargs):
                return tok(*args, **kwargs)

        scope.update(tok=ChatTokenizer(), mdl=model, DEV="cuda:0", LAYER=9, vec=vec, torch=torch)
    for dataset, data in datasets:
        offsets = range(shard * 8, len(data), 16) if kind == "public" else range(len(data))
        for offset in offsets:
            if SNAPSHOT.exists():
                return
            batch = data[offset:offset + (8 if kind == "public" else 1)]
            out = EVAL / f"{kind}.private" / name / dataset / f"{batch[0][0]}.json"
            signature = {"protocol_sha256": protocol_sha, "config_sha256": config_sha,
                         "dataset": dataset, "condition": name, "ids": [k for k, _ in batch]}
            if out.exists():
                signed(out, signature)
                continue
            if kind == "public":
                texts = scope["run_batch"]([(i, dataset, p) for i, (_, p) in enumerate(batch)])
            else:
                messages = ([{"role": "system", "content": system}] if system else []) + [
                    {"role": "user", "content": batch[0][1]}]
                ids = tok.apply_chat_template(messages, add_generation_prompt=True,
                                              return_tensors="pt").to("cuda:0")
                if vec is None:
                    with torch.inference_mode():
                        result = model.generate(ids, max_new_tokens=2400, do_sample=False,
                                                pad_token_id=tok.eos_token_id)
                    texts = [tok.decode(result[0, ids.shape[1]:], skip_special_tokens=True)]
                else:
                    texts = [generate_with_injection(model, tok, ids, vec, layer=9,
                                                     max_new_tokens=2400)["text"]]
            write(out, {"signature": signature, "items": [
                {"id": key, "text": text, "v2_refusal": new_rule(text)}
                for (key, _), text in zip(batch, texts, strict=True)]})
            n_new += len(batch)
            pulse(kind, n_new, total, start, name, shard)


def score(names, config):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    require_cards(pair=True)
    mapping_path = OUT / "wjb_mapping255.json"
    mapping = load(mapping_path)
    assert mapping["protocol_sha256"] == digest(PROTOCOL)
    hb_path = ROOT / "repos/HarmBench/data/behavior_datasets/harmbench_behaviors_text_all.csv"
    assert digest(hb_path) == mapping["hb_sha256"]
    references = {r["BehaviorID"]: r["Behavior"] for r in csv_rows(hb_path)}
    tokenizer = AutoTokenizer.from_pretrained(config["judge"], local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        config["judge"], torch_dtype=torch.bfloat16, device_map="auto",
        max_memory={0: "13GiB", 1: "13GiB", "cpu": "0GiB"}, local_files_only=True,
    ).eval()
    assert not {"cpu", "disk"} & set(model.hf_device_map.values())
    gate = official_functions(ROOT / "tools/handoff_20261106/pair500_eval254.py", {"legacy_gate"})
    gate.update(ROOT=ROOT, EVAL=EVAL, official_functions=official_functions, load=load, write=write,
                utc=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    gate["legacy_gate"](tokenizer, model, torch)
    template = harmbench_scope(ROOT / "repos/HarmBench/eval_utils.py", "classifier")["LLAMA2_CLS_PROMPT"]["prompt"]
    mapping_sha = digest(mapping_path)
    for name in names:
        start = time.monotonic()
        n = 0
        for row in mapping["rows"]:
            if SNAPSHOT.exists():
                return
            key = row["id"]
            if name == "alpha0":
                src = OUT / "public_wjb_a0.private" / f"{key}.json"
            else:
                src = EVAL / "harmful.private" / name / "wildjailbreak_harmful" / f"{key}.json"
            if not src.exists():
                continue
            dst = EVAL / "mapped_scores" / name / f"{key}.json"
            sig = {"generation_sha256": digest(src), "mapping_sha256": mapping_sha}
            if dst.exists():
                signed(dst, sig)
                continue
            generation = load(src)
            if name == "alpha0":
                assert generation["plan_sha256"] == digest(PLAN)
                text = generation["text"]
            else:
                text = generation["items"][0]["text"]
            behavior = references[row["candidates"][0]["behavior_id"]]
            prompt = template.format(behavior=behavior, generation=clip(tokenizer, text, 512))
            tokens = tokenizer(prompt, return_tensors="pt").to(model.device)
            with torch.inference_mode():
                output = model.generate(**tokens, max_new_tokens=1, do_sample=False,
                                        pad_token_id=tokenizer.eos_token_id)
            label = {"yes": 1, "no": 0}.get(tokenizer.decode(output[0, -1:], skip_special_tokens=True).strip().lower())
            write(dst, {"id": key, "signature": sig, "label": label})
            n += 1
            if n % 10 == 0:
                pulse("judge", n, len(mapping["rows"]), start, name)


def guard_public(config):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    require_cards()
    tok = AutoTokenizer.from_pretrained(config["guard"], local_files_only=True)
    mdl = AutoModelForCausalLM.from_pretrained(
        config["guard"], torch_dtype=torch.bfloat16, device_map={"": "cuda:0"}, local_files_only=True,
    ).eval()
    safe, unsafe = [tok.encode(label, add_special_tokens=False) for label in ("safe", "unsafe")]
    assert len(safe) == len(unsafe) == 1
    source = ROOT / "tools/handoff_20261106/guard_qwen_output.py"
    assert digest(source) == load(PLAN)["guard_source_sha256"]
    fn = official_functions(source, {"score"})
    fn.update(tok=tok, mdl=mdl, torch=torch, safe=safe, unsafe=unsafe)
    ref = load(ROOT / "status/guard_output2.json")["alpha0_full"]
    old = load(ROOT / "results/audit/RERUN_v70_a0.0_b8f62434.json")
    keys = sorted(load(ROOT / "configs/stage0_data/val70_ids.json")["ids"],
                  key=lambda k: abs(ref[k] - .5))[:20]
    delta = max(abs(fn["score"](old[k]["text"])[0] - ref[k]) for k in keys)
    assert len(keys) == 20 and delta < .001
    write(EVAL / "guard20_gate.json", {"n": len(keys), "max_abs_delta": delta, "passed": True})
    for folder in sorted((EVAL / "public.private" / "alpha0").glob("*")):
        for path in sorted(folder.glob("*.json")):
            if SNAPSHOT.exists():
                return
            dest = EVAL / "public_guard_scores" / folder.name / path.name
            sig = {"generation_sha256": digest(path), "guard_source_sha256": digest(source)}
            if dest.exists():
                signed(dest, sig)
                continue
            items = [{"id": r["id"], "p_unsafe": fn["score"](r["text"])[0]} for r in load(path)["items"]]
            write(dest, {"signature": sig, "items": items})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=("public", "harmful", "score", "guard-public"))
    p.add_argument("conditions", nargs="+")
    p.add_argument("--shard", type=int, choices=(0, 1), default=0)
    args = p.parse_args()
    os.umask(0o077)
    sys.path.insert(0, str(ROOT / "src"))
    config = load(CFG)
    assert digest(PROTOCOL) == "a12cf4a86ce1d80deb6b1ee89533ba4b9410215574ca1a21d8cafa35e984b5df"
    if args.stage == "score":
        score(args.conditions, config)
    elif args.stage == "guard-public":
        assert args.conditions == ["alpha0"]
        guard_public(config)
    else:
        assert len(args.conditions) == 1
        generate(args.stage, args.conditions[0], args.shard, config)


if __name__ == "__main__":
    main()
