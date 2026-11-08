"""Frozen-prefix generation and portable post-search completion controller."""
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from prefix_support import ROOT,BASE,PREFIX,RUNTIME,load,save,sha,utc,objsha,verify_record,verify_code

NAMES=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']
PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python'
NPY='/data/ray/env/bin/python'
REMOTE='/home/dell/Def'


def pulse(phase,**kw):save(PREFIX/'controller_live.json',{'utc':utc(),'pid':os.getpid(),'phase':phase,**kw})


def beat():
    p=PREFIX/'controller_live.json'
    if p.exists():
        state=load(p);state['utc']=utc();save(p,state)


def sync_search():
    dest=BASE/'generations.private';dest.mkdir(exist_ok=True)
    subprocess.run(['rsync','-a','--ignore-existing','--include=*.json','--exclude=*','node01:'+REMOTE+'/results/audit/pair500/generations.private/',str(dest)+'/'],check=True,stdout=subprocess.DEVNULL)
    order=load(BASE/'row_audit.json')['order'];source_rows={r['id']:r for r in load(BASE/'rows.private.json')};items=[]
    for key in order:
        p=dest/(key+'.json')
        if not p.exists():break
        x=load(p);assert x['config_sha256']=='9e46b2e78bb191363b1dadbe458815871a00f8e9f91cea0202687ca70a83fca1' and x['id']==key
        items.append({'id':key,'prompt':x['best']['prompt'],'prompt_sha256':hashlib.sha256(x['best']['prompt'].encode()).hexdigest(),'row_sha256':objsha(source_rows[key]),'source_file_sha256':sha(p)})
    oldpath=PREFIX/'accepted_source_files.json';old=load(oldpath) if oldpath.exists() else {}
    current={x['id']:x['source_file_sha256'] for x in items}
    assert all(current.get(k)==v for k,v in old.items()),'Previously accepted search row changed'
    save(oldpath,current)
    return items


def task(name,items,gate=False):
    value={'condition':name,'runtime_sha256':sha(RUNTIME),'gate':gate,'items':items}
    if gate:value['reference_sha256']={i['id']:sha(PREFIX/'generation.private'/name/(i['id']+'.json')) for i in items}
    path=PREFIX/'tasks.private'/(name+'_'+objsha(value)[:20]+'.json');save(path,value);return path


def execute_gpu(arguments,device,node='innet',python=None,lease=True):
    python=python or (NPY if node=='node01' else PY)
    directory=REMOTE if node=='node01' else str(ROOT)
    launcher='tools/handoff_20261106/node01_launch_round9.sh' if node=='node01' else 'night/launch.sh'
    cards=device.split(',');locklines='\n'.join(f'exec {8-i}>>logs/idle_gpu{n}.lock\nflock {8-i}' for i,n in enumerate(cards)) if lease else ''
    waits=' && '.join('wait_gpu cuda:'+n for n in cards)
    script=f'''set -euo pipefail
cd {directory}
source {launcher}
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
{locklines}
until {waits}; do sleep 15; done
DEVICE=cuda:{cards[0]} launch_job env CUDA_VISIBLE_DEVICES={device} DEVICE=cuda:{cards[0]} {python} -u tools/handoff_20261106/{arguments}
'''
    cmd=['ssh','node01','bash','-s'] if node=='node01' else ['bash','-s']
    with (ROOT/'logs/prefix254_jobs.log').open('ab',buffering=0) as log:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT)
        proc.stdin.write(script.encode());proc.stdin.close()
        while proc.poll() is None:beat();time.sleep(15)
        return proc.returncode


def gen(name,items):
    from prefix_generate import yield_to_hb
    cfg=load(RUNTIME)
    while True:
        pending=[]
        for item in items:
            p=PREFIX/'generation.private'/name/(item['id']+'.json')
            if p.exists():verify_record(p,name,item,cfg)
            else:pending.append(item)
        if not pending:return
        while yield_to_hb():pulse('yielding_ready_hb_window');time.sleep(15)
        p=task(name,pending);pulse('early_generation',condition=name,n=len(pending),source_rows=len(items))
        code=execute_gpu('prefix_generate.py --task '+str(p.relative_to(ROOT)),'2')
        if code not in (0,75):raise RuntimeError('prefix generation failed '+name+' exit '+str(code))


