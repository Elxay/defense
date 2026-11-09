"""Export operational deployment evidence only; never aggregate classifier outcomes."""
from pathlib import Path
import datetime,hashlib,json,subprocess

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';S=BASE/'lease_priority';P=BASE/'prefix254'
OUT=BASE/'lease_priority_followup_20261109/deployment'
NAMES=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    now=datetime.datetime.now(datetime.timezone.utc);live=load(S/'controller_live.json')
    canonical=P/'controller_live.json'
    if canonical.exists():
        other=load(canonical)
        if other.get('utc','')>live.get('utc',''):live=other
    caught=sorted((S/'caught_up').glob('*.json'),key=lambda p:p.stat().st_mtime)
    jobs=[{k:v for k,v in x.items()if k in ['kind','cards','condition','tail_kind','shard','launcher_pid']}for x in live.get('jobs',{}).values()]
    windows=[]
    for d in sorted((S/'hb_windows').glob('*')):
        row={'pid':d.name}
        for name in ['started','ready','completed']:
            p=d/(name+'.json')
            if p.exists():
                x=load(p);row[name]={k:v for k,v in x.items()if k in ['utc','stage','reference20_passed','fresh_model_hash_check','PAIR_new_rows','scoring_seconds','bounded_window']};row[name+'_sha256']=sha(p)
        p=d/'judge20_gate.json'
        if p.exists():
            x=load(p);row['gate']={k:v for k,v in x.items()if k in ['passed','n','max_delta','max_abs_delta','intermediate','reference_sha256','method']};row['gate']['n']=len(x.get('ids',[]));row['gate_sha256']=sha(p)
        windows.append(row)
    tails=[]
    for p in sorted(S.glob('tail_live_gpu*.json')):
        x=load(p);x['wall_seconds_per_new_row']=x['wall_seconds']/x['new_rows']if x['new_rows']else None;x['metadata_sha256']=sha(p);x['process_exists']=Path('/proc',str(x['pid'])).exists();x['observation_age_seconds']=(now-datetime.datetime.fromisoformat(x['utc'])).total_seconds();tails.append(x)
    done=[load(p)for p in sorted(S.glob('tail_done_*.json'))]
    rates=load(S/'prefix_loading_cost.json');rates={n:{**x,'wall_rows_per_hour':3600/x['wall_seconds_per_row']}for n,x in rates['conditions'].items()}
    node_code="""from pathlib import Path
import json,statistics,datetime
b=Path('/home/dell/Def/results/audit/pair500');rows=[json.loads(p.read_text())['seconds']for p in(b/'generations.private').glob('*.json')];s=json.loads((b/'generation_live.json').read_text());print(json.dumps({'rows':len(rows),'mean_seconds_per_row':statistics.mean(rows),'worker_pid':s['pid'],'heartbeat_utc':s['utc'],'restart_count':1}))
"""
    pair=json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=node_code,text=True));pair['remaining_hours_cumulative_rate']=(500-pair['rows'])*pair['mean_seconds_per_row']/3600;pair['eta_utc_no_future_interruptions']=(now+datetime.timedelta(hours=pair['remaining_hours_cumulative_rate'])).isoformat()
    result={'utc':now.isoformat(),'jst':now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'phase':live['phase'],'scheduler_pid':live['pid'],'heartbeat_age_seconds':(now-datetime.datetime.fromisoformat(live['utc'])).total_seconds(),'accepted_source_rows':live.get('source_rows'),'prefix_coverage':{n:len(list((P/'generation.private'/n).glob('*.json')))for n in NAMES},'jobs':jobs,'first_caught_up':load(caught[0])if caught else None,'first_caught_up_sha256':sha(caught[0])if caught else None,'HB_windows':windows,'tail_live':tails,'tail_completed_invocations':done,'prefix_measured_rates':rates,'prefix_rate_source_sha256':sha(S/'prefix_loading_cost.json'),'PAIR_search':pair,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader'],text=True).splitlines(),'PAIR_outcomes_read':False,'rate_scope':'Completed task batches; wall includes startup and metadata operations. Different condition/output composition; no 1.5x scaling assumed.'}
    p=OUT/('snapshot_'+now.strftime('%Y%m%dT%H%M%S')+'.json');save(p,result)
    print(json.dumps({'file':str(p.relative_to(ROOT)),'sha256':sha(p),'utc':result['utc'],'jst':result['jst'],'PAIR_search':pair,'prefix_coverage':result['prefix_coverage'],'first_caught_up':result['first_caught_up'],'HB_windows':windows,'tail_live':tails},ensure_ascii=False))
if __name__=='__main__':main()
