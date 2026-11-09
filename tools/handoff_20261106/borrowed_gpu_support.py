"""Borrowed-card protocol pins and cooperative release at row boundaries."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess

ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'results/audit/pair500'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_extension():
    x=json.loads((BASE/'gpu0_borrow_publication.json').read_text())
    assert x['old_prefix_publication_sha256']==sha(BASE/'prefix254_publication.json')
    assert x['runtime_sha256']==sha(BASE/'prefix254_runtime.json')
    for name,value in x['code_sha256'].items():assert sha(ROOT/name)==value,name

def gpu0_must_yield():
    if (BASE/'gpu0_reclaim.flag').exists():return True
    cfg=json.loads((BASE/'gpu0_borrow_publication.json').read_text())
    if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(cfg['borrow_until_utc']):return True
    # Do not touch external processes; yield if another compute context appears.
    text=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader,nounits'],text=True)
    uuid=subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader','-i','0'],text=True).strip()
    for line in text.splitlines():
        fields=[x.strip() for x in line.split(',')]
        if len(fields)==2 and fields[1]==uuid and int(fields[0])!=os.getpid():return True
    return False

def gpu0_enabled():
    p=BASE/'gpu0_zero20_result.json'
    if not p.exists() or not json.loads(p.read_text()).get('passed'):return False
    # Before launch this process is a dispatcher, so all other GPU0 contexts cause waiting.
    return not gpu0_must_yield()
