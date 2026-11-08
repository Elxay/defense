"""Read coverage metadata only; final WJB effects need HB and WG all nine."""
import argparse
import datetime
import json
from pathlib import Path

BASE = Path('/data/HZX/Def/results/audit/pair500')
NAMES = ['old_s3', 'rand0', 'old_s4', 'rand1', 'old_s5', 'rand2', 'old_s6', 'rand3', 'old_s7']


def status():
    keys = {str(r['id']) for r in json.loads((BASE / 'wjb_mapping255.json').read_text())['rows']}
    assert len(keys) == 2000
    rows = {}
    for name in NAMES:
        hb = BASE / 'public255/mapped_scores' / name
        wg = BASE / 'wildguard' / (name + '_scores')
        hids = {p.stem for p in hb.glob('*.json')}
        wids = {p.stem for p in wg.glob('*.json')}
        assert hids <= keys and wids <= keys
        rows[name] = {'hb_top1': len(hids), 'wg': len(wids),
                      'wg_done_manifest': (BASE / 'wildguard' / (name + '_done.json')).exists()}
    ready = all(x['hb_top1'] == 2000 and x['wg'] == 2000 and x['wg_done_manifest'] for x in rows.values())
    return {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'all_nine_both_judges_ready': ready, 'units': rows, 'labels_loaded': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--require-ready', action='store_true')
    a = p.parse_args()
    x = status(); print(json.dumps(x, indent=2))
    if a.require_ready and not x['all_nine_both_judges_ready']:
        raise SystemExit(75)
