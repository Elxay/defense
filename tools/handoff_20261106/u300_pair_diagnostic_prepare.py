from pathlib import Path
import hashlib,json,statistics
from transformers import AutoTokenizer
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
D=U/'PAIR_alpha0_independent_replay';assert not (D/'plan.json').exists()
base=L(U/'ready_generation_plan.json');original={r['id']:r for r in L(U/'PAIR_pilot_inputs.private.json')}
data={};rowsmeta=[];fallback=[];costs=[]
for method in ['PAIR','TAP']:
 for model in ['llama','qwen']:
  folder=U/(method+'_pilot')/model;files=sorted((folder/'rows.private').glob('*.json'))
  if files:
   count=0;fail=0
   for p in files:
    r=L(p);prompt=r.get('selected_prompt');fail+=prompt is None
    if prompt is not None:count+=hashlib.sha256(prompt.encode()).hexdigest()==r['source_behavior_sha256']
   fallback.append(dict(method=method,model=model,N_completed=len(files),fallback=count,execution_missing_prompt=fail))
  if (folder/'timing_complete.json').exists():
   x=L(folder/'timing_complete.json');mu=statistics.mean(L(p)['seconds'] for p in files)
   cold=2*x['cold_seconds']/3600
   costs.append(dict(method=method,model=model,N=440,cold_GPUh=cold,
     window_GPUh=x['forecast_GPUh']['440'],steady_excluding_cold_GPUh=440*mu/8*2/3600,
     steady_including_cold_GPUh=cold+440*mu/8*2/3600,not_interval_bounds=True))
  if method!='PAIR':continue
  tok=AutoTokenizer.from_pretrained(base['models'][model]['model_paths']['innet'],local_files_only=True)
  data[model]=[]
  for p in files:
   r=L(p);assert r['failure'] is None;prompt=r['selected_prompt'];source=original[r['id']]
   ids=tok.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True)
   behavior=source.get('behavior',source.get('prompt'))
   assert hashlib.sha256(behavior.encode()).hexdigest()==r['source_behavior_sha256']
   ph=hashlib.sha256(prompt.encode()).hexdigest()
   data[model].append(dict(id=r['id'],prompt=prompt,behavior=behavior,input_ids=ids,
       prompt_sha256=ph,behavior_sha256=r['source_behavior_sha256']))
   rowsmeta.append(dict(id=r['id'],model=model,selected_prompt_sha256=ph,source_row_sha256=H(p),
                        early_stop=r['call_counts']['target']<3,
                        fallback=ph==r['source_behavior_sha256']))
  data[model].sort(key=lambda r:(len(r['input_ids']),hashlib.sha256(('20261240:'+str(r['id'])).encode()).hexdigest()))
save(D/'inputs.private.json',data)
save(D/'plan.json',dict(utc_frozen=utc(),worker_sha256=H(T/'u300_pair_alpha0_replay.py'),
    inputs_sha256=H(D/'inputs.private.json'),numerical_parent_sha256=H(U/'ready_generation_plan.json'),
    generation_cap=2400,do_sample=False,B={'llama':8,'qwen':4},N_unique=20,
    engineering_reference_generations=20,read_scope='SORRY alpha0 early-stop diagnostic only',rows=rowsmeta))
save(U/'search_fallback_metadata.json',dict(utc=utc(),rows=fallback,labels_read=False))
save(U/'search_cost_window_vs_steady.json',dict(utc=utc(),rows=costs,selection_basis='window remains unchanged',
    caveat='Single concurrent window; steady formula ignores contention change and tail effects; not bounds'))
commit=publish([Path(__file__),T/'u300_pair_alpha0_replay.py',D/'plan.json',
        U/'search_fallback_metadata.json',U/'search_cost_window_vs_steady.json'],
        'Bind independent PAIR alpha0 replay inputs and report hash-only fallback and two cost scenarios')
receipt=D/'publication.json';save(receipt,dict(utc=utc(),published=True,commit=commit))
C=U/'ready_queue_catalog.json';cat=L(C)
task=dict(id='PAIR_alpha0_independent_replay_v1',priority=9,site='innet',gpus=[3],kind='alpha0_replay_diagnostic',yieldable=False,
  argv=['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/u300_pair_alpha0_replay.py'],
  requires=[dict(path=str(receipt.relative_to(R)),key='published',value=True)])
score=dict(id='score_PAIR_alpha0_diagnostic',priority=6,site='innet',gpus=[0],kind='cache_only_alpha0_diagnostic_scoring',yieldable=False,
  argv=['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/u300_score_cache_worker.py','SORRY','PAIR_alpha0_diagnostic'],
  requires=[dict(path=str((D/'complete.json').relative_to(R)))])
cat['tasks'] += [task,score];save(C,cat)
print(json.dumps(dict(commit=commit,plan_sha256=H(D/'plan.json'),fallback=fallback,cost=costs)))
