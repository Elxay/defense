"""Bounded project ready queue +15min idle alerts; no outcome aggregation or external messages."""
from pathlib import Path
import json,subprocess,fcntl,hashlib,datetime,time,os,shlex,signal,threading
stop_event=threading.Event();signal.signal(signal.SIGTERM,lambda *args:stop_event.set())
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';Q=U/'ready_queue';Q.mkdir(exist_ok=True);C=U/'ready_queue_catalog.json';T=R/'tools/handoff_20261106';lock=(R/'logs/unified300_ready_queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def L(p):return json.loads(Path(p).read_text())
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(o,indent=2)+'\n');q.replace(p)
def remote(code):return subprocess.run(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(code)],capture_output=True,text=True,check=True).stdout
catalog=L(C);assert H(__file__)==catalog['controller_sha256'];assert H(T/'unified300_queue_runner.py')==catalog['runner_sha256'];previous=[p for p in [Q/'state.json',Q/'task_checkpoint.json']if p.exists()]
state=L(max(previous,key=lambda p:p.stat().st_mtime)).get('tasks',{})if previous else{}
saved_definitions=L(Q/'active_task_definitions.json').get('tasks',{})if(Q/'active_task_definitions.json').exists()else{}
archived={z['task']['id']:z['task']for z in catalog.get('retired_prelaunch_tasks',[])if isinstance(z,dict)and 'task'in z}
known={t['id']:t for t in catalog['tasks']}
for tid,s in state.items():
 if s.get('state')=='running'and tid not in known:
  definition=saved_definitions.get(tid,archived.get(tid))
  if definition is None:raise RuntimeError('active lease definition unavailable: '+tid)
  catalog['tasks'].append(definition);known[tid]=definition
for d in (U/'queue_jobs').glob('*'):
 p=d/'descriptor.json'
 if not p.exists():continue
 x=L(p);tid=x['task_id'];attempt=int(d.name.rsplit('__',1)[1])
 if tid in known and attempt>state.get(tid,{}).get('attempt',0):state[tid]=dict(state='running',site=x['site'],gpus=x['gpus'],job_dir=d.name,attempt=attempt,runner_pid=None,started_utc=datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),priority=known[tid]['priority'],recovered_from_descriptor=True)
def restore_idle_watch(prior):
 stamp=datetime.datetime.fromisoformat(prior['utc']).timestamp()if prior.get('utc')else time.time()
 starts=prior.get('idle_started_unix',{k:stamp-age for k,age in prior.get('idle_seconds',{}).items()})
 alerts=prior.get('last_alert_unix',{})
 return {k:float(v)for k,v in starts.items()if k!='innet:1'},{k:float(v)for k,v in alerts.items()if k!='innet:1'}
