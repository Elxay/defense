"""Operational completeness checks only: never load a condition label."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path('/data/HZX/Def')
BASE = ROOT / 'results/audit/pair500'
NINE = ['old_s3', 'rand0', 'old_s4', 'rand1', 'old_s5', 'rand2', 'old_s6', 'rand3', 'old_s7']


def status():
    snapshot = BASE / 'frozen_prompt_snapshot.json'
    ids = [r['id'] for r in json.loads(snapshot.read_text())['rows']] if snapshot.exists() else []
    def coverage(folder):
        return sum((folder / (key + '.json')).is_file() for key in ids)
    result = {
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'snapshot_ready': bool(ids), 'n': len(ids),
        'counts': {name: {
            'harmbench': coverage(BASE / 'canonical254/scores' / name),
            'wildguard': coverage(BASE / 'wildguard_pair254' / (name + '_scores')),
        } for name in NINE},
        'no_labels_loaded': True,
    }
    result['both_judges_all_nine_ready'] = bool(ids) and all(
        count == len(ids) for row in result['counts'].values() for count in row.values())
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--status', action='store_true')
    p.add_argument('--prepare-baseline', action='store_true')
    args = p.parse_args()
    x = status()
    if args.prepare_baseline:
        snapshot = BASE / 'frozen_prompt_snapshot.json'
        ids = [r['id'] for r in json.loads(snapshot.read_text())['rows']]
        assert ids and all((BASE / 'canonical254/scores/alpha0' / (k + '.json')).exists() for k in ids)
        assert json.loads((BASE / 'canonical254/judge20_gate.json').read_text())['passed']
        gate = BASE / 'canonical254/alpha0_gate.json'
        gate.write_text(json.dumps({'utc': x['utc'], 'snapshot_sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
            'rule': 'Coverage only, no labels read; defer dynamic-range interpretation until both-judge nine-unit read.'}, indent=2) + '\n')
    text = json.dumps(x, indent=2) + '\n'
    dest = BASE / 'canonical254/two_judge_readiness.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.with_suffix('.tmp').write_text(text)
    dest.with_suffix('.tmp').replace(dest)
    with (ROOT / 'docs/PREREG_LOG.txt').open('a') as f:
        f.write(f"{x['utc']} PAIR254_STATUS_ONLY SHA={hashlib.sha256(text.encode()).hexdigest()} ready={x['both_judges_all_nine_ready']} no condition labels read.\n")
    print(text, end='')
