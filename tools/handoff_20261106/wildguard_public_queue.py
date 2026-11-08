"""Public sensitivity only, after the entire WJB WildGuard condition queue."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/data/HZX/Def');sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
from wjb_eval255_run import public_rows
from wjb_eval255_report import normalize
from judge.refusal import new_rule

BASE=ROOT/'results/audit/pair500';OUT=BASE/'wildguard_public';NODE='/home/dell/Def/results/audit/pair500/wildguard_public'
NAMES=['alpha0','old_s3','old_s4','old_s5','old_s6','old_s7','rand0','rand1','rand2','rand3']


def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2)+'\n');os.replace(t,p)


def pulse(phase,name=None):
    save(OUT/'queue_live.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'phase':phase,'condition':name})


def main():
    os.umask(0o077)
    while True:
        gate=BASE/'wildguard/conditions_queue_live.json'
        if gate.exists() and json.loads(gate.read_text())['phase']=='all_units_complete_no_effect_read':break
        pulse('waiting_wjb_wildguard_all_conditions');time.sleep(30)
    source=public_rows();keep=json.loads((ROOT/'results/style_intervention/old_recipe_targets.json').read_text())['keep'];trained={normalize(x['text']) for x in keep}
    assert {k:len(v) for k,v in source.items()}=={'xstest_safe':250,'xstest_unsafe':200,'or_hard':1319,'wildjailbreak_benign':210}
    assert {k:sum(normalize(t) not in trained for _,t in source[k]) for k in ['xstest_safe','or_hard','wildjailbreak_benign']}=={'xstest_safe':238,'or_hard':1301,'wildjailbreak_benign':210}
    subprocess.run(['ssh','node01','mkdir','-p',NODE],check=True)
    subprocess.run(['scp',str(ROOT/'tools/handoff_20261106/wildguard_public_run.py'),'node01:/home/dell/Def/tools/handoff_20261106/wildguard_public_run.py'],check=True)
    for name in NAMES:
        payload=[];hashes={}
        for dataset,prompts in source.items():
            generated={}
            for p in (BASE/'public255/public.private'/name/dataset).glob('*.json'):
                raw=p.read_bytes();hashes[str(p.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
                for row in json.loads(raw)['items']:
                    assert row['id'] not in generated;generated[row['id']]=row
            assert set(generated)=={k for k,t in prompts}
            for key,prompt in prompts:
                row=generated[key];assert bool(new_rule(row['text']))==bool(row['v2_refusal'])
                safe_id=hashlib.sha256((dataset+'\0'+str(key)).encode()).hexdigest()
                payload.append({'id':safe_id,'original_id':key,'dataset':dataset,'keep60_unseen':normalize(prompt) not in trained,'prompt':prompt,'response':row['text'],'v2':row['v2_refusal']})
        assert len(payload)==1979
        p=OUT/(name+'_inputs.private.json');save(p,payload)
        save(OUT/(name+'_input_manifest.json'),{'n':1979,'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'generation_hashes':hashes,'runtime_source_sha256':hashlib.sha256((ROOT/'tools/handoff_20261106/wildguard_public_run.py').read_bytes()).hexdigest(),'primary_rule':'v2 unchanged; WildGuard sensitivity only'})
        subprocess.run(['scp',str(p),'node01:'+NODE+'/'+p.name],check=True);pulse('remote_gpu0_job_dispatched',name)
        shell=f'''set -euo pipefail
cd /home/dell/Def
source tools/handoff_20261106/node01_launch_round9.sh
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu0.lock
flock 8
until wait_gpu cuda:0; do sleep 15; done
DEVICE=cuda:0 launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 /data/ray/env/bin/python -u tools/handoff_20261106/wildguard_public_run.py {name}
'''
        with (ROOT/'logs/wildguard_public_queue.log').open('ab',buffering=0) as log:
            subprocess.run(['ssh','node01','bash','-s'],input=shell.encode(),stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run(['rsync','-a','node01:'+NODE+'/'+name+'_scores/',str(OUT/(name+'_scores'))+'/'],check=True)
        for suffix in ['_summary.json','_done.json','_live.json']:
            subprocess.run(['scp','node01:'+NODE+'/'+name+suffix,str(OUT/(name+suffix))],check=True)
        with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} PUBLIC_WILDGUARD_UNIT_COMPLETED {name} n1979; sensitivity only, final public outcomes unread until all ten complete.\n')
    pulse('all_ten_complete_no_effect_read')


if __name__=='__main__':main()