watch=L(Q/'state.json')if(Q/'state.json').exists()else{}
idle,alerted=restore_idle_watch(watch);site_roots={'innet':R,'node01':Path('/home/dell/Def')}
def snapshot():
 code="""import json,subprocess,pathlib
rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,uuid','--format=csv,noheader,nounits'],text=True).strip().splitlines();procs=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip().splitlines();busy={r.split(',')[0].strip()for r in procs if r.strip()};g=[]
for r in rows:
 a,b,c=map(str.strip,r.split(','));g.append(dict(gpu=int(a),memory_MiB=int(b),compute_busy=c in busy))
root=pathlib.Path(ROOT);exits={p.parent.name:json.loads(p.read_text())for p in (root/'results/audit/unified300/queue_jobs').glob('*/exit.json')}
alive={}
for p in (root/'results/audit/unified300/queue_jobs').glob('*/status.json'):
 z=json.loads(p.read_text());pid=z['runner_pid'];cmd=pathlib.Path('/proc')/str(pid)/'cmdline'
 try:raw=cmd.read_bytes();alive[p.parent.name]=b'unified300_queue_runner.py'in raw and p.parent.name.encode()in raw
 except OSError:alive[p.parent.name]=False
print(json.dumps(dict(gpus=g,exits=exits,runner_alive=alive)))"""
 all={}
 for site,root in site_roots.items():
  text=code.replace('ROOT',repr(str(root)))
  raw=subprocess.check_output(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','-c',text],text=True)if site=='innet'else remote(text)
  all[site]=json.loads(raw)
 return all
def prereqs(task):
 for x in task.get('requires',[]):
  p=R/x['path']
  if not p.exists():return False
  if x.get('sha256')and H(p)!=x['sha256']:return False
  if 'key'in x:
   z=L(p)
   for key in x['key'].split('.'):z=z.get(key)if isinstance(z,dict)else None
   if z!=x['value']:return False
 return True
def deploy(task,folder):
 previous=state.get(task['id'],{})
 if previous.get('last_checkpoint_relative'):
  cp=R/previous['last_checkpoint_relative'];assert H(cp)==previous['last_checkpoint_sha256'];expected=L(cp)['files_sha256']
  if task['site']=='innet':assert all(H(R/p)==h for p,h in expected.items()),'resume checkpoint changed'
  else:
   verify="from pathlib import Path;import hashlib;r=Path('/home/dell/Def');e="+repr(expected)+";assert all(hashlib.sha256((r/p).read_bytes()).hexdigest()==h for p,h in e.items()),'resume checkpoint changed'"
   subprocess.run(['ssh','node01','/data/ray/env/bin/python','-'],input=verify,text=True,check=True,capture_output=True)
 definitions=L(Q/'active_task_definitions.json').get('tasks',{})if(Q/'active_task_definitions.json').exists()else{};definitions[task['id']]=task;save(Q/'active_task_definitions.json',dict(utc=utc(),tasks=definitions))
 journal=Q/'deployments'/(folder.name+'.json');save(journal,dict(utc=utc(),phase='staging',task_id=task['id'],site=task['site']))
 root=site_roots[task['site']];entry=dict(task_id=task['id'],site=task['site'],gpus=task['gpus'],argv=[a.replace('{ROOT}',str(root)) for a in task['argv']],runner_sha256=catalog['runner_sha256'],catalog_sha256=H(C));save(folder/'descriptor.json',entry)
 if task['site']=='node01':
  for rel in catalog['node_deploy_files']:
   dest=root/rel;subprocess.run(['ssh','node01','mkdir -p '+shlex.quote(str(dest.parent))],check=True,capture_output=True);subprocess.run(['scp',str(R/rel),'node01:'+str(dest)],check=True,capture_output=True)
  remote_dir=root/'results/audit/unified300/queue_jobs'/folder.name;subprocess.run(['ssh','node01','mkdir -p '+str(remote_dir)],check=True,capture_output=True);subprocess.run(['scp',str(folder/'descriptor.json'),'node01:'+str(remote_dir/'descriptor.json')],check=True,capture_output=True)
  command='nohup /data/ray/env/bin/python '+str(root/'tools/handoff_20261106/unified300_queue_runner.py')+' '+str(root)+' '+str(remote_dir/'descriptor.json')+' > '+str(remote_dir/'runner.log')+' 2>&1 < /dev/null & echo $!';pid=subprocess.check_output(['ssh','node01',command],text=True).strip()
 else:
  log=(folder/'runner.log').open('a');p=subprocess.Popen(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(T/'unified300_queue_runner.py'),str(R),str(folder/'descriptor.json')],stdout=log,stderr=log,start_new_session=True);pid=p.pid
 save(journal,dict(utc=utc(),phase='launched',runner_pid=str(pid),task_id=task['id'],site=task['site']))
 return str(pid)
def merge_active_definitions(current, requested, states):
 oldmap={t['id']:t for t in current['tasks']}
 newmap={t['id']:t for t in requested['tasks']}
 pins=[]
 for tid, status in states.items():
  if status.get('state')!='running':continue
  if tid not in oldmap:raise RuntimeError('missing immutable definition for active lease '+tid)
  if newmap.get(tid)!=oldmap[tid]:
   newmap[tid]=oldmap[tid];pins.append(tid)
 return {**requested,'tasks':list(newmap.values())},pins
