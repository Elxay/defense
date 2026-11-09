"""One dispatcher for PAIR-first leases, bounded scoring and resumable auxiliary work."""
from pathlib import Path
import collections,fcntl,json,os,signal,subprocess,time
from lease_priority_support import ROOT,BASE,STATE,load,save,sha,utc,verify,request_path
import prefix_controller as old
from prefix_support import PREFIX,RUNTIME,objsha
from gpu0_day_authorization import install
install()
from borrowed_gpu_support import gpu0_enabled

STOP=False
def stop(*_):
    global STOP;STOP=True

def launch(arguments,cards,kind,**metadata):
    card=cards[0];locks='\n'.join(f'exec {8-i}>>logs/idle_gpu{c}.lock\nflock {8-i}' for i,c in enumerate(cards));checks=' && '.join('wait_gpu cuda:'+c for c in cards)
    optional=f'if test -f {request_path(card).relative_to(ROOT)}; then exit 75; fi' if kind in ['tail','guard'] else 'true'
    shell=f'''set -euo pipefail
cd {ROOT}
source night/launch.sh
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
{locks}
{optional}
until {checks}; do {optional}; sleep 5; done
{optional}
DEVICE=cuda:{card} launch_job env CUDA_VISIBLE_DEVICES={','.join(cards)} DEVICE=cuda:{card} {old.PY} -u tools/handoff_20261106/gpu0_authorized_bootstrap.py {arguments}
'''
    event={'utc':utc(),'kind':kind,'cards':cards,**metadata};eventpath=STATE/'dispatches'/(utc().replace(':','')+'_'+kind+'.json');save(eventpath,event)
    log=(ROOT/'logs'/('lease_priority_'+kind+'_'+''.join(cards)+'.log')).open('ab',buffering=0);proc=subprocess.Popen(['bash','-s'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT);proc.stdin.write(shell.encode());proc.stdin.close();return {'proc':proc,'log':log,'kind':kind,'cards':cards,'event_sha256':sha(eventpath),**metadata}

def prefix_pending(items,jobs):
    reserved={(j['condition'],k) for j in jobs.values() if j['kind']=='prefix' for k in j['ids']};result={}
    for name in old.NAMES:
        result[name]=[x for x in items if (name=='alpha0' or (PREFIX/'generation.private/alpha0'/(x['id']+'.json')).exists()) and not(PREFIX/'generation.private'/name/(x['id']+'.json')).exists() and (name,x['id']) not in reserved]
    return result

def coverage(items):
    return {n:sum((PREFIX/'generation.private'/n/(x['id']+'.json')).exists() for x in items) for n in old.NAMES}

def hb_pending(items):
    from prefix_hb_incremental_worker import cache_signature
    rows={r['id']:r for r in load(BASE/'rows.private.json')};pending=[]
    for name in old.NAMES:
        for row in items:
            key=row['id']
            if rows[key]['layer']=='copyright':continue
            p=PREFIX/'generation.private'/name/(key+'.json')
            if not p.exists():continue
            dest=PREFIX/'hb_pre_scores'/name/(key+'.json');sig=cache_signature(sha(p),row['row_sha256'])
            if dest.exists():assert load(dest)['signature']==sig;continue
            pending.append({'condition':name,'id':key,'generation_sha256':sig['prefix_generation_sha256'],'row_sha256':row['row_sha256']})
    return pending

def optional_hb_pending():
    if not(BASE/'wjb_top2_shared_window_done.json').exists():return True
    for name in ['old_s0','SYS_A','SYS_B']:
        existing={p.stem for p in (BASE/'public255/harmful.private'/name/'wildjailbreak_harmful').glob('*.json')};scored={p.stem for p in (BASE/'public255/mapped_scores'/name).glob('*.json')}
        if existing-scored:return True
    return False

def tail_candidate(kind,jobs):
    import wjb_eval255_run as w
    reserved={(j['tail_kind'],j['condition'],j['shard']) for j in jobs.values() if j['kind']=='tail'}
    for name in ['old_s0','SYS_A','SYS_B']:
        tasks=[]
        for shard in [0,1]:
            if kind=='harmful':
                keys=load(w.PLAN)['ids'][shard::2];pending=any(not(w.EVAL/'harmful.private'/name/'wildjailbreak_harmful'/(k+'.json')).exists() for k in keys)
            else:
                pending=any(not(w.EVAL/'public.private'/name/d/(data[i][0]+'.json')).exists() for d,data in w.public_rows().items() for i in range(shard*8,len(data),16))
            if pending:tasks.append(shard)
        if tasks:
            for shard in tasks:
                if (kind,name,shard) not in reserved:return (name,shard)
            return None  # Preserve condition order within this output family.
    return None

def guard_pending():
    import wjb_eval255_run as w
    for name in old.NAMES:
        for kind in ['public','harmful']:
            if kind=='harmful' and name=='alpha0':
                if len(list((BASE/'public255/output_guard_all/harmful/alpha0/wildjailbreak_harmful').glob('*.json')))<2000:return True
                continue
            for p in (BASE/'public255'/f'{kind}.private'/name).glob('*/*.json'):
                # Inspect identifiers only; no probabilities or refusal aggregates.
                d=p.parent.name
                if any(not(BASE/'public255/output_guard_all'/kind/name/d/(x['id']+'.json')).exists() for x in load(p)['items']):return True
    return False

def request(card,reason):save(request_path(card),{'utc':utc(),'scheduler_pid':os.getpid(),'reason':reason})
def clear_request(card):
    p=request_path(card)
    if p.exists():
        x=load(p);owner=x.get('scheduler_pid');assert owner==os.getpid() or not Path('/proc',str(owner)).exists();p.unlink()

def main():
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);verify();assert sha(Path(__file__))==load(BASE/"gpu0_day_authorization.json")["controller_sha256"]
    with(PREFIX/'controller.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        verify();jobs={};cursor=0;low_cursor=0;last_sync=0;items=[];last_hb=0;last_counts={};first_caught=False
        while True:
            for tag,j in list(jobs.items()):
                code=j['proc'].poll()
                if code is not None:
                    j['log'].close();del jobs[tag]
                    if code not in [0,75]:raise RuntimeError(f'{j["kind"]} failed exit{code}, preserve checkpoints')
            closed=(BASE/'frozen_prompt_snapshot.json').exists()
            if STOP or closed:
                for j in jobs.values():
                    if j['kind'] in ['tail','guard']:
                        for c in j['cards']:request(c,'PAIR closure/drain')
                    if j['kind']=='hb':save(STATE/'hb_yield.json',{'utc':utc(),'reason':'PAIR source closure'})
                if not jobs:break
            elif time.monotonic()-last_sync>15 or not items:items=old.sync_search();last_sync=time.monotonic()
            if not(STOP or closed):
                counts=coverage(items);caught=bool(items) and all(v==len(items) for v in counts.values())
                if caught and counts!=last_counts:
                    receipt={'utc':utc(),'source_rows':len(items),'coverage':counts,'source_manifest_sha256':sha(PREFIX/'accepted_source_files.json'),'effects_read':False};save(STATE/'caught_up'/(str(len(items))+'.json'),receipt)
                    with(ROOT/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{utc()} PAIR_PREFIX_CAUGHT_UP n={len(items)} all13conditions SHA={sha(STATE/"caught_up"/(str(len(items))+".json"))} no outcome reads.\n')
                    last_counts=counts;first_caught=True
                occupied={c for j in jobs.values() for c in j['cards']}
                # A window may start only at an observed fully-generated prefix.
                reserve_hb=False
                if caught and not any(j['kind']=='hb' for j in jobs.values()) and time.monotonic()-last_hb>30:
                    pending=hb_pending(items)
                    if len(pending)>=256:  # Auxiliary classification never opens a window by itself.
                        reserve_hb=True
                        for j in jobs.values():
                            if j['kind'] in ['tail','guard']:
                                for c in set(j['cards'])&{'2','3'}:request(c,'PAIR incremental judge lease')
                        if not {'2','3'}&occupied:
                            for c in ['2','3']:clear_request(c)
                            flag=STATE/'hb_yield.json'
                            if flag.exists():flag.unlink()
                            task={'utc':utc(),'source_rows':len(items),'source_manifest_sha256':sha(PREFIX/'accepted_source_files.json'),'items':pending,'effects_read':False};p=STATE/'hb_tasks'/(utc().replace(':','')+'.json');save(p,task)
                            jobs['hb']=launch('prefix_hb_incremental_worker.py --task '+str(p.relative_to(ROOT)),['2','3'],'hb',task_sha256=sha(p),pair_rows=len(pending));last_hb=time.monotonic();occupied|={'2','3'}
                pending=prefix_pending(items,jobs)
                for card in ['2','3','0']:
                    if card in occupied or (card=='0' and not gpu0_enabled()):continue
                    name='alpha0';todo=pending['alpha0']
                    if not todo:
                        for _ in old.NAMES[1:]:
                            name=old.NAMES[1:][cursor%12];cursor+=1;todo=pending[name]
                            if todo:break
                    if todo:
                        clear_request(card);batch=todo[:50];p=old.task(name,batch);jobs[card]=launch('prefix_generate_borrowed.py --task '+str(p.relative_to(ROOT)),[card],'prefix',condition=name,ids=[x['id'] for x in batch],source_rows=len(items));pending[name]=todo[50:];occupied.add(card)
                # Request cooperative yield only if unreserved high-priority work remains.
                if any(pending.values()):
                    for j in jobs.values():
                        if j['kind'] in ['tail','guard']:
                            for c in j['cards']:request(c,'unreserved PAIR generation')
                for card in ['2','3','0']:
                    if card in occupied or (card=='0' and not gpu0_enabled()):continue
                    if reserve_hb and card in ['2','3']:continue
                    clear_request(card);selected=None
                    for _ in range(5):
                        kind=['public','harmful','public','harmful','guard'][low_cursor%5];low_cursor+=1
                        if kind=='guard':
                            if not any(j['kind']=='guard' for j in jobs.values()) and guard_pending():selected=('guard',None,None);break
                        else:
                            candidate=tail_candidate(kind,jobs)
                            if candidate:selected=(kind,*candidate);break
                    if selected:
                        kind,name,shard=selected
                        if kind=='guard':jobs[card]=launch('auxiliary_output_guard_worker.py --limit 400',[card],'guard')
                        else:jobs[card]=launch(f'wjb_tail_priority_worker_v2.py {kind} {name} --shard {shard}',[card],'tail',tail_kind=kind,condition=name,shard=shard)
                        occupied.add(card)
            live={'utc':utc(),'pid':os.getpid(),'phase':'lease_priority_running' if not(STOP or closed) else 'draining_for_final_snapshot','source_rows':len(items),'caught_up_observed':first_caught,'jobs':{k:{x:v for x,v in j.items() if x not in ['proc','log']}|{'launcher_pid':j['proc'].pid} for k,j in jobs.items()},'stop_requested':STOP,'effects_read':False};save(STATE/'controller_live.json',live);save(PREFIX/'controller_live.json',live);time.sleep(5)
        if STOP:return
        items=old.sync_search();assert len(items)==len(load(BASE/'frozen_prompt_snapshot.json')['rows']);route=old.choose_route();old.gen('alpha0',items);old.baseline50(items);old.node_lanes(items,route)
        from prefix_hb_cache_reuse import import_verified
        reused=import_verified();save(STATE/'final_cache_import.json',{'utc':utc(),'counts':reused,'effects_read':False});old.final_score(items,route);old.pulse('generation_hb_guard_complete')
        # Auxiliary workers are resumed by a separate invocation after the primary queue.
        save(STATE/'PAIR_GPU_complete.json',{'utc':utc(),'n':len(items),'effects_read':False})

if __name__=='__main__':
    try:main()
    except Exception as exc:save(PREFIX/'controller_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'failed','error_type':type(exc).__name__,'error':str(exc),'effects_read':False});raise
