"""Clustered row and group summaries for retained-row evaluations."""
import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from pair500_generate import digest, load, write

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/audit/pair500"
AUDIT = ROOT / "results/audit"
BOOT_SEED = 20261108
BOOT_REPS = 10000
sys.path.insert(0, str(ROOT / "src"))
from judge.refusal import new_rule


def cluster_interval(values, groups, equal_groups=False):
    clusters = defaultdict(list)
    for value, group in zip(values, groups, strict=True):
        if value is not None:
            clusters[group].append(value)
    if not clusters:
        return {"mean_pct": None, "ci95_pct": [None, None], "scored_rows": 0, "scored_groups": 0}
    ordered = [clusters[k] for k in sorted(clusters)]
    sums = np.array([sum(xs) for xs in ordered], dtype=float)
    sizes = np.array([len(xs) for xs in ordered], dtype=int)
    if equal_groups:
        numerators, weights = sums / sizes, np.ones_like(sizes)
    else:
        numerators, weights = sums, sizes
    indices = np.random.default_rng(BOOT_SEED).integers(len(ordered), size=(BOOT_REPS, len(ordered)))
    boot = numerators[indices].sum(axis=1) / weights[indices].sum(axis=1)
    return {
        "mean_pct": float(100 * numerators.sum() / weights.sum()),
        "ci95_pct": (np.quantile(boot, [0.025, 0.975]) * 100).tolist(),
        "scored_rows": int(sizes.sum()), "scored_groups": len(ordered),
    }


def summarize(rows, score_fn, equal_groups=False):
    result = cluster_interval([score_fn(r["id"]) for r in rows],
                              [r["group"] for r in rows], equal_groups=equal_groups)
    return {"planned_rows": len(rows), "planned_groups": len({r["group"] for r in rows}), **result}


def stratified_summary(rows, score_fn):
    layers = sorted({r["layer"] for r in rows})
    plan = np.array([sum(r["layer"] == layer for r in rows) for layer in layers], dtype=float)
    measured = defaultdict(list)
    for row in rows:
        value = score_fn(row["id"])
        if value is not None:
            measured[row["group"]].append((layers.index(row["layer"]), value))
    sums = np.zeros((len(measured), len(layers)))
    counts = np.zeros_like(sums)
    for i, group in enumerate(sorted(measured)):
        for layer, value in measured[group]:
            sums[i, layer] += value
            counts[i, layer] += 1
    n = counts.sum(axis=0)
    result = {
        "source_layer_n": dict(zip(layers, plan.astype(int).tolist())),
        "scored_layer_n": dict(zip(layers, n.astype(int).tolist())),
        "mean_pct": None, "ci95_pct": [None, None], "valid_bootstrap_replicates": 0,
    }
    if not all(n):
        return result
    result["mean_pct"] = float(100 * np.average(sums.sum(axis=0) / n, weights=plan))
    rng = np.random.default_rng(BOOT_SEED)
    estimates = []
    for _ in range(0, BOOT_REPS, 250):
        ix = rng.integers(len(measured), size=(250, len(measured)))
        denom = counts[ix].sum(axis=1)
        valid = np.all(denom > 0, axis=1)
        estimates.extend(np.average(sums[ix[valid]].sum(axis=1) / denom[valid], axis=1, weights=plan))
    result["valid_bootstrap_replicates"] = len(estimates)
    if estimates:
        result["ci95_pct"] = (100 * np.quantile(estimates, [0.025, 0.975])).tolist()
    return result


