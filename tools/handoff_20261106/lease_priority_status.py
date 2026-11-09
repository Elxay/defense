"""Operational snapshot only: no judge labels, probabilities or effect imports."""
from pathlib import Path
import datetime,hashlib,json,subprocess
ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';STATE=BASE/'lease_priority'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();names=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B'];prefix=BASE/'prefix254'
    live=load(STATE/'controller_live.json')if(STATE/'controller_live.json').exists()else None
    coverage={name:len(list((prefix/'generation.private'/name).glob('*.json')))for name in names};caught=[load(p)for p in sorted((STATE/'caught_up').glob('*.json'),key=lambda p:p.stat().st_mtime)]
    tail={kind:{name:sum(len(load(p)['items'])for p in (BASE/'public255'/f'{kind}.private'/name).glob('*/*.json'))for name in ['old_s0','SYS_A','SYS_B']}for kind in ['harmful','public']}
    tailtiming=[load(p)for p in STATE.glob('tail_done_*.json')];guardcounts={kind:{name:len(list((BASE/'public255/output_guard_all'/kind/name).glob('*/*.json')))for name in names}for kind in ['harmful','public']}
    windows=[]
    for p in (STATE/'hb_windows').glob('*'):
        row={'window':p.name}
        for name in ['started','ready','completed']:
            q=p/(name+'.json')
            if q.exists():x=load(q);row[name]={k:v for k,v in x.items()if k in ['utc','pid','stage','reference20_passed','fresh_model_hash_check','PAIR_new_rows','scoring_seconds','bounded_window']};row[name+'_sha256']=sha(q)
        windows.append(row)
    node_code="""from pathlib import Path
import json,statistics,datetime
b=Path('/home/dell/Def/results/audit/pair500');live=json.loads((b/'generation_live.json').read_text());rows=[json.loads(p.read_text())['seconds']for p in (b/'generations.private').glob('*.json')];print(json.dumps({'n':len(rows),'mean_seconds':statistics.mean(rows),'worker_pid':live['pid'],'heartbeat_utc':live['utc'],'restart_count':1}))
"""
    node=json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=node_code,text=True));result={'utc':now,'controller':live,'prefix_coverage':coverage,'first_recorded_caught_up':caught[0]if caught else None,'last_caught_up':caught[-1]if caught else None,'tail_generation_coverage':tail,'completed_tail_invocations':tailtiming,'HB_windows':windows,'HB_prefix_cached_counts':{name:len(list((prefix/'hb_pre_scores'/name).glob('*.json')))for name in names},'Guard_cached_counts':guardcounts,'PAIR_search':node,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader'],text=True).splitlines(),'outcome_labels_read':False}
    destination=STATE/'snapshots'/(now.replace(':','')+'.json');destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'file':str(destination.relative_to(ROOT)),'sha256':sha(destination),**result},ensure_ascii=False))
if __name__=='__main__':main()
