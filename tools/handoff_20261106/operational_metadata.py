"""Operational fields only. No imports from evaluation or aggregation code."""
import datetime
import json
import os
from pathlib import Path
import statistics
import subprocess

ROOT=Path('/data/HZX/Def')
BASE=ROOT/'results/audit/pair500'


def small_metadata(path, keys):
    if not path.exists(): return None
    data=json.loads(path.read_text())
    return {key:data[key] for key in keys if key in data}


def capture():
    remote="""from pathlib import Path
import json,datetime,statistics,subprocess
base=Path('/home/dell/Def/results/audit/pair500');now=datetime.datetime.now(datetime.timezone.utc)
live=json.loads((base/'generation_live.json').read_text());times=[]
for p in (base/'generations.private').glob('*.json'):
 data=json.loads(p.read_text());times.append((p.stat().st_mtime,float(data['seconds'])))
recent=[v for _,v in sorted(times)[-10:]]
worker={k:live[k] for k in ['pid','utc','gpus','n','of','phase'] if k in live};worker['alive']=Path('/proc',str(live.get('pid',0))).exists()
worker.update(completed_rows=len(times),mean_seconds_per_row=statistics.mean(v for _,v in times) if times else None,recent10_seconds=recent,heartbeat_age_s=(now-datetime.datetime.fromisoformat(live['utc'].replace('Z','+00:00'))).total_seconds())
out=[]
for folder in ['wildguard','wildguard_public','wildguard_pair254']:
 for p in (base/folder).glob('*_live.json'):
  data=json.loads(p.read_text());pid=data.get('pid')
  if pid and Path('/proc',str(pid)).exists():
   fields={k:data[k] for k in ['utc','pid','n','total','seconds_per_scored_row','host','gpu'] if k in data}
   out.append({'group':folder,'file':p.name,**fields,'heartbeat_age_s':(now-datetime.datetime.fromisoformat(data['utc'])).total_seconds()})
print(json.dumps({'utc':now.isoformat(),'pair':worker,'node01_active_classifiers':out,'gpu_memory':subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used','--format=csv,noheader,nounits'],text=True).splitlines()}))
"""
    result=json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=remote,text=True,timeout=40))
    result['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    fields=['pid','utc','device','n','total','seconds_per_row','stage','condition']
    result['innet_active_workers']=[]
    for p in (BASE/'public255').glob('live_*.json'):
        data=small_metadata(p,fields)
        if data.get('pid') and Path('/proc',str(data['pid'])).exists():
            data.update(file=p.name,heartbeat_age_s=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(data['utc'])).total_seconds())
            result['innet_active_workers'].append(data)
    result['wjb_generation_coverage']={name:len(list((BASE/'public255/harmful.private'/name/'wildjailbreak_harmful').glob('*.json'))) for name in ['rand3','old_s7','old_s0','SYS_A','SYS_B']}
    result['judge_coverage']={name:{'hb_top1_files':len(list((BASE/'public255/mapped_scores'/name).glob('*.json'))),'wg_files':len(list((BASE/'wildguard'/(name+'_scores')).glob('*.json')))} for name in ['old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7']}
    for key,rel in [('harmful_wg_queue','wildguard/conditions_queue_live.json'),('public_wg_queue','wildguard_public/queue_live.json'),('morning_capture','morning_0800_capture_live.json')]:
        result[key]=small_metadata(BASE/rel,['utc','pid','phase','condition','due_utc'])
    history=BASE/'gpu3_external_30m.jsonl'
    result['external_gpu3_last_observation']=json.loads(history.read_text().splitlines()[-1]) if history.exists() else None
    result['innet_gpu_memory']=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used','--format=csv,noheader,nounits','-i','2,3'],text=True).splitlines()
    result['imports_analysis_code']=False
    result['reads_outcome_labels']=False
    result['prefix_generation']=small_metadata(BASE/'prefix254/controller_live.json',['utc','pid','phase','condition','n','source_rows'])
    result['prefix_generation_coverage']={name:len(list((BASE/'prefix254/generation.private'/name).glob('*.json'))) for name in ['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']}
    return result
