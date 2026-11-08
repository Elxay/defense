"""Run public refusal generation or the mapped-reference WildJailbreak evaluator."""
import argparse
import collections
import datetime
import json
import os
import socket
import hashlib
import sys
import time
from pathlib import Path

import numpy as np
from pair500_eval254 import OUT, ROOT, clip, harmbench_scope, require_cards, signed
from pair500_generate import digest, load, official_functions, write
from public_wjb_alpha0_gate import LLAMA, PLAN, rows as harmful_rows
from wjb_eval255_map import csv_rows

EVAL = OUT / "public255"
PROTOCOL = ROOT / "docs/255_WJB_PUBLIC_EVAL_PROTOCOL.md"
SNAPSHOT = OUT / "frozen_prompt_snapshot.json"
CFG = OUT / "eval255_frozen_runtime_config.json"


def snapshot_preempts(condition=None):
    if not SNAPSHOT.exists():
        return False
    mode = os.environ.get("WJB_POST_SNAPSHOT_MODE", "")
    if mode == "post_pair":
        assert load(OUT / "full_queue_live.json").get("phase") == "complete", "PAIR GPU work must finish before tail resume"
        return False
    if mode == "last_condition":
        decision = load(OUT / "pair_priority_trigger.json")
        assert decision.get("last_condition_exemption") and decision.get("remaining_conditions") == [condition]
        assert not decision.get("active")
        return False
    return True


