"""Run the unchanged frozen PAIR WildGuard classifier on an immutable batch."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path('/home/dell/Def');BASE=ROOT/'results/audit/pair500'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);a=p.parse_args()
    batch=ROOT/a.batch;meta=json.loads((batch/'manifest.json').read_text());pub=json.loads((BASE/'prefix254_dual_publication.json').read_text())
    for name,value in pub['code_sha256'].items():assert sha(ROOT/name)==value,name
    source=ROOT/'tools/handoff_20261106/pair500_wildguard_run.py';assert sha(source)==pub['pair_wildguard_source_sha256']
    assert sha(batch/(meta['condition']+'_inputs.private.json'))==meta['input_sha256']
    sys.argv=[str(source),meta['condition']]
    scope={'__name__':'frozen_prefix_classifier','__file__':str(source)}
    exec(compile(source.read_text(),str(source),'exec'),scope)
    scope['OUT']=batch
    scope['main']()


if __name__=='__main__':main()
