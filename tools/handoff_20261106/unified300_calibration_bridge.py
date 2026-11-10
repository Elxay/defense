from pathlib import Path
import json,datetime,hashlib,os,subprocess,time
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';D=U/'calibration_S1a';ND='/home/dell/Def/results/audit/unified300/calibration_S1a_WG'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
plan=load(U/'S1a_manifest.json');assert sha(__file__)==plan['code_sha256']['tools/handoff_20261106/unified300_calibration_bridge.py'];cal={r['id']:r for r in load(U/'calibration700.private.json')};sent=set();received=set();start=time.monotonic();tasks=[(k,c['id'])for c in plan['calibration_conditions']for k in ['llama','qwen']]
while len(received)<44:
 for model,condition in tasks:
  task_id=model+'__'+condition;folder=D/model/condition;done=folder/'generation_complete.json'
  if task_id not in sent and done.exists():
   marker=load(done);assert marker['manifest_sha256']==sha(U/'S1a_manifest.json');rows=[]
   for k in plan['calibration_IDs']:
    f=folder/'generation.private'/(k+'.json');assert sha(f)==marker['record_sha256'][k];v=load(f);rows.append(dict(id=k,prompt=cal[k]['prompt'],response=v['result']['text'],generation_record_sha256=sha(f)))
   p=D/'transfer.private'/(task_id+'.json')
   if p.exists():
    payload=load(p);assert payload['manifest_sha256']==sha(U/'S1a_manifest.json')and payload['generation_receipt_sha256']==sha(done);assert payload['rows']==rows
   else:
    payload=dict(task_id=task_id,utc=utc(),manifest_sha256=sha(U/'S1a_manifest.json'),rows=rows,rows_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),generation_receipt_sha256=sha(done));save(p,payload)
   subprocess.run(['scp',str(p),'node01:'+ND+'/incoming.private/'+task_id+'.part'],check=True);subprocess.run(['ssh','node01','mv '+ND+'/incoming.private/'+task_id+'.part '+ND+'/incoming.private/'+task_id+'.json'],check=True);sent.add(task_id)
  if task_id in sent and task_id not in received:
   check=subprocess.run(['ssh','node01','test -f '+ND+'/tasks/'+task_id+'/complete.json'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   if check.returncode==0:
    out=folder/'WG_cache';out.mkdir(exist_ok=True)
    for n in ['bundle.private.json','complete.json']:subprocess.run(['scp','node01:'+ND+'/tasks/'+task_id+'/'+n,str(out/n)],check=True)
    marker=load(out/'complete.json');assert sha(out/'bundle.private.json')==marker['bundle_sha256'];assert marker['N']==700;received.add(task_id)
 save(D/'bridge_live.json',dict(utc=utc(),pid=os.getpid(),sent_tasks=len(sent),received_tasks=len(received),total44=44,condition_effects_aggregated=False))
 if time.monotonic()-start>30*3600:raise RuntimeError('30h wait; incomplete grid not selected')
 time.sleep(10)
save(D/'all_calibration_cache_complete.json',dict(utc=utc(),tasks=44,rows=30800,manifest_sha256=sha(U/'S1a_manifest.json'),condition_effects_aggregated=False))