while True:
 try:
  newer=L(C)
  if newer!=catalog:
   assert newer['controller_sha256']==H(__file__)and newer['runner_sha256']==catalog['runner_sha256']
   catalog,pins=merge_active_definitions(catalog,newer,state)
   save(Q/'active_catalog_pins.json',dict(utc=utc(),requested_sha256=H(C),active_pinned_task_ids=pins))
  snap=snapshot();now=time.time();running={(site,g):tid for tid,s in state.items()if s['state']=='running'for site in [s['site']]for g in s['gpus']}
  for task in catalog['tasks']:
   tid=task['id'];s=state.get(tid)
   if not s or s['state']!='running':continue
   ex=snap[task['site']]['exits'].get(s['job_dir'])
   if not ex and s['job_dir']in snap[task['site']]['runner_alive']and not snap[task['site']]['runner_alive'][s['job_dir']]:
    ex=dict(returncode=80,utc=utc(),reason='registered runner no longer alive; no automatic retry')
   if not ex and s['job_dir']not in snap[task['site']]['runner_alive']and now-datetime.datetime.fromisoformat(s['started_utc']).timestamp()>90:
    ex=dict(returncode=81,utc=utc(),reason='runner status never appeared; preserve descriptor and block automatic retry')
   if ex:
    s.update(state='done'if ex['returncode']==0 else'pending'if ex['returncode']==75 else'failed',exit=ex,finished_utc=utc())
    if task.get('sync_relpath')and task['site']=='node01':
     rel=task['sync_relpath'];(R/rel).mkdir(parents=True,exist_ok=True);subprocess.run(['rsync','-a','node01:/home/dell/Def/'+rel+'/',str(R/rel)+'/'],check=True,capture_output=True)
    if ex['returncode']==75 and task.get('yieldable'):
     root=R/task['sync_relpath']if task.get('sync_relpath')else U/'ready_generated'/task['argv'][2]/task['argv'][3]/task['argv'][4]
     records={str(p.relative_to(R)):H(p)for p in(root/'generation.private').glob('*.json')};cp=Q/'checkpoints'/(s['job_dir']+'.json');save(cp,dict(utc=utc(),captured_after_yield_utc=ex['utc'],N=len(records),files_sha256=records,task_id=task['id']));s['last_checkpoint_relative']=str(cp.relative_to(R));s['last_checkpoint_sha256']=H(cp)
  save(Q/'task_checkpoint.json',dict(utc=utc(),tasks=state))
  running={(s['site'],g):tid for tid,s in state.items()if s['state']=='running'for g in s['gpus']}
  ready=[];blocked=[]
  for task in catalog['tasks']:
   status=state.get(task['id'],{}).get('state','pending')
   if status not in ['pending']:continue
   (ready if prereqs(task)else blocked).append(task)
  ready.sort(key=lambda t:(t['priority'],t['id']))
  reservations={}
  for gang in ready:
   if len(gang['gpus'])<2:continue
   site=gang['site'];managed_or_free=all((site,n)in running or any(g['gpu']==n and not g['compute_busy']and g['memory_MiB']<2000 for g in snap[site]['gpus'])for n in gang['gpus'])
   if managed_or_free:
    for n in gang['gpus']:reservations.setdefault((site,n),(gang['priority'],gang['id']))
  for task in ready:
   if stop_event.is_set():break
   site=task['site']
   if site=='innet'and task['id'].startswith('main_'):
    model=task['id'].split('_',2)[1];slots=catalog['compatible_innet_slots'][model];free=[n for n in slots if(site,n)not in running and any(g['gpu']==n and not g['compute_busy']and g['memory_MiB']<2000 for g in snap[site]['gpus'])]
    if free:
     chosen=free[0];task={**task,'gpus':[chosen],'argv':task['argv'][:-1]+[str(chosen)]}
   if site=='node01'and task['kind']=='alpha0_family_generate'and task.get('yieldable'):
    free=[n for n in catalog['compatible_node_language_slots']if(site,n)not in running and (site,n)not in reservations and any(g['gpu']==n and not g['compute_busy']and g['memory_MiB']<2000 for g in snap[site]['gpus'])]
    if free:
     chosen=free[0];task={**task,'gpus':[chosen],'argv':task['argv'][:-1]+[str(chosen)]}
   if any((site,n)in reservations and reservations[(site,n)][0]<task['priority']for n in task['gpus']):continue
   resources=[next(g for g in snap[site]['gpus']if g['gpu']==n)for n in task['gpus']];busy=[running.get((site,n))for n in task['gpus']]
   if any(busy)or any(g['compute_busy']or g['memory_MiB']>=2000 for g in resources):
    for tid in [x for x in busy if x]:
     old=next(t for t in catalog['tasks']if t['id']==tid)
     if old.get('yieldable')and old['priority']>task['priority']:
      job=state[tid]['job_dir'];p=site_roots[site]/'results/audit/unified300/queue_jobs'/job/'yield.request'
      if site=='innet':p.touch()
      else:subprocess.run(['ssh','node01','touch '+str(p)],check=True,capture_output=True)
    continue
   attempt=state.get(task['id'],{}).get('attempt',0)+1;job=task['id']+'__'+str(attempt);folder=U/'queue_jobs'/job;folder.mkdir(parents=True,exist_ok=False);pid=deploy(task,folder);state[task['id']]={**state.get(task['id'],{}),**dict(state='running',site=site,gpus=task['gpus'],runner_pid=pid,job_dir=job,attempt=attempt,started_utc=utc(),priority=task['priority'])}
   save(Q/'task_checkpoint.json',dict(utc=utc(),tasks=state))
   for n in task['gpus']:running[(site,n)]=task['id']
  for site,s in snap.items():
   for g in s['gpus']:
    key=site+':'+str(g['gpu'])
    if site=='innet'and g['gpu']==1:continue
    isidle=not g['compute_busy']and g['memory_MiB']<2000
    if isidle:
     idle.setdefault(key,now);age=now-idle[key]
     if not catalog.get('independent_watchdog',False)and age>=900 and now-alerted.get(key,0)>=900:
      event=dict(utc=utc(),gpu=key,idle_seconds=age,ready_task_ids=[t['id']for t in ready],blocked_task_ids=[t['id']for t in blocked],reserved_by_job=running.get((site,g['gpu'])),delivery='local alerts.jsonl and controller stdout; Windows frontend blocked by script policy, no bypass')
      with (Q/'alerts.jsonl').open('a')as f:f.write(json.dumps(event)+'\n')
      print('IDLE_GPU_ALERT',json.dumps(event),flush=True);alerted[key]=now
    else:idle.pop(key,None);alerted.pop(key,None)
  save(Q/'state.json',dict(utc=utc(),pid=os.getpid(),catalog_sha256=H(C),tasks=state,ready=[t['id']for t in ready],blocked=[t['id']for t in blocked],idle_seconds={k:now-v for k,v in idle.items()},idle_started_unix=idle,last_alert_unix=alerted,gang_reservations={f'{site}:{g}':v for(site,g),v in reservations.items()},snapshots=snap,exclusion='innetGPU1 never dispatch/idle-alert eligible',main_labels_or_effects_read=False))
 except Exception as e:
  save(Q/'controller_health.json',dict(utc=utc(),pid=os.getpid(),error_type=type(e).__name__,last_success_utc=L(Q/'state.json').get('utc')if(Q/'state.json').exists()else None))
  with (Q/'controller_errors.jsonl').open('a')as f:f.write(json.dumps(dict(utc=utc(),type=type(e).__name__,reason=str(e)[:1000]))+'\n')
 if stop_event.is_set():break
 stop_event.wait(30)