def baseline50(items):
    path=PREFIX/'alpha0_first50_cross_node.json'
    if path.exists():return
    assert len(items)>=50
    rows=[]
    for item in items[:50]:
        native=load(BASE/'generations.private'/(item['id']+'.json'))['alpha0'];p=PREFIX/'generation.private/alpha0'/(item['id']+'.json')
        canonical=load(p)['result']['text'];rows.append({'id':item['id'],'byte_identical':native.encode()==canonical.encode(),
            'native_text_sha256':hashlib.sha256(native.encode()).hexdigest(),'canonical_text_sha256':hashlib.sha256(canonical.encode()).hexdigest()})
    # A diagnostic between search-native and helper paths, not an ASR or a
    # substitute for the per-condition identical-helper node gate.
    save(path,{'utc':utc(),'n':50,'identical':sum(x['byte_identical'] for x in rows),'rows':rows,'nonzero_labels_read':False,'role':'diagnostic; retain uniform helper baseline regardless of native-path differences'})
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{utc()} PREFIX_ALPHA0_NATIVE50_DIAGNOSTIC SHA={sha(path)} completed before nonzero generation; no harmfulness labels read.\n')


def early_allowed():
    return len(list((BASE/'public255/harmful.private/old_s7/wildjailbreak_harmful').glob('*.json')))==2000


