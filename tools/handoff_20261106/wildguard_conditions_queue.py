"""Follow the frozen order, after the saved conversational baseline read."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/data/HZX/Def');sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
from public_wjb_alpha0_gate import rows,PLAN
from judge.refusal import new_rule

BASE=ROOT/'results/audit/pair500';OUT=BASE/'wildguard';NODE='/home/dell/Def/results/audit/pair500/wildguard'
NAMES=['old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');os.replace(tmp,path)


def pulse(phase,name=None):
    save(OUT/'conditions_queue_live.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'phase':phase,'condition':name})


def main():
    os.umask(0o077)
    while not (OUT/'baseline_read/refusal_agreement.json').exists():pulse('waiting_baseline_conversational_read');time.sleep(15)
    mapping=json.loads((BASE/'wjb_mapping255.json').read_text())['rows'];prompts=rows(json.loads(PLAN.read_text()))
    assert len(mapping)==2000
    subprocess.run(['scp',str(ROOT/'tools/handoff_20261106/wildguard_conditions_run.py'),'node01:/home/dell/Def/tools/handoff_20261106/wildguard_conditions_run.py'],check=True)
    for name in NAMES:
        source=BASE/'public255/harmful.private'/name/'wildjailbreak_harmful'
        while len(list(source.glob('*.json')))!=2000:pulse('waiting_complete_target_outputs',name);time.sleep(30)
        payload=[];hashes={}
        for row in mapping:
            p=source/(row['id']+'.json');raw=p.read_bytes();x=json.loads(raw);text=x['items'][0]['text']
            hashes[row['id']]=hashlib.sha256(raw).hexdigest()
            payload.append({'id':row['id'],'prompt':prompts[row['id']],'response':text,'v2':new_rule(text),'low_confidence':row['low_similarity'] or row['low_margin'],'historical_used':row['historical_group_used']})
        private=OUT/(name+'_inputs.private.json');save(private,payload)
        save(OUT/(name+'_input_manifest.json'),{'n':2000,'input_sha256':hashlib.sha256(private.read_bytes()).hexdigest(),'generation_hashes':hashes,'classifier_source_sha256':hashlib.sha256((ROOT/'tools/handoff_20261106/wildguard_conditions_run.py').read_bytes()).hexdigest()})
        subprocess.run(['scp',str(private),'node01:'+NODE+'/'+private.name],check=True)
        pulse('remote_gpu0_job_dispatched',name)
        shell=f'''set -euo pipefail
cd /home/dell/Def
source tools/handoff_20261106/node01_launch_round9.sh
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu0.lock
flock 8
until wait_gpu cuda:0; do sleep 15; done
DEVICE=cuda:0 launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 /data/ray/env/bin/python -u tools/handoff_20261106/wildguard_conditions_run.py {name}
'''
        with (ROOT/'logs/wildguard_conditions_queue.log').open('ab',buffering=0) as log:
            subprocess.run(['ssh','node01','bash','-s'],input=shell.encode(),stdout=log,stderr=subprocess.STDOUT,check=True)
        pulse('copying_completed_scores',name)
        subprocess.run(['rsync','-a','node01:'+NODE+'/'+name+'_scores/',str(OUT/(name+'_scores'))+'/'],check=True)
        for suffix in ['_summary.json','_done.json','_live.json']:
            subprocess.run(['scp','node01:'+NODE+'/'+name+suffix,str(OUT/(name+suffix))],check=True)
        with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} WILDGUARD_UNIT_COMPLETED {name} n2000, no conversational unit-effect read; source manifest retained.\n')
    pulse('all_units_complete_no_effect_read')


if __name__=='__main__':main()
