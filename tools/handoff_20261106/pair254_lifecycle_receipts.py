"""Observe lifecycle timing only; never open classifier outputs or invoke reports."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';O=B/'read_order10/lifecycle';NAMES=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.'+str(os.getpid())+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');os.replace(q,p)
def receipt(name,x):
    p=O/(name+'.json')
    if p.exists():return
    put(p,{'observed_utc':utc(),'outcome_labels_read':False,**x})
    with(R/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{utc()} PAIR254_LIFECYCLE {name} receipt={p.relative_to(R)} SHA={sha(p)} operational timing only; no outcome read.\n')
def main():
    O.mkdir(parents=True,exist_ok=True);start=time.monotonic();last_node=0
    while time.monotonic()-start<96*3600:
        now=utc();snapshot=B/'frozen_prompt_snapshot.json'
        if not(O/'search_complete.json').exists() and time.monotonic()-last_node>30:
            code="from pathlib import Path;import json; p=Path('/home/dell/Def/results/audit/pair500/generation_live.json');x=json.loads(p.read_text());print(json.dumps({k:x[k]for k in ['utc','pid','phase','saved','limit']}))"
            try:
                result=subprocess.run(['ssh','node01','python3','-'],input=code,text=True,capture_output=True,timeout=25);assert result.returncode==0;x=json.loads(result.stdout)
                if x['phase']=='complete':receipt('search_complete',{'event_utc':x['utc'],'source':'node01 generation_live complete heartbeat','worker_pid':x['pid'],'saved':x['saved'],'limit':x['limit']})
            except(Exception)as e:put(O/'last_node_probe_error.json',{'utc':utc(),'error_type':type(e).__name__})
            last_node=time.monotonic()
        if snapshot.exists():
            x=json.loads(snapshot.read_text());ids=[r['id']for r in x['rows']];receipt('final_snapshot',{'snapshot_sha256':sha(snapshot),'n':len(ids),'snapshot_record_utc':x.get('utc'),'source':'actual final snapshot, not an early prefix'})
            if not(O/'target_generation_complete.json').exists():
                files=[B/'prefix254/generation.private'/n/(k+'.json')for n in NAMES for k in ids]
                if all(p.is_file()for p in files):
                    t=max(p.stat().st_mtime for p in files);receipt('target_generation_complete',{'n':len(ids),'conditions':len(NAMES),'snapshot_sha256':sha(snapshot),'last_atomic_file_mtime_utc':datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat(),'mtime_scope':'Prefix output mtime; observed_utc is the completeness observation, not inferred search end. No generation text or labels selected.'})
            if(B/'lease_priority/PAIR_GPU_complete.json').exists():receipt('PAIR_GPU_complete',{'source_receipt_sha256':sha(B/'lease_priority/PAIR_GPU_complete.json')})
            # Readiness uses file coverage only, including non-applicable copyright fields.
            nines=NAMES[1:10];both=all((B/'canonical254/scores'/n/(k+'.json')).is_file()and(B/'wildguard_pair254'/(n+'_scores')/(k+'.json')).is_file()for n in ['alpha0',*nines]for k in ids)
            if both:
                receipt('both_judges_ready',{'n':len(ids),'units':9,'alpha0_included':True,'snapshot_sha256':sha(snapshot),'coverage_only':True});put(O/'observer_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'finished_readiness_only','labels_read':False});return
        put(O/'observer_live.json',{'utc':now,'pid':os.getpid(),'phase':'waiting_lifecycle_events','snapshot_exists':snapshot.exists(),'labels_read':False});time.sleep(15)
    receipt('observer_time_limit',{'hours':96})
if __name__=='__main__':main()