def pulse(stage, done, total, start, condition, shard=0, timed_rows=None):
    write(EVAL / f"live_{stage}_{condition}_{shard}.json", {
        "pid": os.getpid(), "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "device": os.environ["DEVICE"], "n": done, "total": total,
        "seconds_per_row": (time.monotonic() - start) / max(1, done if timed_rows is None else timed_rows),
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


def baseline_source(key):
    marker = EVAL / "alpha0_active_baseline.json"
    regenerated = marker.exists() and load(marker)["lane"] == "zero_regenerated"
    return ((EVAL / "harmful.private/alpha0/wildjailbreak_harmful" / f"{key}.json")
            if regenerated else (OUT / "public_wjb_a0.private" / f"{key}.json"))


def baseline_text(record):
    return record["text"] if "text" in record else record["items"][0]["text"]


def activate_baseline():
    plan = load(PLAN)
    assert len(plan["ids"]) == len(set(plan["ids"])) == 2000
    check_path = EVAL / "zero20_check.json"
    check = load(check_path)
    lane = "native" if check["byte_identical"] == 20 else "zero_regenerated"
    sources = []
    for key in plan["ids"]:
        p = ((OUT / "public_wjb_a0.private" / f"{key}.json") if lane == "native" else
             (EVAL / "harmful.private/alpha0/wildjailbreak_harmful" / f"{key}.json"))
        record = load(p)
        if lane == "native":
            assert record["plan_sha256"] == digest(PLAN)
        else:
            assert record["signature"]["condition"] == "alpha0"
            assert record["signature"]["config_sha256"] == digest(CFG)
            assert record["generation"]["injection_count"] == 1
            assert record["generation"]["rho_runtime"] == 0
        sources.append({"id": key, "sha256": digest(p)})
    manifest = EVAL / "alpha0_active_files.json"
    write(manifest, sources)
    write(EVAL / "alpha0_active_baseline.json", {"lane": lane, "n": len(sources),
          "zero20_sha256": digest(check_path), "manifest_sha256": digest(manifest),
          "superseded_native": lane != "native"})

def observed_public_batch(scope, batch):
    """Observe the existing batch hook without changing its tensor result."""
    layer = scope["mdl"].model.layers[scope["LAYER"]]
    original_register = layer.register_forward_hook
    events = []

    def register(callback, *args, **kwargs):
        def observe(module, inputs, output):
            result = callback(module, inputs, output)
            if result[0] is not output[0]:
                delta = (result[0][:, -1, :] - output[0][:, -1, :]).float()
                events.append(delta.norm(dim=-1).cpu().tolist())
            return result
        return original_register(observe, *args, **kwargs)

    try:
        layer.register_forward_hook = register
        texts = scope["run_batch"](batch)
    finally:
        layer.register_forward_hook = original_register
    assert len(events) == 1 and len(events[0]) == len(batch)
    return texts, events[0]


def generate(kind, name, shard, config):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from gen.common import generate_with_injection
    from judge.refusal import new_rule

    require_cards()
    if kind == "harmful" and name == "old_s3":
        from verify_public_first_resume import verify
        verify(shard, "before")
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
    if kind == "harmful" and name != "alpha0":
        assert load(EVAL / "alpha0_active_baseline.json")["n"] == 2000
    start = time.monotonic()
    n_new = 0
    total = sum(len(rows) for _, rows in datasets) if kind == "harmful" else sum(
        len(rows[offset:offset + 8]) for _, rows in datasets for offset in range(shard * 8, len(rows), 16)
    )
    initial = 0
    for dataset, data in datasets:
        offsets = range(shard * 8, len(data), 16) if kind == "public" else range(len(data))
        for offset in offsets:
            batch = data[offset:offset + (8 if kind == "public" else 1)]
            cached = EVAL / f"{kind}.private" / name / dataset / f"{batch[0][0]}.json"
            if cached.exists():
                initial += len(batch)
    if initial == total:
        return
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
            if snapshot_preempts(name):
                return
            batch = data[offset:offset + (8 if kind == "public" else 1)]
            out = EVAL / f"{kind}.private" / name / dataset / f"{batch[0][0]}.json"
            signature = {"protocol_sha256": protocol_sha, "config_sha256": config_sha,
                         "dataset": dataset, "condition": name, "ids": [k for k, _ in batch]}
            if out.exists():
                signed(out, signature)
                continue
            if kind == "public":
                texts, delta_norms = observed_public_batch(scope, [(i, dataset, p) for i, (_, p) in enumerate(batch)])
            else:
                messages = ([{"role": "system", "content": system}] if system else []) + [
                    {"role": "user", "content": batch[0][1]}]
                ids = tok.apply_chat_template(messages, add_generation_prompt=True,
                                              return_tensors="pt").to("cuda:0")
                runtime = np.zeros(4096, dtype=np.float32) if vec is None else vec
                result = generate_with_injection(
                    model, tok, ids, runtime, layer=9, max_new_tokens=2400, device="cuda:0",
                    src_vec_sha256=spec.get("file_sha256"), alpha=spec["alpha"])
                result.update(host=socket.gethostname(), physical_device=os.environ["DEVICE"],
                              rho_runtime=float(np.linalg.norm(runtime)))
                texts = [result["text"]]
            record = {"signature": signature, "items": [
                {"id": key, "text": text, "v2_refusal": new_rule(text)}
                for (key, _), text in zip(batch, texts, strict=True)]}
            if kind == "public":
                for item, delta_norm in zip(record["items"], delta_norms, strict=True):
                    item.update(
                        vector_sha256=spec.get("file_sha256"), injection_count=1 if vec is not None else 0,
                        prefill_hook_count=1, rho_runtime=float(np.linalg.norm(vec)) if vec is not None else 0.0,
                        delta_norm_runtime=delta_norm, host=socket.gethostname(),
                        physical_device=os.environ["DEVICE"],
                        device_uuid=str(torch.cuda.get_device_properties(0).uuid),
                        metadata_origin="observed original batch8 hook",
                    )
            if kind == "harmful":
                record["generation"] = result
            write(out, record)
            n_new += len(batch)
            pulse(kind, initial + n_new, total, start, name, shard, timed_rows=n_new)

    if kind == "harmful" and name == "old_s3":
        verify(shard, "after")


def score(names, config, sensitivity=False):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    require_cards(pair=True)
    from hb_judge_preflight import prepare, reference_failed, reference_passed
    launch_dir, launch_record = prepare(names, config["judge"])
    if sensitivity:
        assert digest(ROOT / "docs/255_ADDENDUM3_RANDOM_REFERENCE.md") == "939abf789acb028d632d1caf2288c78b121bdcef98a9ce3cf6e3d72937f8d6fb"
        assert len(list((OUT / "public_wjb_a0.private").glob("*.json"))) == 2000, "Wait for all alpha0 rows"
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
    gate.update(ROOT=ROOT, EVAL=launch_dir, official_functions=official_functions, load=load, write=write,
                utc=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        gate["legacy_gate"](tokenizer, model, torch)
    except Exception as exc:
        reference_failed(launch_dir, exc)
        raise
    write(EVAL / "judge20_gate.json", load(launch_dir / "judge20_gate.json"))
    reference_passed(launch_dir, launch_record)
    template = harmbench_scope(ROOT / "repos/HarmBench/eval_utils.py", "classifier")["LLAMA2_CLS_PROMPT"]["prompt"]
    mapping_sha = digest(mapping_path)
    random_refs = {r["id"]: r["random_behavior"] for r in load(OUT / "wjb_random_reference200.json")} if sensitivity else {}
    yes_ids = tokenizer.encode("Yes", add_special_tokens=False)
    no_ids = tokenizer.encode("No", add_special_tokens=False)
    assert len(yes_ids) == len(no_ids) == 1
    for name in names:
        start = time.monotonic()
        n = 0
        for row in mapping["rows"]:
            if snapshot_preempts(name):
                return
            key = row["id"]
            if name == "alpha0":
                src = baseline_source(key)
            else:
                src = EVAL / "harmful.private" / name / "wildjailbreak_harmful" / f"{key}.json"
            if not src.exists():
                continue
            generation = load(src)
            if name == "alpha0":
                text = baseline_text(generation)
            else:
                text = generation["items"][0]["text"]
            kinds = ("top1", "top2", "random") if sensitivity else ("top1",)
            for kind in kinds:
                if kind == "random" and key not in random_refs:
                    continue
                behavior_id = (random_refs[key] if kind == "random" else
                               row["candidates"][0 if kind == "top1" else 1]["behavior_id"])
                directory = ("mapped_scores" if kind == "top1" else
                             "mapped_top2_scores" if kind == "top2" else "random_reference_scores")
                dst = EVAL / directory / name / f"{key}.json"
                sig = {"generation_sha256": digest(src), "mapping_sha256": mapping_sha}
                if kind == "random":
                    sig["random_plan_sha256"] = digest(OUT / "wjb_random_reference200.json")
                if dst.exists():
                    signed(dst, sig)
                    continue
                behavior = references[behavior_id]
                prompt = template.format(behavior=behavior, generation=clip(tokenizer, text, 512))
                tokens = tokenizer(prompt, return_tensors="pt").to(model.device)
                with torch.inference_mode():
                    output = model.generate(**tokens, max_new_tokens=1, do_sample=False,
                                            pad_token_id=tokenizer.eos_token_id,
                                            return_dict_in_generate=True, output_logits=True)
                label = {"yes": 1, "no": 0}.get(tokenizer.decode(output.sequences[0, -1:], skip_special_tokens=True).strip().lower())
                pair_logits = output.logits[0][0, [yes_ids[0], no_ids[0]]].float()
                p_yes = float(torch.softmax(pair_logits, dim=-1)[0])
                write(dst, {"id": key, "signature": sig, "label": label, "p_yes": p_yes,
                            "behavior_id": behavior_id, "method": "hf_innet_standard",
                            "probability_definition": "raw_Yes_No_pair_normalized"})
            n += 1
            if n % 10 == 0:
                pulse("sensitivity" if sensitivity else "judge", n, len(mapping["rows"]), start, name)


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
            if snapshot_preempts():
                return
            dest = EVAL / "public_guard_scores" / folder.name / path.name
            sig = {"generation_sha256": digest(path), "guard_source_sha256": digest(source)}
            if dest.exists():
                signed(dest, sig)
                continue
            items = [{"id": r["id"], "p_unsafe": fn["score"](r["text"])[0]} for r in load(path)["items"]]
            write(dest, {"signature": sig, "items": items})


def zero_check(config):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from gen.common import generate_with_injection

    require_cards()
    keys = (OUT / "wjb_alpha0_zero20_ids.txt").read_text().splitlines()
    assert len(keys) == len(set(keys)) == 20
    data = harmful_rows(load(PLAN))
    tok = AutoTokenizer.from_pretrained(LLAMA, local_files_only=True)
    mdl = AutoModelForCausalLM.from_pretrained(
        LLAMA, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"}, local_files_only=True,
    ).eval()
    rows = []
    for key in keys:
        ids = tok.apply_chat_template([{"role": "user", "content": data[key]}],
                                     add_generation_prompt=True, return_tensors="pt").to("cuda:0")
        vector = np.zeros(4096, dtype=np.float32)
        result = generate_with_injection(mdl, tok, ids, vector, layer=9, max_new_tokens=2400, alpha=0.0)
        result.update(host=socket.gethostname(), physical_device=os.environ["DEVICE"], rho_runtime=0.0)
        old = load(OUT / "public_wjb_a0.private" / f"{key}.json")
        assert old["plan_sha256"] == digest(PLAN)
        write(EVAL / "zero20.private" / f"{key}.json", result)
        proxy = len(tok.encode(old["text"], add_special_tokens=False)) >= 2390
        truth = result["new_tokens"] >= 2400
        rows.append({"id": key, "byte_identical": old["text"].encode() == result["text"].encode(),
                     "proxy_ge2390": proxy, "true_cap2400": truth,
                     "new_tokens": result["new_tokens"],
                     "old_retokenized_length": len(tok.encode(old["text"], add_special_tokens=False))})
    matrix = {f"proxy{int(p)}_true{int(t)}": sum(r["proxy_ge2390"] == p and r["true_cap2400"] == t for r in rows)
              for p in (False, True) for t in (False, True)}
    summary = {"n": 20, "byte_identical": sum(r["byte_identical"] for r in rows), "cap_proxy_2x2": matrix, "rows": rows}
    write(EVAL / "zero20_check.json", summary)
    # A mismatch selects full baseline regeneration in the supervisor.


def main():
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=("public", "harmful", "score", "guard-public", "sensitivity", "zero-check", "activate-baseline"))
    p.add_argument("conditions", nargs="+")
    p.add_argument("--shard", type=int, choices=(0, 1), default=0)
    args = p.parse_args()
    os.umask(0o077)
    sys.path.insert(0, str(ROOT / "src"))
    config = load(CFG)
    assert digest(PROTOCOL) == "a12cf4a86ce1d80deb6b1ee89533ba4b9410215574ca1a21d8cafa35e984b5df"
    if args.stage == "score":
        score(args.conditions, config)
    elif args.stage == "activate-baseline":
        activate_baseline()
    elif args.stage == "zero-check":
        zero_check(config)
    elif args.stage == "sensitivity":
        assert args.conditions == ["alpha0"]
        score(args.conditions, config, sensitivity=True)
    elif args.stage == "guard-public":
        assert args.conditions == ["alpha0"]
        guard_public(config)
    else:
        assert len(args.conditions) == 1
        generate(args.stage, args.conditions[0], args.shard, config)


if __name__ == "__main__":
    main()
