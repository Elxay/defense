"""Fresh process/progress snapshot; reads heartbeats, not holdout data."""
import datetime,json,subprocess
from pathlib import Path
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round12';rel9='results/audit/handoff_round9/';rel11='results/audit/handoff_round11/';rel12='results/audit/handoff_round12/'
def local(p):
 f=B/p;return json.loads(f.read_text()) if f.exists() else {}
rpaths=[rel9+f'generate_full_s{s}_live.json' for s in (3,4,5)]+[rel11+'noise_B_live.json',rel11+'noise_B_launcher_live.json']+[rel12+f'same_alpha_s{s}_{part}.json' for s in (3,5) for part in ('live','launcher_live')]
code="""from pathlib import Path
import json,sys,subprocess
b=Path('/home/dell/Def'); files=sys.argv[1:]
print(json.dumps({**{p:json.loads((b/p).read_text()) for p in files if (b/p).exists()}, 'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used','--format=csv,noheader,nounits'],text=True)}))
"""
node=json.loads(subprocess.check_output(['ssh','-o','ConnectTimeout=8','node01','python3','-','--',*rpaths],input=code,text=True,timeout=15))
now=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()
t=datetime.datetime.fromisoformat(now.replace('Z','+00:00'));rows=[]
def row(job,host,gpu,d,note=None):
 if not d:return
 utc=d.get('utc');age=round(max(0,(t-datetime.datetime.fromisoformat(utc)).total_seconds()),1) if utc else None
 count=f"{d['n']}/{d['total']}" if 'n'in d and 'total'in d else note
 if count is None and ('n_harm' in d or 'n_pairs' in d):count=f"{d.get('n_harm',0)}/300 + {d.get('n_pairs',0)}/600"
 rows.append(dict(job=job,host=host,gpu=gpu,pid=d.get('pid'),phase=d.get('phase'),progress=count,seconds_per_item=d.get('seconds_per_item'),heartbeat_age_s=age,heartbeat_utc=utc))
for seed in range(3,8):
 p=rel9+f'generate_full_s{seed}_live.json'
 d=node.get(p,{}) if seed in (3,4,5) else local(p)
 row(f'original_s{seed}','node01' if seed<6 else 'innet',{3:0,4:1,5:2,6:2,7:3}[seed],d,'1800/1800' if d.get('phase')=='complete' else None)
for seed in (3,5):
 x=node.get(rel12+f'same_alpha_s{seed}_live.json') or node.get(rel12+f'same_alpha_s{seed}_launcher_live.json',{})
 row(f'same_alpha_s{seed}','node01',{3:0,5:2}[seed],x,'0/600')
x=node.get(rel11+'noise_B_live.json') or node.get(rel11+'noise_B_launcher_live.json',{})
row('noise_B','node01',0,x)
row('legal400','innet',2,local(rel12+'legal400_live.json'))
row('original_controller','innet','CPU',local(rel9+'pipeline_live.json'))
row('plain_controller','innet','CPU',local(rel11+'plain_pipeline_live.json'),'5/5 vectors done; grid 0')
row('same_alpha_analysis','innet','CPU',local(rel12+'same_alpha_analysis_live.json'))
row('primary_read_gate','innet','CPU',local(rel12+'primary_read_wait_live.json'))
d=dict(date_u=now,jst=t.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),rows=rows,gpu_mib={'node01':node['gpu'].strip(),'innet':subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used','--format=csv,noheader,nounits'],text=True).strip()},original_effect_file_exists=(B/rel9/'intervention_complete_results.json').exists())
(O/'status_fresh.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
