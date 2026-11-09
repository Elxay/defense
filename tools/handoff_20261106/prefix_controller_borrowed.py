"""Two leased single-row lanes; no outcome reads, row-disjoint dispatch."""
from pathlib import Path
import collections
import fcntl
import json
import os
import signal
import subprocess
import time

from borrowed_gpu_support import verify_extension, gpu0_enabled
import prefix_controller as old
from prefix_support import ROOT,BASE,PREFIX,RUNTIME,load,save,sha,utc,verify_code

STOP=False
def request_stop(*_):
    global STOP
    STOP=True


def start(name,items,accepted,device):
    path=old.task(name,items)
    rows={r['id']:r for r in load(BASE/'rows.private.json')}
    record={'utc':utc(),'condition':name,'physical_device':device,'task_sha256':sha(path),'batch_n':len(items),
        'batch_layers':dict(collections.Counter(rows[x['id']]['layer'] for x in items)),
        'accepted_prefix_n':len(accepted),'prefix_layers':dict(collections.Counter(rows[x['id']]['layer'] for x in accepted)),
        'ids':[x['id'] for x in items],'before_process_launch':True,'runtime_sha256':sha(RUNTIME)}
    meta=PREFIX/'dispatch_metadata'/(path.stem+'_gpu'+device+'.json');save(meta,record)
    script=f'''set -euo pipefail
cd {ROOT}
source night/launch.sh
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu{device}.lock
flock 8
until wait_gpu cuda:{device}; do sleep 15; done
DEVICE=cuda:{device} launch_job env CUDA_VISIBLE_DEVICES={device} DEVICE=cuda:{device} {old.PY} -u tools/handoff_20261106/prefix_generate_borrowed.py --task {path.relative_to(ROOT)}
'''
    log=(ROOT/'logs'/('prefix254_dual_gpu'+device+'.log')).open('ab',buffering=0)
    proc=subprocess.Popen(['bash','-s'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT)
    proc.stdin.write(script.encode());proc.stdin.close()
    return {'proc':proc,'log':log,'condition':name,'ids':record['ids'],'dispatch_metadata_sha256':sha(meta)}


def main():
    signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGINT,request_stop)
    with (PREFIX/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);verify_extension();verify_code()
        lanes={};cursor=0;items=[];last_sync=0
        while True:
            for device,job in list(lanes.items()):
                code=job['proc'].poll()
                if code is not None:
                    job['log'].close();del lanes[device]
                    if code not in [0,75]:raise RuntimeError(f'GPU{device} generation failed exit {code}')
            closed=(BASE/'frozen_prompt_snapshot.json').exists()
            if (closed or STOP) and not lanes:break
            if not(closed or STOP):
                if time.monotonic()-last_sync>15 or not items:
                    items=old.sync_search();last_sync=time.monotonic()
                reserved={(job['condition'],key) for job in lanes.values() for key in job['ids']}
                for device in ['2','3','0']:
                    if device=='0' and not gpu0_enabled():continue
                    if device in lanes:continue
                    pending=[x for x in items if not(PREFIX/'generation.private/alpha0'/(x['id']+'.json')).exists() and ('alpha0',x['id']) not in reserved]
                    name='alpha0'
                    if not pending:
                        if not(PREFIX/'alpha0_first50_cross_node.json').exists():
                            if all((PREFIX/'generation.private/alpha0'/(x['id']+'.json')).exists() for x in items[:50]):old.baseline50(items)
                            else:continue
                        for _ in old.NAMES[1:]:
                            name=old.NAMES[1:][cursor%12];cursor+=1
                            pending=[x for x in items if (PREFIX/'generation.private/alpha0'/(x['id']+'.json')).exists() and not(PREFIX/'generation.private'/name/(x['id']+'.json')).exists() and (name,x['id']) not in reserved]
                            if pending:break
                    if pending:
                        batch=pending[:50];lanes[device]=start(name,batch,items,device);reserved.update((name,x['id']) for x in batch)
            state={'utc':utc(),'pid':os.getpid(),'phase':'early_generation_borrowed_three_lanes' if not closed else 'closing_prefix_lanes','source_rows':len(items),
                'lanes':{d:{'launcher_pid':j['proc'].pid,'condition':j['condition'],'batch_n':len(j['ids']),'dispatch_metadata_sha256':j['dispatch_metadata_sha256']} for d,j in lanes.items()},'stop_requested':STOP}
            save(PREFIX/'controller_live.json',state);save(PREFIX/'triple_live.json',state);time.sleep(5)
        if STOP:old.pulse('paused_at_row_batch_boundaries');return
        items=old.sync_search();assert len(items)==len(load(BASE/'frozen_prompt_snapshot.json')['rows'])
        route=old.choose_route();old.gen('alpha0',items);old.baseline50(items)
        old.pulse('post_search_generation',route=route,n=len(items));old.node_lanes(items,route)
        old.pulse('classifying_final_snapshot',n=len(items));old.final_score(items,route);old.pulse('generation_hb_guard_complete')
        if route['fallback']:
            subprocess.run(['rsync','-a','node01:/home/dell/Def/results/audit/pair500/public255/mapped_top2_scores/',str(BASE/'public255/mapped_top2_scores')+'/'],check=True)
            subprocess.run(['rsync','-a','node01:/home/dell/Def/results/audit/pair500/wjb_top2_shared_window_done.json',str(BASE)+'/'],check=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:old.pulse('failed',error_type=type(exc).__name__,error=str(exc));raise
