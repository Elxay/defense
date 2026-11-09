"""Finish lower-priority WJB/Guard checkpoints after canonical PAIR GPU work."""
from pathlib import Path
import fcntl,os,time
from lease_priority_support import ROOT,BASE,STATE,load,save,sha,utc,verify
import lease_priority_controller as ctl

def main():
    verify()
    while not(STATE/'PAIR_GPU_complete.json').exists():save(STATE/'aux_finish_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'waiting_PAIR_GPU_work','effects_read':False});time.sleep(15)
    with (BASE/'prefix254/controller.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);jobs={};cursor=0
        while True:
            for card,j in list(jobs.items()):
                code=j['proc'].poll()
                if code is not None:
                    j['log'].close();del jobs[card]
                    if code not in [0,75]:raise RuntimeError('auxiliary job failed '+str(code))
            # Once generation is complete, let HB auxiliary scores take both cards.
            gen_pending=any(ctl.tail_candidate(k,{}) is not None for k in ['public','harmful'])
            if not gen_pending and ctl.optional_hb_pending():
                for j in jobs.values():
                    if j['kind'] in ['tail','guard']:
                        for c in j['cards']:ctl.request(c,'auxiliary HB after PAIR')
                if not jobs:
                    for c in ['2','3']:ctl.clear_request(c)
                    flag=STATE/'hb_yield.json'
                    if flag.exists():flag.unlink()
                    task={'utc':utc(),'items':[],'auxiliary_after_PAIR':True,'effects_read':False};p=STATE/'hb_tasks'/('aux_'+utc().replace(':','')+'.json');save(p,task);jobs['hb']=ctl.launch('prefix_hb_incremental_worker.py --task '+str(p.relative_to(ROOT)),['2','3'],'hb',pair_rows=0)
            else:
                occupied={c for j in jobs.values() for c in j['cards']}
                for c in ['2','3']:
                    if c in occupied:continue
                    ctl.clear_request(c);selected=None
                    for _ in range(3):
                        kind=['public','harmful','guard'][cursor%3];cursor+=1
                        if kind=='guard':
                            if not any(j['kind']=='guard' for j in jobs.values()) and ctl.guard_pending():selected=('guard',None,None);break
                        else:
                            candidate=ctl.tail_candidate(kind,jobs)
                            if candidate:selected=(kind,*candidate);break
                    if selected:
                        kind,name,shard=selected
                        jobs[c]=ctl.launch('auxiliary_output_guard_worker.py --limit 400',[c],'guard') if kind=='guard' else ctl.launch(f'wjb_tail_priority_worker.py {kind} {name} --shard {shard}',[c],'tail',tail_kind=kind,condition=name,shard=shard)
            phase='auxiliary_running'
            if not jobs and not gen_pending and not ctl.optional_hb_pending() and not ctl.guard_pending():phase='all_auxiliary_GPU_work_complete'
            save(STATE/'aux_finish_live.json',{'utc':utc(),'pid':os.getpid(),'phase':phase,'jobs':list(jobs),'effects_read':False})
            if phase=='all_auxiliary_GPU_work_complete':return
            time.sleep(5)

if __name__=='__main__':main()
