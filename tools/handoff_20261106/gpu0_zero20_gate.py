"""Replay the fixed first twenty prompts on GPU0; compare bytes, never labels."""
from pathlib import Path
import datetime
import hashlib
import json
import sys
import subprocess

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';PREFIX=BASE/'prefix254'
sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
from prefix_support import load,save,sha,objsha,utc,RUNTIME
from borrowed_gpu_support import verify_extension

def main():
    verify_extension();keys=load(BASE/'row_audit.json')['order'][:20];items=[];references={}
    for key in keys:
        reference=PREFIX/'generation.private/alpha0'/(key+'.json');g=load(reference);n=load(BASE/'generations.private'/(key+'.json'))
        item={'id':key,'prompt':n['best']['prompt'],'prompt_sha256':hashlib.sha256(n['best']['prompt'].encode()).hexdigest(),'row_sha256':g['signature']['row_sha256']}
        assert item['prompt_sha256']==g['signature']['prompt_sha256'];items.append(item);references[key]=sha(reference)
    task={'condition':'alpha0','runtime_sha256':sha(RUNTIME),'gate':True,'gate_output':'gpu0_zero20.private','items':items,'reference_sha256':references}
    p=PREFIX/'tasks.private/gpu0_zero20.json';save(p,task)
    shell=f'''set -euo pipefail
cd {ROOT}
source night/launch.sh
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu0.lock
flock 8
until wait_gpu cuda:0; do sleep 15; done
DEVICE=cuda:0 launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 /home/kemove/anaconda3/envs/HZX_GLA/bin/python -u tools/handoff_20261106/prefix_generate_borrowed.py --task {p.relative_to(ROOT)}
'''
    started=utc()
    with (ROOT/'logs/gpu0_zero20_gate.log').open('ab',buffering=0) as log:
        result=subprocess.run(['bash','-s'],input=shell.encode(),stdout=log,stderr=subprocess.STDOUT)
    comparisons=[]
    if result.returncode==0:
        for key in keys:
            oldpath=PREFIX/'generation.private/alpha0'/(key+'.json');newpath=PREFIX/'gpu0_zero20.private/alpha0'/(key+'.json');old=load(oldpath);new=load(newpath)
            assert sha(oldpath)==references[key]
            comparisons.append({'id':key,'byte_equal':old['result']['text'].encode()==new['result']['text'].encode(),'input_ids_equal':old['result']['input_ids_sha256']==new['result']['input_ids_sha256'],'injection_count':new['result']['injection_count'],'rho_runtime':new['result']['rho_runtime'],'device_uuid':new['result']['device_uuid'],'old_sha256':references[key],'new_sha256':sha(newpath)})
    passed=result.returncode==0 and len(comparisons)==20 and all(x['byte_equal'] and x['input_ids_equal'] and x['injection_count']==1 and x['rho_runtime']==0 for x in comparisons)
    record={'started_utc':started,'completed_utc':utc(),'task_sha256':sha(p),'exit_code':result.returncode,'passed':passed,'byte_equal':sum(x['byte_equal'] for x in comparisons),'n':len(comparisons),'comparisons':comparisons,'outcome_labels_read':False}
    save(BASE/'gpu0_zero20_result.json',record)
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{utc()} GPU0_ZERO20_COMPLETE passed={passed} bytes={record["byte_equal"]}/{record["n"]} sha256={sha(BASE/"gpu0_zero20_result.json")} no labels read; failed gate leaves GPU0 disabled.\n')
    print(json.dumps({k:record[k] for k in ['started_utc','completed_utc','passed','byte_equal','n','exit_code']}))

if __name__=='__main__':main()
