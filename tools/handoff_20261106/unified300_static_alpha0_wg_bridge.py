from pathlib import Path
import json,datetime,hashlib,os,subprocess,time
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';D=U/'static_alpha0';ND='/home/dell/Def/results/audit/unified300/static_alpha0_WG'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
plan=load(U/'static_alpha0_WG_execution_plan.json');assert sha(__file__)==plan['code_sha256']['tools/handoff_20261106/unified300_static_alpha0_wg_bridge.py'];assert sha(U/'static_alpha0_inputs.private.json')==plan['private_generation_inputs_sha256'];inputs=load(U/'static_alpha0_inputs.private.json');sent=set();received=set();unavailable=set();start=time.monotonic();tasks=plan['tasks'];expected=len(tasks)
while len(received)+len(unavailable)<expected:
 for task in tasks:
  key,family,name=task['model'],task['family'],task['id'];folder=D/key/family;done=folder/'generation_complete.json'
  blocked=folder/'execution_blocked.json'
  if name not in unavailable and blocked.exists()and not done.exists():
   p=D/'WG_unavailable_tasks'/(name+'.json');save(p,dict(utc=utc(),task_id=name,reason='generation execution gate failed or incomplete family',generation_blocked_sha256=sha(blocked),no_harmless_default=True));subprocess.run(['scp',str(p),'node01:'+ND+'/unavailable_tasks/'+name+'.json'],check=True);unavailable.add(name)
  if name in unavailable:continue
  if name not in sent and done.exists():
   marker=load(done);assert marker['execution_plan_sha256']==plan['parent_generation_plan_sha256'];raw={r['id']:r for r in inputs[key][family]};rows=[]
   for k in plan['static_IDs']:
    f=folder/'generation.private'/f'{k:04d}.json';assert sha(f)==marker['record_sha256'][str(k)];v=load(f);r=raw[k];rows.append(dict(id=k,prompt=r['prompt'],response=r['prefill']+v['result']['text'],v2_response=v['result']['text'],generation_record_sha256=sha(f)))
   p=D/'WG_transfer.private'/(name+'.json')
   if p.exists():payload=load(p);assert payload['manifest_sha256']==sha(U/'static_alpha0_WG_execution_plan.json')and payload['generation_receipt_sha256']==sha(done);assert payload['rows']==rows
   else:
    payload=dict(task_id=name,model=key,family=family,condition='alpha0',utc=utc(),manifest_sha256=sha(U/'static_alpha0_WG_execution_plan.json'),rows=rows,rows_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),generation_receipt_sha256=sha(done));save(p,payload)
   subprocess.run(['scp',str(p),'node01:'+ND+'/incoming.private/'+name+'.part'],check=True);subprocess.run(['ssh','node01','mv '+ND+'/incoming.private/'+name+'.part '+ND+'/incoming.private/'+name+'.json'],check=True);sent.add(name)
  if name in sent and name not in received:
   ready=subprocess.run(['ssh','node01','test -f '+ND+'/tasks/'+name+'/complete.json'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   if ready.returncode==0:
    out=folder/'WG_cache';out.mkdir(exist_ok=True)
    for n in ['bundle.private.json','complete.json']:subprocess.run(['scp','node01:'+ND+'/tasks/'+name+'/'+n,str(out/n)],check=True)
    complete=load(out/'complete.json');assert sha(out/'bundle.private.json')==complete['bundle_sha256']and complete['N']==440;received.add(name)
 save(D/'WG_bridge_live.json',dict(utc=utc(),pid=os.getpid(),sent_tasks=len(sent),received_tasks=len(received),total=expected,unavailable_tasks=len(unavailable),main_effects_aggregated=False))
 if time.monotonic()-start>30*3600:raise RuntimeError('30h limit; incomplete main caches remain unread')
 time.sleep(10)
save(D/'all_WG_alpha0_caches_complete.json',dict(utc=utc(),tasks=len(received),rows=len(received)*440,unavailable_tasks=len(unavailable),execution_plan_sha256=sha(U/'static_alpha0_WG_execution_plan.json'),main_effects_aggregated=False))
