"""Measure the selected search response's token cap around the unchanged PAIR worker."""
import argparse
import hashlib
from pathlib import Path

import pair500_generate as worker


def watch_search(original, target, cap, *args):
    row, _, _, _, _, _, heartbeat = args
    rounds = []
    stream = []
    records = {}
    parse = worker.parse_candidate
    generate = target.model.generate

    def parse_candidate(text):
        candidate = parse(text)
        stream.append(candidate is not None)
        return candidate

    def capture(**kwargs):
        result = generate(**kwargs)
        if kwargs["max_new_tokens"] == cap:
            continuation = result[:, kwargs["input_ids"].shape[1]:]
            eos = target.model.generation_config.eos_token_id
            eos = set(eos if isinstance(eos, (list, tuple)) else [eos])
            valid = [i for i, ok in enumerate(stream) if ok]
            assert len(valid) == continuation.shape[0]
            for i, tokens in zip(valid, continuation.cpu().tolist()):
                end = next((j + 1 for j, token in enumerate(tokens) if token in eos), None)
                records[len(rounds) + 1, i] = (end or len(tokens), end is not None)
        return result

    def pulse(*values):
        heartbeat(*values)
        stream.clear()
        rounds.append(None)

    try:
        worker.parse_candidate = parse_candidate
        target.model.generate = capture
        result = original(*args[:-1], pulse)
    finally:
        worker.parse_candidate = parse
        target.model.generate = generate
    best = result[0]
    key = best["round"], best["stream"]
    count, eos = (None, None) if result[3] else records[key]
    return result, {
        "id": row["id"], "round": key[0], "stream": key[1], "generated_tokens": count,
        "reached_cap": None if count is None else count == cap,
        "cap_without_eos": None if count is None else count == cap and not eos,
        "prompt_sha256": hashlib.sha256(best["prompt"].encode()).hexdigest(),
    }


def cap_summary(directory, rows):
    exact = []
    pilot_proxy = []
    for row in rows:
        key = row["id"]
        p = directory / "search_cap.private" / f"{key}.json"
        if p.exists():
            detail = worker.load(p)
            assert detail["prompt_sha256"] == row["prompt_sha256"]
            exact.append(detail)
        else:
            record = worker.load(directory / "generations.private" / f"{key}.json")
            score = record["best"]["score"]
            pilot_proxy.append(score is not None and score[1] >= 512)
    return {
        "exact_n": len(exact), "exact_selected_n": sum(x["generated_tokens"] is not None for x in exact),
        "exact_reached_512": sum(x["reached_cap"] is True for x in exact),
        "exact_reached_512_without_eos": sum(x["cap_without_eos"] is True for x in exact),
        "pilot_without_token_trace_n": len(pilot_proxy),
        "pilot_decoded_then_retokenized_at_least_512": sum(pilot_proxy),
    }


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", required=True, type=Path)
    args, _ = parser.parse_known_args()
    directory = args.root / "results/audit/pair500/search_cap.private"
    directory.mkdir(exist_ok=True)
    original = worker.search_row

    def search(row, config, attacker, target, upstream, refusal, heartbeat):
        result, cap = watch_search(
            original, target, config["search_target_max_new_tokens"],
            row, config, attacker, target, upstream, refusal, heartbeat,
        )
        worker.write(directory / f"{row['id']}.json", cap)
        return result

    worker.search_row = search
    worker.main()


if __name__ == "__main__":
    main()
