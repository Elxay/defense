"""Run frozen PAIR search on alpha=0, then generate one evaluation completion per row."""
import argparse
import ast
import datetime
import hashlib
import json
import os
import re
import time
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def contextual_prompt(context, candidate):
    return f"{context}\n\n---\n\n{candidate}" if context else candidate


def official_functions(source, names):
    tree = ast.parse(source.read_text())
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == set(names)
    scope = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), scope)
    return scope


def parse_candidate(text):
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get("prompt"), str) and value["prompt"].strip():
            return value
    return None


def gpu_roles(phase):
    value = os.environ.get("DEVICE", "")
    if not re.fullmatch(r"cuda:\d+", value):
        raise SystemExit("DEVICE must identify the physical primary GPU as cuda:N")
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")
    if len(visible) != 2 or len(set(visible)) != 2 or visible[0] != value.split(":")[1]:
        raise SystemExit(f"{phase} requires two isolated GPUs, with DEVICE first in CUDA_VISIBLE_DEVICES")
    return visible


class LocalModel:
    def __init__(self, path, device):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        self.tokenizer.padding_side = "left"
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            path, torch_dtype=torch.bfloat16, device_map={"": device}, local_files_only=True,
        ).eval()

    def generate(self, messages, cap, temperature=0, thinking=None):
        import torch

        extra = {} if thinking is None else {"enable_thinking": thinking}
        rendered = [self.tokenizer.apply_chat_template(
            item, tokenize=False, add_generation_prompt=True, **extra,
        ) for item in messages]
        batch = self.tokenizer(rendered, padding=True, add_special_tokens=False, return_tensors="pt").to(self.device)
        options = {"do_sample": False} if temperature == 0 else {
            "do_sample": True, "temperature": temperature, "top_p": 1.0, "top_k": 0,
        }
        with torch.inference_mode():
            output = self.model.generate(
                **batch, max_new_tokens=cap, pad_token_id=self.tokenizer.pad_token_id, **options,
            )
        return self.tokenizer.batch_decode(output[:, batch.input_ids.shape[1]:], skip_special_tokens=True)


