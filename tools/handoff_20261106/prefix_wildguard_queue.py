"""Pre-score immutable target rows; never aggregate their outcome labels."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';PREFIX=BASE/'prefix254';REMOTE='/home/dell/Def'
NAMES=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,p)
def pulse(phase,**kw):save(BASE/'prefix_wildguard_live.json',{'utc':utc(),'pid':os.getpid(),'phase':phase,**kw})


def main():
    pub=load(BASE/'prefix254_dual_publication.json')
    for name,value in pub['code_sha256'].items():assert sha(ROOT/name)==value,name
    order=load(BASE/'row_audit.json')['order'];rows={r['id']:r for r in load(BASE/'rows.private.json')};cursor=0
    while not(BASE/'frozen_prompt_snapshot.json').exists():
        selected=None
        for _ in NAMES:
            name=NAMES[cursor%len(NAMES)];cursor+=1;indexpath=PREFIX/'wg_pre_index'/(name+'.json');index=load(indexpath) if indexpath.exists() else {}
            pending=[k for k in order if (PREFIX/'generation.private'/name/(k+'.json')).exists() and k not in index]
            if pending:selected=(name,pending[:200],index,indexpath);break
        if selected is None:pulse('waiting_target_rows');time.sleep(15);continue
        name,keys,index,indexpath=selected;payload=[];provenance={}
        for key in keys:
            p=PREFIX/'generation.private'/name/(key+'.json');g=load(p);native=load(BASE/'generations.private'/(key+'.json'));prompt=native['best']['prompt'];response=g['result']['text']
            prompt_sha=hashlib.sha256(prompt.encode()).hexdigest();assert prompt_sha==g['signature']['prompt_sha256']
            payload.append({'id':key,'prompt':prompt,'response':response,'layer':rows[key]['layer']})
            provenance[key]={'generation_sha256':sha(p),'prompt_sha256':prompt_sha,'response_sha256':hashlib.sha256(response.encode()).hexdigest()}
        content=json.dumps(payload,ensure_ascii=False,indent=2)+'\n';ih=hashlib.sha256(content.encode()).hexdigest();batch=BASE/'prefix_wg_batches'/name/ih
        batch.mkdir(parents=True,exist_ok=True);inputpath=batch/(name+'_inputs.private.json')
        if inputpath.exists():assert sha(inputpath)==ih
        else:inputpath.write_text(content)
        meta={'utc':utc(),'condition':name,'n':len(keys),'input_sha256':ih,'provenance':provenance,'read_lock':'no outcome reads before final search/all rows/both judges','source_sha256':pub['pair_wildguard_source_sha256']}
        if (batch/'manifest.json').exists():
            previous=load(batch/'manifest.json')
            assert all(previous[k]==meta[k] for k in ['condition','n','input_sha256','provenance','source_sha256'])
        else:save(batch/'manifest.json',meta)
        relative=str(batch.relative_to(ROOT));subprocess.run(['rsync','-aR',str(inputpath.relative_to(ROOT)),str((batch/'manifest.json').relative_to(ROOT)),'node01:'+REMOTE+'/'],cwd=ROOT,check=True)
        shell=f'''set -euo pipefail
cd {REMOTE}
source tools/handoff_20261106/node01_launch_round9.sh
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu0.lock
flock 8
until wait_gpu cuda:0; do sleep 15; done
DEVICE=cuda:0 launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 /data/ray/env/bin/python -u tools/handoff_20261106/prefix_wg_batch_runner.py --batch {relative}
'''
        with (ROOT/'logs/prefix_wildguard.log').open('ab',buffering=0) as log:
            proc=subprocess.Popen(['ssh','node01','bash','-s'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT);proc.stdin.write(shell.encode());proc.stdin.close()
            while proc.poll() is None:pulse('scoring_no_effect_read',condition=name,batch_n=len(keys),batch_sha256=ih);time.sleep(15)
            assert proc.returncode==0,'prefix WG batch failed'
        scores=batch/(name+'_scores');subprocess.run(['rsync','-a','node01:'+REMOTE+'/'+relative+'/'+name+'_scores/',str(scores)+'/'],check=True)
        for key in keys:
            p=scores/(key+'.json');record=load(p);assert record['id']==key and record['signature']['input_sha256']==ih
            assert record['signature']['runtime_source_sha256']==pub['pair_wildguard_source_sha256']
            index[key]={**provenance[key],'score_file':str(p.relative_to(ROOT)),'score_file_sha256':sha(p),'batch_manifest_sha256':sha(batch/'manifest.json')}
        save(indexpath,index);pulse('batch_complete_no_effect_read',condition=name,batch_n=len(keys),condition_cached=len(index))
    save(BASE/'prefix_wg_drained.json',{'utc':utc(),'phase':'search_closed_no_new_batches','labels_aggregated':False});pulse('drained_for_final_queue')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        pulse('failed',error_type=type(exc).__name__,error=str(exc));save(BASE/'prefix_wg_drained.json',{'utc':utc(),'phase':'optional_prescore_failed','gaps_require_original_classifier':True});raise
