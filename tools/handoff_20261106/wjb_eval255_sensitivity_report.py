"""Summarize label changes under alternate references without publishing any text."""
import collections

import numpy as np
from transformers import AutoTokenizer

from pair500_generate import digest, load, write
from wjb_eval255_report import cluster_interval
from wjb_eval255_run import CFG, EVAL, OUT, PLAN, ROOT


def summarize(values):
    if not values:
        return None
    values = np.asarray(values)
    return {"n": len(values), "mean": float(values.mean()), "quartiles": np.quantile(values, [.25, .5, .75]).tolist(),
            "above_0p5": int((values > .5).sum()), "above_0p9": int((values > .9).sum())}


def sensitivity():
    mapping = load(OUT / "wjb_mapping255.json")["rows"]
    a = {p.stem: load(p) for p in (EVAL / "mapped_scores/alpha0").glob("*.json")}
    b = {p.stem: load(p) for p in (EVAL / "mapped_top2_scores/alpha0").glob("*.json")}
    random = {p.stem: load(p) for p in (EVAL / "random_reference_scores/alpha0").glob("*.json")}
    layers = {}
    for name, predicate in {
        "all": lambda row: True, "high_confidence": lambda row: not (row["low_similarity"] or row["low_margin"]),
        "low_confidence": lambda row: row["low_similarity"] or row["low_margin"],
        "margin_below_0p05": lambda row: row["low_margin"],
    }.items():
        selected = [r for r in mapping if predicate(r)]
        scored = [r for r in selected if r["id"] in a and r["id"] in b]
        valid = [r for r in scored if a[r["id"]]["label"] is not None and b[r["id"]]["label"] is not None]
        changes = [(r["group"], int(a[r["id"]]["label"] != b[r["id"]]["label"])) for r in valid]
        rate = sum(v for _, v in changes) / len(changes) if changes else None
        layers[name] = {"planned": len(selected), "scored_pairs": len(scored), "valid_pairs": len(valid),
                        "either_invalid": len(scored) - len(valid), "disagreements": sum(v for _, v in changes),
                        "disagreement_rate": rate, "cluster_95ci": cluster_interval(changes),
                        "absolute_rate_descriptive_only": rate is not None and rate > .15}
    common = sorted(set(a) & set(random))
    paired = [k for k in common if a[k]["label"] is not None and random[k]["label"] is not None]
    return {"layers": layers, "random_reference": {
        "planned": 200, "scored_pairs": len(common), "valid_pairs": len(paired),
        "label_disagreements": sum(a[k]["label"] != random[k]["label"] for k in paired),
        "top1_p_yes": summarize([a[k]["p_yes"] for k in common]),
        "random_p_yes": summarize([random[k]["p_yes"] for k in common]),
        "top1_minus_random_p_yes": summarize([a[k]["p_yes"] - random[k]["p_yes"] for k in common]),
    }, "interpretation": "Reference-substitution sensitivity does not verify mapping correctness."}


def baseline_generation():
    config = load(CFG)
    tok = AutoTokenizer.from_pretrained(config["target"], local_files_only=True)
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from judge.refusal import new_rule
    plan = load(PLAN)
    files = [OUT / "public_wjb_a0.private" / f"{k}.json" for k in plan["ids"]]
    available = [p for p in files if p.exists()]
    assert len(available) == 2000, "Generation summary requires all 2000 rows"
    counts = collections.Counter()
    for path in available:
        row = load(path)
        assert row["plan_sha256"] == digest(PLAN)
        text = row["text"]
        counts["v2_refused"] += new_rule(text)
        counts["empty_after_strip"] += not text.strip()
        counts["decoded_retokenized_at_least_2400"] += len(tok.encode(text, add_special_tokens=False)) >= 2400
    return {"planned": 2000, "generated": len(available), **dict(counts),
            "v2_refusal_rate": counts["v2_refused"] / len(available),
            "exact_generated_token_cap": None,
            "cap_limitation": "Historical generator saved decoded text but omitted raw token count and EOS. Re-tokenized length is a proxy."}


if __name__ == "__main__":
    write(EVAL / "alpha0_generation_summary.json", baseline_generation())
    write(EVAL / "reference_sensitivity_summary.json", sensitivity())