def search_row(row, config, attacker, target, upstream, refusal, heartbeat):
    behavior, context, prefix = row["behavior"], row["context"], row["target"]
    system = upstream["get_attacker_system_prompt"](behavior, context, prefix)
    initial = upstream["get_init_msg"](behavior, prefix, context)
    starter = [{"role": "system", "content": system}, {"role": "user", "content": initial}]
    histories = [list(starter) for _ in range(config["streams"])]
    best = None
    target_calls = 0
    valid_candidates = 0
    for step in range(config["steps"]):
        outputs = attacker.generate(
            histories, config["attacker_max_new_tokens"], config["attack_temperature"], thinking=False,
        )
        candidates = []
        for index, output in enumerate(outputs):
            parsed = parse_candidate(output)
            if parsed is None:
                histories[index] = list(starter)
            else:
                candidates.append((index, parsed))
        prompts = [contextual_prompt(context, item["prompt"]) for _, item in candidates]
        if prompts:
            texts = target.generate(
                [[{"role": "user", "content": prompt}] for prompt in prompts], config["search_target_max_new_tokens"],
            )
        else:
            texts = []
        assert len(texts) == len(candidates)
        target_calls += len(texts)
        valid_candidates += len(texts)
        for (index, parsed), prompt, response in zip(candidates, prompts, texts):
            length = len(target.tokenizer.encode(response, add_special_tokens=False))
            nonrefusal = bool(response.strip()) and not refusal(response)
            score = (int(nonrefusal), length)
            if best is None or score > best["score"]:
                best = {"prompt": prompt, "score": score, "round": step + 1, "stream": index}
            feedback = 1 if not nonrefusal else 2 + 8 * min(length, config["search_target_max_new_tokens"]) / config["search_target_max_new_tokens"]
            history = histories[index] + [
                {"role": "assistant", "content": json.dumps(parsed, ensure_ascii=False)},
                {"role": "user", "content": upstream["process_target_response"](
                    response, round(feedback, 3), behavior, prefix, context,
                )},
            ]
            histories[index] = [starter[0]] + history[1:][-2 * config["keep_last_feedback_turns"] - 1:]
            # Preserve the user/assistant alternation expected by the model template.
            if histories[index][1]["role"] != "user":
                raise RuntimeError("invalid PAIR conversation structure")
        heartbeat("search", row["id"], step + 1)
    fallback = best is None
    if fallback:
        best = {"prompt": contextual_prompt(context, behavior), "score": None, "round": None, "stream": None}
    return best, target_calls, valid_candidates, fallback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--attacker", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--limit", required=True, type=int)
    args = parser.parse_args()
    physical = gpu_roles("PAIR search")
    import sys
    import torch

    sys.path.insert(0, str(args.root / "src"))
    from judge.refusal import new_rule

    root = args.root
    directory = root / "results/audit/pair500"
    config_path = directory / "config.json"
    config = load(config_path)
    rows_path = directory / "rows.private.json"
    rows = load(rows_path)
    assert 1 <= args.limit <= len(rows) == 500
    assert digest(rows_path) == config["rows_sha256"]
    script = Path(__file__)
    assert digest(script) == config["worker_sha256"]
    assert (directory / "publication.json").exists(), "Freeze and push docs/253 before generation"
    for role in ("attacker", "target"):
        path = getattr(args, role)
        assert digest(path / "model.safetensors.index.json") == config[f"{role}_index_sha256"]
    publication = load(directory / "publication.json")
    assert digest(root / "docs/253_PAIR500_ROW_PROTOCOL.md") == publication["doc_sha256"]
    assert digest(config_path) == publication["config_sha256"]
    source = root / "repos/HarmBench/baselines/pair"
    for path in (source / "system_prompts.py", source / "common.py", root / "src/judge/refusal.py"):
        assert digest(path) == config["source_sha256"][str(path.relative_to(root))]
    upstream = official_functions(source / "system_prompts.py", {"get_attacker_system_prompt"})
    upstream.update(official_functions(source / "common.py", {"get_init_msg", "process_target_response"}))
    data = directory / "generations.private"
    signature = digest(config_path)
    selected = rows[:args.limit]
    pending = []
    for row in selected:
        path = data / f"{row['id']}.json"
        if path.exists():
            record = load(path)
            assert record["config_sha256"] == signature and record["id"] == row["id"]
        else:
            pending.append(row)

    def heartbeat(phase, row=None, step=None):
        write(directory / "generation_live.json", {
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "pid": os.getpid(),
            "gpus": physical, "phase": phase, "row": row, "round": step,
            "saved": sum((data / f"{r['id']}.json").exists() for r in selected), "limit": args.limit,
        })

    if not pending:
        heartbeat("complete")
        return
    heartbeat("loading")
    start = time.monotonic()
    attacker = LocalModel(args.attacker, "cuda:0")
    target = LocalModel(args.target, "cuda:1")
    write(directory / "generation_load.json", {"seconds": time.monotonic() - start, "gpus": physical})
    for row in pending:
        start = time.monotonic()
        seed = int.from_bytes(hashlib.sha256(f"{config['seed']}:{row['id']}".encode()).digest()[:4], "big")
        torch.manual_seed(seed)
        best, calls, valid, fallback = search_row(row, config, attacker, target, upstream, new_rule, heartbeat)
        search_seconds = time.monotonic() - start
        heartbeat("alpha0", row["id"])
        final = target.generate([[{"role": "user", "content": best["prompt"]}]], config["eval_target_max_new_tokens"])[0]
        elapsed = time.monotonic() - start
        record = {
            "id": row["id"], "layer": row["layer"], "config_sha256": signature,
            "best": best, "alpha0": final, "fallback": fallback, "seed": seed,
            "target_search_calls": calls, "valid_candidates": valid, "search_seconds": search_seconds,
            "alpha0_seconds": elapsed - search_seconds, "seconds": elapsed, "gpus": physical,
        }
        write(data / f"{row['id']}.json", record)
        print(f"ROW_COMPLETE {row['id']} {row['layer']} {elapsed:.2f}s calls={calls}", flush=True)
        heartbeat("saved", row["id"])
    heartbeat("complete")


if __name__ == "__main__":
    main()