def attack_report(conditions):
    records = load(OUT / "row_audit.json")["flags"]
    sets = {"all": records, "untouched": [r for r in records if r["untouched"]]}
    for dataset in ("HarmBench", "JBB"):
        sets[dataset] = [r for r in records if r["dataset"] == dataset]
        sets[f"{dataset}_untouched"] = [r for r in sets[dataset] if r["untouched"]]
    for layer in ("standard", "contextual", "copyright", "jbb"):
        sets[layer] = [r for r in records if r["layer"] == layer]
        sets[f"{layer}_untouched"] = [r for r in sets[layer] if r["untouched"]]

    def primary(identifier):
        names = [f"old_s{s}" for s in range(3, 8)] + [f"rand{s}" for s in range(4)]
        scores = [conditions.get(k, {}).get(identifier) for k in names]
        if any(v is None for v in scores):
            return None
        return np.mean(scores[:5]) - np.mean(scores[5:])

    methods = {name: lambda k, x=labels: x.get(k) for name, labels in conditions.items()}
    if set([f"old_s{s}" for s in range(3, 8)] + [f"rand{s}" for s in range(4)]) <= set(conditions):
        methods["learned_minus_random"] = primary
    report = {
        label: {name: summarize(rows, score) for name, score in methods.items()}
        for label, rows in sets.items()
    }
    for label, layers in {
        "untouched_standard_jbb": {"standard", "jbb"},
        "untouched_contextual_copyright": {"contextual", "copyright"},
    }.items():
        sets[label] = [row for row in sets["untouched"] if row["layer"] in layers]
        report[label] = {name: summarize(sets[label], score) for name, score in methods.items()}
    for label in sets:
        report[f"{label}_behavior_weighted"] = {
            name: summarize(sets[label], score, equal_groups=True) for name, score in methods.items()
        }
    for label in ("all", "untouched", "HarmBench", "HarmBench_untouched"):
        for name, score in methods.items():
            cell = report[label][name]
            if cell["scored_rows"] < cell["planned_rows"]:
                cell["source_layer_weighted_partial"] = stratified_summary(sets[label], score)
    return report


def grouped_key(text):
    return hashlib.sha256(" ".join(text.split()).casefold().encode()).hexdigest()


