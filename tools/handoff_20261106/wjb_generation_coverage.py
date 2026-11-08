"""Validate complete fixed-ID coverage, without reading responses or labels."""
import json
from pathlib import Path
import sys

BASE=Path('/data/HZX/Def/results/audit/pair500')
name,kind=sys.argv[1:]
assert name in ['old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']
keys={str(r['id']) for r in json.loads((BASE/'wjb_mapping255.json').read_text())['rows']}
folder=(BASE/'public255/harmful.private'/name/'wildjailbreak_harmful' if kind=='generation'
        else BASE/'public255/mapped_scores'/name)
assert kind in ['generation','score'] and len(keys)==2000
got={p.stem for p in folder.glob('*.json')}
assert got<=keys
if got!=keys:
    print(f'INCOMPLETE {name} {kind} {len(got)}/2000')
    raise SystemExit(75)
print(f'COMPLETE {name} {kind} 2000/2000')
