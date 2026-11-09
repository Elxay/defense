"""One real row-boundary reclaim check of our borrowed worker only."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import time

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';PREFIX=BASE/'prefix254'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
    active=[]
    for p in (PREFIX/'live').glob('*.json'):
        x=json.loads(p.read_text())
        if x.get('device')=='cuda:0' and Path('/proc',str(x['pid'])).exists() and x.get('phase')=='generation':active.append((p,x))
    assert len(active)==1;live,x=active[0];pid=x['pid'];assert 'prefix_generate_borrowed.py' in Path('/proc',str(pid),'cmdline').read_bytes().decode()
    before={str(p.relative_to(ROOT)):sha(p) for p in (PREFIX/'generation.private'/x['condition']).glob('*.json')};flag=BASE/'gpu0_reclaim.flag';marker='controlled row-boundary release test '+utc()
    with flag.open('x') as f:f.write(marker+'\n')
    start=utc();limit=time.monotonic()+180
    while Path('/proc',str(pid)).exists() and time.monotonic()<limit:time.sleep(1)
    assert not Path('/proc',str(pid)).exists(),'worker did not release within180s; leave reclaim flag set'
    after={str(p.relative_to(ROOT)):sha(p) for p in (PREFIX/'generation.private'/x['condition']).glob('*.json')};assert all(after.get(k)==v for k,v in before.items())
    assert len(after)-len(before)<=1
    end=json.loads(live.read_text());assert end['phase']=='borrowed_gpu0_yield'
    result={'request_utc':start,'released_utc':utc(),'worker_pid':pid,'condition':x['condition'],'previous_rows_unchanged':len(before),'rows_added_before_release':len(after)-len(before),'worker_phase':end['phase'],'passed':True,'scope':'only our registered borrowed GPU0 worker; no PAIR restart or external process signal','live_sha256':sha(live)}
    assert flag.read_text()==marker+'\n';flag.unlink();result['own_test_flag_removed_utc']=utc()
    p=BASE/'gpu0_cooperative_release_check.json';p.write_text(json.dumps(result,indent=2)+'\n')
    with (ROOT/'docs/OPS_LOG.txt').open('a') as f:f.write(f'{utc()} GPU0_ROW_BOUNDARY_RECLAIM_TEST passed worker={pid} previousfiles={len(before)} maxone_newrow={result["rows_added_before_release"]}; our test flag removed for resume. PAIR restart count unchanged1; no external process touched. SHA={sha(p)}\n')
    print(json.dumps(result))

if __name__=='__main__':main()