def existing_report():
    """Use previously read conditions. Current treatment holdout caches are outside this scope."""
    source_hashes = {}

    def get(path):
        source_hashes[str(path.relative_to(ROOT))] = digest(path)
        return load(path)

    def texts(name):
        d = get(AUDIT / name)
        return d.get("items", d)

    legal = get(ROOT / "data/legal_val_items.json")
    legal_rows = [{"id": r["key"], "group": grouped_key(r["prompt"]), "layer": r["group"]} for r in legal]
    out_legal = {}
    for model, names in {
        "Llama": ["none", "SYS_A", "SYS_B"],
        "Qwen": ["qwen_a0", "QWEN_A_replace", "QWEN_A_append", "QWEN_B_replace", "QWEN_B_append"],
    }.items():
        base = {key: new_rule(row["text"]) for key, row in texts(f"LEGALVALB_{names[0]}.json").items()}
        assert len(base) == 400
        sets = {"all": legal_rows, "baseline_nonrefusal": [r for r in legal_rows if not base[r["id"]]],
                "baseline_refusal": [r for r in legal_rows if base[r["id"]]]}
        for layer in sorted({r["layer"] for r in legal_rows}):
            sets[layer] = [r for r in legal_rows if r["layer"] == layer]
        out_legal[model] = {}
        for name in names:
            flags = {key: new_rule(row["text"]) for key, row in texts(f"LEGALVALB_{name}.json").items()}
            assert set(flags) == set(base)
            out_legal[model][name] = {
                k: {
                    "refusal": summarize(rows, lambda i: int(flags[i])),
                    "net_refusal_change": summarize(rows, lambda i: int(flags[i]) - int(base[i])),
                    "new_refusal": summarize(rows, lambda i: int(flags[i] and not base[i])),
                } for k, rows in sets.items()
            }

    wjb = get(ROOT / "configs/stage0_data/wjb300.json")
    wjb_rows = [{"id": r["id"], "group": grouped_key(r["vanilla"])} for r in wjb]
    judge_dir = ROOT / "results/hfjudge"
    paths = {"alpha0": "JUDGE_HF_wjb_a0_innet_round2",
             "rand0": "JUDGE_HF_wjb_rand0_innet_round2", "rand1": "JUDGE_HF_wjb_rand1_innet",
             "rand2": "JUDGE_HF_wjb_rand2_innet_round6", "rand3": "JUDGE_HF_wjb_rand3_innet_round6"}
    for s in range(3, 8):
        suffix = "" if s <= 4 else "_round5"
        paths[f"old_s{s}"] = f"JUDGE_HF_wjb_old_s{s}_a1.0_innet{suffix}"
    flags = {}
    for name, path in paths.items():
        payload = get(judge_dir / path)
        assert payload["n"] == 300 and payload["invalid"] == 0
        flags[name] = {k: int(v["p_yes"] > 0.5) for k, v in payload["items"].items()}
        assert set(flags[name]) == {r["id"] for r in wjb_rows}
    wjb_sets = {"all": wjb_rows, "baseline_success": [r for r in wjb_rows if flags["alpha0"][r["id"]]],
                "baseline_nonsuccess": [r for r in wjb_rows if not flags["alpha0"][r["id"]]]}
    out_wjb = {}
    for name, subset in wjb_sets.items():
        out_wjb[name] = {k: summarize(subset, x.get) for k, x in flags.items()}
        out_wjb[name]["learned_minus_random"] = summarize(
            subset,
            lambda i: np.mean([flags[f"old_s{s}"][i] for s in range(3, 8)]) -
            np.mean([flags[f"rand{s}"][i] for s in range(4)]),
        )

    wjb_pairs = get(ROOT / "configs/stage0_data/wjb_benign246_pairs300.json")
    pairs = [{"id": r["id"], "group": grouped_key(r["vanilla"])} for r in wjb_pairs]
    base = {key: new_rule(row["text"]) for key, row in texts("WJB_BENIGN246_alpha0.json").items()}
    assert len(base) == 600
    def eligible(row):
        return not any(base[f"{row['id']}|{side}"] for side in ("vanilla", "adversarial"))
    pair_sets = {"all": pairs, "neither_baseline_refusal": [r for r in pairs if eligible(r)],
                 "either_baseline_refusal": [r for r in pairs if not eligible(r)]}
    out_pairs = {}
    for name in ("alpha0", "old_s0", "old_s3", "old_s4", "old_s5", "old_s6", "old_s7", "rand0", "rand1"):
        label = {key: new_rule(row["text"]) for key, row in texts(f"WJB_BENIGN246_{name}.json").items()}
        assert set(label) == set(base)
        def dd(i):
            a, v = f"{i}|adversarial", f"{i}|vanilla"
            return int(label[a]) - int(base[a]) - int(label[v]) + int(base[v])
        out_pairs[name] = {}
        for key, subset in pair_sets.items():
            out_pairs[name][key] = {
                "vanilla_refusal": summarize(subset, lambda i: int(label[f"{i}|vanilla"])),
                "wrapped_refusal": summarize(subset, lambda i: int(label[f"{i}|adversarial"])),
                "difference_in_differences": summarize(subset, dd),
            }
    return {"legal400": out_legal, "wjb_harmful300": out_wjb, "wjb_benign300_pairs": out_pairs,
            "source_sha256": source_hashes, "seed": BOOT_SEED, "bootstrap_replicates": BOOT_REPS}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("historical", "pair500"))
    p.add_argument("--conditions", type=Path, help="Mapping from condition to row ID to ASR label or null")
    a = p.parse_args()
    if a.mode == "historical":
        write(OUT / "existing_evaluation_stratified.json", existing_report())
    else:
        if a.conditions is None:
            p.error("--conditions is required for pair500")
        write(OUT / "pair500_clustered_report.json", attack_report(load(a.conditions)))


if __name__ == "__main__":
    main()
