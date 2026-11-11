"""Progress-only metadata; no main judge record or effect reads."""
from pathlib import Path
import datetime,hashlib,json,subprocess,statistics
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def L(p):return json.loads(Path(p).read_text())
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
now=utc();C=L(U/'ready_queue_catalog.json');S=L(U/'ready_queue/state.json')
gpu={}
for site in ['innet','node01']:
 args=['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits']
 if site=='node01':args=['ssh','node01',*args]
 gpu[site]=[]
 for line in subprocess.check_output(args,text=True).strip().splitlines():
  i,mem,util=map(int,line.split(','));gpu[site].append(dict(card=i,memory_MiB=mem,utilization_percent=util))
progress={}
for judge in ['SORRY','WG']:
 rel='results/audit/unified300/queue_jobs/score_'+judge+'_0001__1/live.json'
 if judge=='WG':z=json.loads(subprocess.check_output(['ssh','node01','cat /home/dell/Def/'+rel],text=True))
 else:z=L(R/rel)
 progress[judge]=z
hist=U/'scoring_progress_history.jsonl';old=[json.loads(x) for x in hist.read_text().splitlines()] if hist.exists() else []
etas={}
for judge,z in progress.items():
 candidates=[v for v in old if judge in v['progress'] and
    (datetime.datetime.fromisoformat(z['utc'])-datetime.datetime.fromisoformat(v['progress'][judge]['utc'])).total_seconds()>=60]
 if candidates:
  p=candidates[-1]['progress'][judge];seconds=(datetime.datetime.fromisoformat(z['utc'])-datetime.datetime.fromisoformat(p['utc'])).total_seconds()
  rate=(z['completed_input_rows']-p['completed_input_rows'])*3600/seconds
  if rate>0:
   left=(z['total_rows']-z['completed_input_rows'])/rate
   eta=datetime.datetime.fromisoformat(z['utc'])+datetime.timedelta(hours=left)
   etas[judge]=dict(recent_rows_per_hour=rate,elapsed_between_snapshots_seconds=seconds,
          forecast_utc=eta.isoformat(),scope='First wave only, recent observed throughput; not full campaign or confidence interval')
snapshot=dict(utc=now,controller_utc=S['utc'],progress=progress,first_wave_ETA=etas,gpus=gpu,
 active=[dict(task=k,site=v['site'],gpus=v['gpus'],started_utc=v['started_utc']) for k,v in S['tasks'].items() if v['state']=='running'],
 encoding_alpha0_task_counts={s:sum(1 for t in C['tasks'] if t['id'].startswith('encoding_') and S['tasks'].get(t['id'],{}).get('state','pending')==s) for s in ['pending','running','done','failed']},
 language_preprocessing_planned_cells=len(L(U/'language_preprocess_execution_v2.json')['cells']),
 main_labels_INVALID_counts_and_effects_read=False)
with hist.open('a') as f:f.write(json.dumps(snapshot)+'\n')
save(U/'scoring_live_metadata.json',snapshot)
cost=[];fallback=[]
for method in ['PAIR','TAP']:
 for model in ['llama','qwen']:
  folder=U/(method+'_pilot')/model;files=list((folder/'rows.private').glob('*.json'))
  if files:
   same=sum(hashlib.sha256(L(p)['selected_prompt'].encode()).hexdigest()==L(p)['source_behavior_sha256'] for p in files if L(p)['selected_prompt'] is not None)
   fallback.append(dict(method=method,model=model,N=len(files),fallback=same,scope='completed pilot final prompts only'))
  cp=folder/'timing_complete.json'
  if cp.exists():
   c=L(cp);mean=statistics.mean(L(p)['seconds'] for p in files)
   cold=2*c['cold_seconds']/3600
   cost.append(dict(method=method,model=model,window_GPUh=c['forecast_GPUh']['440'],
     steady_without_cold_GPUh=440*mean/8*2/3600,steady_with_cold_GPUh=cold+440*mean/8*2/3600,
     cold_GPUh=cold,formal_window_seconds=c['formal_window_seconds']))
save(U/'search_cost_and_fallback_latest.json',dict(utc=now,cost=cost,fallback=fallback,
   known_440_point_sum=sum(c['window_GPUh'] for c in cost),not_tier_selection=True))
print(json.dumps(snapshot))
print(json.dumps(dict(cost=cost,fallback=fallback)))
