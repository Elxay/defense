"""One requested morning snapshot of operational metadata, without labels."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/data/HZX/Def')
BASE=ROOT/'results/audit/pair500'
DUE=datetime.datetime(2026,11,8,23,tzinfo=datetime.timezone.utc)


def main():
    dest=BASE/'morning_20261109_0800_status.json'
    if dest.exists():return
    while datetime.datetime.now(datetime.timezone.utc)<DUE:
        p=BASE/'morning_0800_capture_live.json';t=p.with_suffix('.tmp')
        t.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'phase':'waiting_0800_JST','due_utc':DUE.isoformat()},indent=2)+'\n');t.replace(p)
        time.sleep(30)
    sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
    from wjb_morning_read import status
    from wjb_nine_read_gate import status as gate
    source=status()
    remote="""from pathlib import Path
import json,datetime
base=Path('/home/dell/Def/results/audit/pair500');now=datetime.datetime.now(datetime.timezone.utc);out=[]
for folder in ['wildguard','wildguard_public','wildguard_pair254']:
 for p in (base/folder).glob('*_live.json'):
  x=json.loads(p.read_text());pid=x.get('pid')
  if pid and Path('/proc',str(pid)).exists():out.append({'group':folder,'file':p.name,'metadata':x,'heartbeat_age_s':(now-datetime.datetime.fromisoformat(x['utc'])).total_seconds()})
print(json.dumps(out))
"""
    peers=json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=remote,text=True))
    x={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requested_jst':'2026-11-09T08:00:00+09:00',
       'pair':[r for r in source['rows'] if r['name']=='node01 PAIR worker'],
       'recent10':source['recent_search_rows'],'pair_recovery':source['recovery'],
       'active_wjb_workers':[r for r in source['wjb_workers'] if r['alive']],
       'generation_counts':{name:len(list((BASE/'public255/harmful.private'/name/'wildjailbreak_harmful').glob('*.json'))) for name in ['old_s7','old_s0','SYS_A','SYS_B']},
       'joint_gate':gate(),'node01_active_classifier_workers':peers,'effects_read':False}
    for key,relative in [('external_gpu3','gpu3_external_30m.jsonl'),('public_wg_queue','wildguard_public/queue_live.json'),('harmful_wg_queue','wildguard/conditions_queue_live.json'),('hb_window','public255/judge_window_live.json'),('judge_wait','hb_delay_wait_live.json')]:
        p=BASE/relative
        if p.exists():x[key]=json.loads(p.read_text().splitlines()[-1]) if p.suffix=='.jsonl' else json.loads(p.read_text())
    temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');temp.replace(dest)
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{x["utc"]} REQUESTED_0800JST_STATUS_CAPTURED SHA={hashlib.sha256(dest.read_bytes()).hexdigest()} progress/timing only; no outcome labels loaded.\n')


if __name__=='__main__':main()
