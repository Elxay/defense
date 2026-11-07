"""Build frozen row manifests and audit labels without dropping evaluation rows."""
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/audit/pair500"
STAGE = ROOT / "configs/stage0_data"
HB = ROOT / "repos/HarmBench"
HB_CSV = HB / "data/behavior_datasets/harmbench_behaviors_text_all.csv"
JBB_CSV = Path("/data/huggingface/hub/datasets--JailbreakBench--JBB-Behaviors/snapshots/886acc352a31533ffbcf4ef22c744658688086fc/data/harmful-behaviors.csv")
SEED = 20261107
sys.path.insert(0, str(ROOT / "src"))
from judge.refusal import new_rule


def load(path):
    return json.loads(path.read_text())


def write(name, value):
    path = OUT / name
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temp.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text):
    text = unicodedata.normalize("NFKC", text).lower()
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def jbb_id(attack_id):
    return f"jbb_{int(attack_id.rsplit('_', 1)[-1]):03d}"


def source_rows():
    targets = load(HB / "data/optimizer_targets/harmbench_targets_text.json")
    rows = {}
    with HB_CSV.open(newline="") as file:
        for row in csv.DictReader(file):
            identifier = row["BehaviorID"]
            layer = row["FunctionalCategory"]
            assert (layer == "contextual") == bool(row["ContextString"])
            key = f"hb_{identifier}"
            rows[key] = {
                "id": key, "dataset": "HarmBench", "layer": layer,
                "behavior": row["Behavior"], "context": row["ContextString"],
                "target": targets[identifier], "hb_row": row,
            }
    with JBB_CSV.open(newline="") as file:
        for i, row in enumerate(csv.DictReader(file)):
            key = f"jbb_{i:03d}"
            rows[key] = {
                "id": key, "dataset": "JBB", "layer": "jbb",
                "behavior": row["Goal"], "context": "", "target": row["Target"],
            }
    assert Counter(row["layer"] for row in rows.values()) == {
        "standard": 200, "contextual": 100, "copyright": 100, "jbb": 100,
    }
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = source_rows()
    groups = load(STAGE / "behavior_groups.json")["groups"]
    by_id = {}
    by_text = defaultdict(set)
    group_data = {}
    for group in groups:
        canonical = group["canonical"]
        group_data[canonical] = group
        for identifier, text in zip(group["members"], group["texts"], strict=True):
            assert identifier not in by_id
            assert normalize(rows[identifier]["behavior"]) == normalize(text)
            by_id[identifier] = canonical
            by_text[normalize(text)].add(identifier)
    assert set(rows) == set(by_id) and len(group_data) == 479

    acts_path = ROOT / "results/probes/llama31_8b_instruct/acts_attack2.pt"
    meta = torch.load(acts_path, map_location="cpu", weights_only=True)["meta"]
    legacy_attacks = [row["id"] for row in meta if row["id"].split("_")[0] in {"pair", "tap"}]
    legacy_raw_ids = sorted({value.split("_", 2)[2] for value in legacy_attacks})
    dev_pool = set(legacy_raw_ids[24:])
    dev22 = [value for value in legacy_attacks if value.split("_", 2)[2] in dev_pool][:22]
    legacy46 = [row["id"] for row in load(ROOT / "configs/stage0_split.json")["train"]]
    strat = load(STAGE / "b8_train_strat.json")["items"]
    strat_ids = set()
    strat_groups = set()
    for item in strat:
        matched = set().union(*(by_text[normalize(text)] for text in item["texts"]))
        group_ids = {by_id[key] for key in matched}
        assert len(group_ids) == 1
        strat_groups.update(group_ids)
        strat_ids.update(matched)
    assert len(strat_groups) == len(strat) == 97

    flags = {
        "fit12": {jbb_id(row["id"]) for row in load(STAGE / "attacks_fit12.json")},
        "legacy46": set(legacy46),
        "dev22": {jbb_id(key) for key in dev22},
        "val70": set(load(STAGE / "val70_ids.json")["ids"]),
        "train_strat97": strat_ids,
        "legacy_additional": {jbb_id(key) for key in legacy_raw_ids} - set(legacy46),
    }
    assert [len(flags[k]) for k in ("fit12", "legacy46", "dev22", "val70")] == [12, 46, 22, 70]
    assert set().union(*flags.values()) <= set(rows)
    group_flags = {name: {by_id[key] for key in keys} for name, keys in flags.items()}
    flag_records = []
    for key in sorted(rows):
        group = by_id[key]
        direct = [name for name, keys in flags.items() if key in keys]
        inherited = [name for name, ids in group_flags.items() if group in ids]
        used = group_data[group]["used"]
        item = {
            "id": key, "group": group, "dataset": rows[key]["dataset"],
            "layer": rows[key]["layer"], "direct_flags": direct, "group_flags": inherited,
            "historical_group_used": used, "untouched": not (inherited or used),
        }
        flag_records.append(item)
        rows[key].update(item)

    strata = ["standard", "contextual", "copyright", "jbb"]
    order = sorted(rows, key=lambda key: hashlib.sha256(f"{SEED}:{key}".encode()).digest())
    pilot_quota = {"standard": 4, "contextual": 2, "copyright": 2, "jbb": 2}
    pilot_set = set()
    for layer, quota in pilot_quota.items():
        pilot_set.update([key for key in order if rows[key]["layer"] == layer][:quota])
    pilot = [key for key in order if key in pilot_set]
    order = pilot + [key for key in order if key not in pilot_set]

    layers = {}
    for layer in strata:
        subset = [x for x in flag_records if x["layer"] == layer]
        layers[layer] = {
            "rows": len(subset), "groups": len({x["group"] for x in subset}),
            "untouched_rows": sum(x["untouched"] for x in subset),
            "untouched_groups": len({x["group"] for x in subset if x["untouched"]}),
        }
    cross = [g["members"] for g in groups if len({rows[k]["dataset"] for k in g["members"]}) > 1]
    copyright_keys = {rows[k]["hb_row"]["BehaviorID"] for k in rows if rows[k]["layer"] == "copyright"}
    hash_files = {p.stem: p for p in (HB / "data/copyright_classifier_hashes").glob("*.pkl")}
    assert copyright_keys == set(hash_files)
    hash_manifest = {key: digest(hash_files[key]) for key in sorted(hash_files)}
    write("copyright_hash_manifest.json", hash_manifest)
    counts = {
        "total_rows": len(rows), "total_groups": len(groups), "layers": layers,
        "cross_dataset_groups": cross,
        "group_sizes": dict(Counter(len(g["members"]) for g in groups)),
        "historical_used_groups": sum(g["used"] for g in groups),
        "untouched_rows": sum(x["untouched"] for x in flag_records),
        "untouched_groups": len({x["group"] for x in flag_records if x["untouched"]}),
        "flag_counts": {k: {"direct_rows": len(flags[k]), "groups": len(group_flags[k]),
                            "including_group_mates_rows": sum(by_id[x] in group_flags[k] for x in rows)}
                        for k in flags},
    }
    sources = [HB_CSV, JBB_CSV, STAGE / "behavior_groups.json", STAGE / "attacks_fit12.json",
               STAGE / "b8_train_strat.json", STAGE / "val70_ids.json", acts_path,
               ROOT / "configs/stage0_split.json", ROOT / "src/eval/legacy33.py"]
    write("row_audit.json", {
        "counts": counts, "flags": flag_records, "seed": SEED, "pilot": pilot, "order": order,
        "source_sha256": {str(p): digest(p) for p in sources},
        "flag_direct_ids": {k: sorted(v) for k, v in flags.items()},
    })
    write("rows.private.json", [rows[key] for key in order])

    legal = load(ROOT / "data/legal_val_items.json")
    baseline = load(ROOT / "results/audit/LEGALVALB_none.json")
    assert {r["key"] for r in legal} == set(baseline) and len(legal) == 400
    legal_marks = [{"id": row["key"], "layer": row["group"],
                    "baseline_refusal_v2": new_rule(baseline[row["key"]]["text"])}
                   for row in legal]
    wjb = load(STAGE / "wjb300.json")
    judge = load(ROOT / "results/hfjudge/JUDGE_HF_wjb_a0_innet_round2")["items"]
    assert {row["id"] for row in wjb} == set(judge) and len(wjb) == 300
    wjb_marks = [{"id": row["id"], "baseline_judge_success": judge[row["id"]]["p_yes"] > .5}
                 for row in wjb]
    pairs = load(STAGE / "wjb_benign246_pairs300.json")
    baseline_pairs = load(ROOT / "results/audit/WJB_BENIGN246_alpha0.json")["items"]
    pair_marks = []
    for pair in pairs:
        sides = {side: new_rule(baseline_pairs[f"{pair['id']}|{side}"]["text"])
                 for side in ("vanilla", "adversarial")}
        for side, refused in sides.items():
            pair_marks.append({"id": f"{pair['id']}|{side}", "group": pair["id"], "side": side,
                               "baseline_refusal_v2": refused, "either_baseline_refusal_v2": any(sides.values())})
    assert len(pair_marks) == len(baseline_pairs) == 600
    write("existing_evaluation_flags.json", {
        "legal400": legal_marks, "wjb_harmful300": wjb_marks, "wjb_benign600": pair_marks,
        "scope": "Rows are retained. Baseline statuses describe historical outcomes. Existing primary read gates apply to generated treatments.",
    })
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
