from pathlib import Path
import hashlib,json
from transformers import AutoTokenizer
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
D=U/'TAP_alpha0_independent_replay';assert not (D/'plan.json').exists()
source=T/'u300_pair_alpha0_replay.py';worker=T/'u300_tap_alpha0_replay.py'
code=source.read_text().replace('PAIR','TAP');worker.write_text(code);compile(code,str(worker),'exec')
base=L(U/'ready_generation_plan.json');original={r['id']:r for r in L(U/'PAIR_pilot_inputs.private.json')}
data={};meta=[];audit=[]
for method in ['PAIR','TAP']:
 for model in ['llama','qwen']:
  folder=U/(method+'_pilot')/model;files=sorted((folder/'rows.private').glob('*.json'));assert len(files)==10
  ledger=L(folder/'call_ledger.private.json');query_count=sum(e['batch_rows'] for e in ledger if e['role']=='target')
  logged=0;details=[]
  for p in files:
   z=L(p);assert z['failure'] is None
   candidates=[c for s in z['streams'] for c in s] if method=='PAIR' else z['source_logs']
   field='score' if method=='PAIR' else 'judge_score'
   assert all(isinstance(c.get('adv_prompt'),str) and field in c for c in candidates)
   logged+=len(candidates)
   details.append(dict(id=z['id'],N_logged_candidates=len(candidates),source_record_sha256=H(p),
      candidate_hashes=[hashlib.sha256(c['adv_prompt'].encode()).hexdigest() for c in candidates],
      grades_present_for_every_logged_candidate=True))
  audit.append(dict(method=method,model=model,N_rows=10,target_query_rows=query_count,
    saved_scored_candidates=logged,details=details,
    full_all_attempts_saved=False,
    coverage='All parsed candidates delivered to target are logged; malformed attacker retries raw text absent.' if method=='PAIR' else
             'Only leaves after topic/rating pruning are saved. Pre-pruning candidates/raw parser retries are not a complete tree archive.',
    fallback_initial_score=0,original_behavior_scored_before_search=False))
  if method!='TAP':continue
  tok=AutoTokenizer.from_pretrained(base['models'][model]['model_paths']['innet'],local_files_only=True);data[model]=[]
  for p in files:
   r=L(p);prompt=r['selected_prompt'];src=original[r['id']];behavior=src.get('behavior',src.get('prompt'))
   assert hashlib.sha256(behavior.encode()).hexdigest()==r['source_behavior_sha256']
   ids=tok.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True)
   ph=hashlib.sha256(prompt.encode()).hexdigest()
   data[model].append(dict(id=r['id'],prompt=prompt,behavior=behavior,input_ids=ids,prompt_sha256=ph,behavior_sha256=r['source_behavior_sha256']))
   meta.append(dict(id=r['id'],model=model,source_row_sha256=H(p),selected_prompt_sha256=ph,
      early_stop=r['call_counts']['target']<10,fallback=ph==r['source_behavior_sha256']))
  data[model].sort(key=lambda r:(len(r['input_ids']),hashlib.sha256(('20261240:'+str(r['id'])).encode()).hexdigest()))
save(D/'inputs.private.json',data)
save(D/'plan.json',dict(utc_frozen=utc(),worker_sha256=H(worker),inputs_sha256=H(D/'inputs.private.json'),
    parent_generator_sha256=H(source),N_unique=20,B={'llama':8,'qwen':4},cap=2400,greedy=True,
    engineering_reference_generations=20,read_scope='Only TAP pilot alpha0 and direct/PAIR alpha0 comparison',
    staged_gate_plan_sha256=H(U/'search_staged_alpha0_gate_frozen.json'),rows=meta))
save(U/'search_candidate_log_coverage.json',dict(utc=utc(),rows=audit,main_nonzero_effects_read=False,
   no_reranking=True,interpretation='Fallback sentinel zero is not an evaluated direct-request score.'))
commit=publish([worker,D/'plan.json',U/'search_candidate_log_coverage.json',Path(__file__)],
               'Bind TAP independent alpha0 diagnostic and audit actual candidate-log coverage')
receipt=D/'publication.json';save(receipt,dict(utc=utc(),published=True,commit=commit))
C=U/'ready_queue_catalog.json';cat=L(C)
cat['tasks'] += [dict(id='TAP_alpha0_independent_replay_v1',priority=4,site='innet',gpus=[0],kind='alpha0_replay_diagnostic',yieldable=False,
 argv=['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/u300_tap_alpha0_replay.py'],
 requires=[dict(path=str(receipt.relative_to(R)),key='published',value=True)]),
 dict(id='score_TAP_alpha0_diagnostic',priority=3,site='innet',gpus=[0],kind='cache_only_alpha0_diagnostic_scoring',yieldable=False,
 argv=['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/u300_score_cache_worker.py','SORRY','TAP_alpha0_diagnostic'],
 requires=[dict(path=str((D/'complete.json').relative_to(R)))])]
save(C,cat)
print(json.dumps(dict(commit=commit,plan_sha256=H(D/'plan.json'),
 coverage=[{k:v for k,v in x.items() if k!='details'} for x in audit])))
