"""Recover only validated, fully generated alpha0 groups after a packaging-only failure."""
from u300_schedule_prepare import *
import time,os
O=U/'followup38';P=O/'replay_execution.json';specs=L(P)['groups'];done=set()
while len(done)<len(specs):
 state=L(U/'ready_queue/state.json')['tasks']
 for c in specs:
  name=c['group'];D=O/'replays'/name
  if (D/'complete.json').exists():done.add(name);continue
  if name=='TAP_qwen_first78':continue
  job=state.get('replay38_'+name,{});ex=job.get('exit');folder=U/'queue_jobs'/job.get('job_dir','NOT_STARTED')
  if not ex or ex.get('returncode')!=1:continue
  log=(folder/'execution.log').read_text(errors='replace');assert 'TypeError: can only concatenate str (not "list") to str' in log and "'order38_'+group" in log,'Only the identified packaging error is recoverable'
  rows=L(D/'inputs.private.json');assert H(D/'inputs.private.json')==L(D/'inputs_manifest.json')['inputs_sha256'];assert len(rows)==c['N'];gate=L(D/'zero20.json');assert gate['passed'];ms=[L(p) for p in (D/'metrics').glob('*.json')];assert sum(x['rows'] for x in ms)==len(rows);pack=[]
  for r in rows:
   p=D/'generation.private'/f"{r['id']:04d}.json";z=L(p);assert z['plan_sha256']==H(P) and z['prompt_sha256']==r['prompt_sha256'] and z['behavior_sha256']==r['behavior_sha256'] and z['search_source_sha256']==r['search_source_sha256'];result=z['result'];assert result['injection_count']==1 and result['rho_runtime']==0 and hashlib.sha256(result['text'].encode()).hexdigest()==z['full_response_sha256']
   pack.append(dict(id=r['id'],model=c['model'],family=name,condition='alpha0',prompt=r['prompt'],behavior=r['behavior'],response=result['text'],prompt_sha256=r['prompt_sha256'],behavior_sha256=r['behavior_sha256'],response_sha256=z['full_response_sha256'],generation_sha256=H(p),preprocessing_sha256=None,primary_preprocessing_INVALID=r['missing_selected_prompt_fallback']))
  W=U/'score_waves'/('order38_'+name);save(W/'inputs.private.json',pack);save(W/'manifest.json',dict(utc=utc(),N=len(rows),judges=['SORRY'],inputs_sha256=H(W/'inputs.private.json'),scope='authorized alpha0 diagnostic, packaging recovery only',original_generation_plan_sha256=H(P),CPU_recovery_sha256=H(__file__)))
  save(D/'complete.json',dict(utc=utc(),N=len(rows),generation_SHA={str(r['id']):H(D/'generation.private'/f"{r['id']:04d}.json") for r in rows},wave=W.name,generation_worker_exit=1,postprocessing_recovered=True,original_exit_unchanged=True,source_job=job['job_dir'],CPU_recovery_sha256=H(__file__),nonzero_generated=False));done.add(name)
 save(O/'packaging_recovery_live.json',dict(utc=utc(),pid=os.getpid(),completed_groups=len(done),total_groups=len(specs),GPU_inference=False,labels_read=False));time.sleep(5)