def choose_route():
    path=PREFIX/'resource_route.json'
    if path.exists():return load(path)
    eligible=[];memory={}
    for n in [2,3]:
        used=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits','-i',str(n)],text=True).strip());memory[str(n)]=used
        with (ROOT/f'logs/idle_gpu{n}.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if used<=2000:eligible.append(n)
    result={'utc':utc(),'fallback':len(eligible)<2,'eligible':eligible,'memory_mib':memory,'existing_innet_rows_retained':True}
    save(path,result);return result


def materialize(items):
    snap=BASE/'frozen_prompt_snapshot.json'
    if not snap.exists():return
    snapshot=load(snap);index={x['id']:x for x in snapshot['rows']};cfg=load(RUNTIME)
    assert set(index)=={x['id'] for x in items}
    for item in items:
        assert index[item['id']]['prompt_sha256']==item['prompt_sha256'] and index[item['id']]['file_sha256']==item['source_file_sha256']
        for name in NAMES:
            p=PREFIX/'generation.private'/name/(item['id']+'.json')
            if not p.exists():continue
            x=verify_record(p,name,item,cfg);out=BASE/'canonical254/generation.private'/name/(item['id']+'.json')
            sig={'snapshot_sha256':sha(snap),'runtime_sha256':sha(RUNTIME),'prefix_generation_sha256':sha(p),'condition':name}
            if out.exists():assert load(out)['signature']==sig;continue
            save(out,{'id':item['id'],'signature':sig,'result':x['result'],'generation_node':x['generation_node'],'host':x['host'],'physical_gpu':x['physical_gpu'],'prefix_source':str(p.relative_to(ROOT))})
    correction=PREFIX/'final_snapshot_binding.json'
    if not correction.exists():
        save(correction,{'utc':utc(),'snapshot_sha256':sha(snap),'n':len(items),'prefix_sources_immutable':True})
        with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{utc()} PREFIX_FINAL_SNAPSHOT_BOUND SHA={sha(correction)}; supersedes old controller automatic wording before canonical generation: prefix generation was authorized earlier under its own immutable prompt signatures. Original line retained.\n')


def node_lanes(items,route):
    policy=load(BASE/'pair500_node_fallback_policy.json');placements=policy['fallback_target_placements'] if route['fallback'] else {n:'innet:2' for n in NAMES}
    if not route['fallback']:
        jobs={}
        for device in ['2','3']:
            commands=[]
            for i,name in enumerate(NAMES):
                if str(2+i%2)!=device:continue
                pending=[x for x in items if not(PREFIX/'generation.private'/name/(x['id']+'.json')).exists()]
                p=task(name,pending)
                commands.append(f'DEVICE=cuda:{device} launch_job env CUDA_VISIBLE_DEVICES={device} DEVICE=cuda:{device} {PY} -u tools/handoff_20261106/prefix_generate.py --task {p.relative_to(ROOT)}')
            shell=f'''set -euo pipefail
cd {ROOT}
source night/launch.sh
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu{device}.lock
flock 8
until wait_gpu cuda:{device}; do sleep 15; done
'''+ '\n'.join(commands)+'\n'
            log=(ROOT/'logs'/('prefix254_innet_lane'+device+'.log')).open('ab',buffering=0)
            proc=subprocess.Popen(['bash','-s'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT);proc.stdin.write(shell.encode());proc.stdin.close();jobs[device]=(proc,log)
        while jobs:
            beat()
            materialize(items)
            for device,(proc,log) in list(jobs.items()):
                code=proc.poll()
                if code is not None:
                    log.close();del jobs[device]
                    if code:raise RuntimeError('innet lane failed '+device+':'+str(code))
            if jobs:time.sleep(15)
        materialize(items);return
    nodes=[n for n in NAMES if placements[n].startswith('node01')]
    for name in nodes:gen(name,items[:20])
    scripts={}
    if nodes:
        subprocess.run(['rsync','-a',str(BASE/'frozen_prompt_snapshot.json'),'node01:'+REMOTE+'/results/audit/pair500/'],check=True)
        subprocess.run(['rsync','-a',str(PREFIX/'generation.private')+'/','node01:'+REMOTE+'/results/audit/pair500/prefix254/generation.private/'],check=True)
        for device in ['0','1','2']:
            commands=[]
            for name in nodes:
                if placements[name]!='node01:'+device:continue
                gate=task(name,items[:20],True)
                pending=[i for i in items if not(PREFIX/'generation.private'/name/(i['id']+'.json')).exists()]
                main=task(name,pending)
                for p in [gate,main]:subprocess.run(['rsync','-aR',str(p.relative_to(ROOT)),'node01:'+REMOTE+'/'],cwd=ROOT,check=True)
                commands += [f'DEVICE=cuda:{device} launch_job env CUDA_VISIBLE_DEVICES={device} DEVICE=cuda:{device} {NPY} -u tools/handoff_20261106/prefix_generate.py --task {gate.relative_to(ROOT)}',
                    f'NOGPU=1 DEVICE=cpu launch_job {NPY} tools/handoff_20261106/prefix_compare_gate.py --task {gate.relative_to(ROOT)}',
                    f'DEVICE=cuda:{device} launch_job env CUDA_VISIBLE_DEVICES={device} DEVICE=cuda:{device} {NPY} -u tools/handoff_20261106/prefix_generate.py --task {main.relative_to(ROOT)}']
            if not commands:continue
            shell=f'''set -euo pipefail
cd {REMOTE}
source tools/handoff_20261106/node01_launch_round9.sh
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu{device}.lock
flock 8
until wait_gpu cuda:{device}; do sleep 15; done
'''+ '\n'.join(commands)+'\n'
            log=(ROOT/'logs'/('prefix254_node_lane'+device+'.log')).open('ab',buffering=0)
            proc=subprocess.Popen(['ssh','node01','bash','-s'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT);proc.stdin.write(shell.encode());proc.stdin.close();scripts[device]=(proc,log)
    for name in NAMES:
        if placements[name]=='innet:2':gen(name,items);materialize(items)
    while scripts:
        subprocess.run(['rsync','-a','--ignore-existing','--include=*/','--include=*.json','--exclude=*','node01:'+REMOTE+'/results/audit/pair500/prefix254/generation.private/',str(PREFIX/'generation.private')+'/'],check=True)
        materialize(items)
        for device,(proc,log) in list(scripts.items()):
            code=proc.poll()
            if code is not None:
                log.close();del scripts[device]
                if code:raise RuntimeError('node lane '+device+' stopped at a gate or failed: '+str(code))
                if device=='0':save(PREFIX/'node_lane0_complete.json',{'utc':utc(),'target_jobs_complete':True})
        if scripts:pulse('node_generation_running',lanes=list(scripts));time.sleep(15)
    if nodes:
        subprocess.run(['rsync','-a','--ignore-existing','node01:'+REMOTE+'/results/audit/pair500/prefix254/generation.private/',str(PREFIX/'generation.private')+'/'],check=True)
        subprocess.run(['rsync','-a','node01:'+REMOTE+'/results/audit/pair500/prefix254/node_gate_results/',str(PREFIX/'node_gate_results')+'/'],check=True)
    materialize(items)
    assert all(len(list((BASE/'canonical254/generation.private'/n).glob('*.json')))==len(items) for n in NAMES)


def final_score(items,route):
    allargs=' '.join('--condition '+n for n in NAMES)
    if route['fallback']:
        subprocess.run(['rsync','-a',str(BASE/'canonical254/generation.private')+'/','node01:'+REMOTE+'/results/audit/pair500/canonical254/generation.private/'],check=True)
        assert execute_gpu('prefix_evaluate.py classifier '+allargs,'1,2','node01')==0
        shell=f'cd {REMOTE} && DEVICE=cpu CUDA_VISIBLE_DEVICES= /data/ray/pair_hash_env/bin/python -u tools/handoff_20261106/prefix_evaluate.py hash {allargs}'
        with (ROOT/'logs/prefix254_hash.log').open('ab') as log:subprocess.run(['ssh','node01',shell],stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run(['rsync','-a','node01:'+REMOTE+'/results/audit/pair500/canonical254/scores/',str(BASE/'canonical254/scores')+'/'],check=True)
        subprocess.run(['rsync','-a','node01:'+REMOTE+'/results/audit/pair500/canonical254/judge_launches/',str(BASE/'canonical254/judge_launches_node01')+'/'],check=True)
    else:
        assert execute_gpu('prefix_evaluate.py classifier '+allargs,'2,3')==0
        with (ROOT/'logs/prefix254_hash.log').open('ab') as log:subprocess.run([PY,str(ROOT/'tools/handoff_20261106/prefix_evaluate.py'),'hash',*sum([['--condition',n] for n in NAMES],[])],env={**os.environ,'DEVICE':'cpu','CUDA_VISIBLE_DEVICES':''},stdout=log,stderr=subprocess.STDOUT,check=True)
    assert execute_gpu('prefix_evaluate.py guard','2')==0
    assert all(len(list((BASE/'canonical254/scores'/n).glob('*.json')))==len(items) for n in NAMES)
    assert len(list((BASE/'canonical254/guard').glob('*.json')))==len(items)
    save(PREFIX/'generation_hb_guard_complete.json',{'utc':utc(),'n':len(items),'route':route,'no_effect_report':True})


def main():
    with (PREFIX/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        verify_code()
        cursor=0
        while not (BASE/'frozen_prompt_snapshot.json').exists():
            if not early_allowed():pulse('waiting_s7_generation_complete');time.sleep(30);continue
            items=sync_search()
            if len(items)<50:pulse('waiting_first50');time.sleep(30);continue
            alpha=[i for i in items if not(PREFIX/'generation.private/alpha0'/(i['id']+'.json')).exists()]
            if alpha:gen('alpha0',alpha[:50]);continue
            baseline50(items)
            refs=next((n for n in NAMES[1:] if any(not(PREFIX/'generation.private'/n/(i['id']+'.json')).exists() for i in items[:20])),None)
            if refs:gen(refs,items[:20]);continue
            available=False
            for _ in NAMES[1:]:
                name=NAMES[1:][cursor%12];cursor+=1
                pending=[i for i in items if not(PREFIX/'generation.private'/name/(i['id']+'.json')).exists()]
                if pending:gen(name,pending[:50]);available=True;break
            if not available:pulse('caught_up_with_search',n=len(items));time.sleep(30)
        items=sync_search();snapshot=load(BASE/'frozen_prompt_snapshot.json');assert len(items)==len(snapshot['rows'])
        route=choose_route()
        # At the first safe dispatch boundary after source closure, freeze the
        # resource route before another full alpha0 completion batch starts.
        gen('alpha0',items);baseline50(items)
        pulse('post_search_generation',route=route,n=len(items));node_lanes(items,route)
        pulse('classifying_final_snapshot',n=len(items));final_score(items,route);pulse('generation_hb_guard_complete')


if __name__=='__main__':
    PREFIX.mkdir(parents=True,exist_ok=True)
    try:main()
    except Exception as exc:pulse('failed',error_type=type(exc).__name__,error=str(exc));raise
