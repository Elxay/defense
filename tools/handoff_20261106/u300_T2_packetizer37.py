from u300_schedule_prepare import *
import time,shlex,os
O=U/'followup36';O37=U/'followup37';P=L(U/'T2_processing37_registry.json');done=set()
while len(done)<len(P['cells']):
 for c in P['cells']:
  key=c['cell_id'];D=U/c['generation_root'];ready=O/'T2_processing_ready'/f'{key}.json'
  if not ready.exists() and (D/'complete.json').exists():
   assert L(D/'complete.json')['N']==440;plan=R/c['generation_plan'];assert H(plan)==c['generation_plan_sha256'];spec=L(plan)['models'][c['model']]['families'][c['family']];I=U/spec['input_file'];assert H(I)==spec['input_sha256'];by={str(r['id']):r for r in L(I)[c['model']][c['family']]};pack=[]
   for id in spec['ordered_IDs']:
    raw=by[str(id)];gp=D/'generation.private'/f'{int(id):04d}.json';z=L(gp);assert z['prompt_sha256']==raw['prompt_sha256'];response=z['result']['text'];pack.append(dict(id=int(id),model=c['model'],family=c['family'],condition=c['condition'],prompt=raw['prompt'],behavior=raw['behavior'],response=response,prompt_sha256=raw['prompt_sha256'],behavior_sha256=raw['behavior_sha256'],response_sha256=hashlib.sha256(response.encode()).hexdigest(),generation_sha256=H(gp)))
   ip=U/'language_nonzero36_inputs'/f'{key}.private.json';bp=U/'language_nonzero36_bindings'/f'{key}.json';save(ip,pack);save(bp,dict(utc=utc(),inputs_sha256=H(ip),N=440,generation_plan_sha256=H(plan),complete_sha256=H(D/'complete.json')))
   if c['site']=='node01':
    for path in [ip,bp]:
     dest='/home/dell/Def/'+str(path.relative_to(R));subprocess.run(['ssh','node01','mkdir -p '+shlex.quote(str(Path(dest).parent))],check=True,capture_output=True);subprocess.run(['scp',str(path),'node01:'+dest],check=True,capture_output=True)
   save(ready,dict(utc=utc(),ready=True,N=440,private_input_sha256=H(ip),binding_sha256=H(bp)))
  sr=O37/'T2_site_ready'/f'{key}.json'
  if ready.exists() and not sr.exists():
   ip=U/'language_nonzero36_inputs'/f'{key}.private.json';bp=U/'language_nonzero36_bindings'/f'{key}.json';assert H(ip)==L(bp)['inputs_sha256']
   if c['site']=='node01':
    for path in [ip,bp]:
     dest='/home/dell/Def/'+str(path.relative_to(R));subprocess.run(['ssh','node01','mkdir -p '+shlex.quote(str(Path(dest).parent))],check=True,capture_output=True);subprocess.run(['scp',str(path),'node01:'+dest],check=True,capture_output=True)
   save(sr,dict(utc=utc(),ready=True,site=c['site'],gpu=c['gpu'],inputs_sha256=H(ip),numeric_execution_sha256=H(U/'language_nonzero36_execution.json'),scheduling_registry_sha256=H(U/'T2_processing37_registry.json')))
  comp=U/'language_processed36'/key/'complete.json';wr=O/'T2_score_ready'/f'{key}.json'
  if comp.exists() and not wr.exists():
   W=U/'score_waves'/('language36_'+key)
   if c['site']=='node01':
    W.mkdir(parents=True,exist_ok=True)
    for n in ['inputs.private.json','manifest.json']:subprocess.run(['scp','node01:/home/dell/Def/results/audit/unified300/score_waves/'+W.name+'/'+n,str(W/n)],check=True,capture_output=True)
   assert H(W/'inputs.private.json')==L(W/'manifest.json')['inputs_sha256'];save(wr,dict(utc=utc(),ready=True,N=440,manifest_sha256=H(W/'manifest.json'),cache_only=True,no_nonzero_labels_read=True));done.add(key)
  elif wr.exists():done.add(key)
 save(O37/'T2_packetizer_live.json',dict(utc=utc(),PID=os.getpid(),translated_cells=len(done),N_cells=len(P['cells']),no_judge_labels_read=True));time.sleep(20)
