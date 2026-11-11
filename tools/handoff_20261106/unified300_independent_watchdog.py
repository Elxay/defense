"""Independent read-only GPU idle and scheduler-health watchdog; no job control."""
from pathlib import Path
import json, subprocess, datetime, time, os, signal, threading, fcntl
R=Path('/data/HZX/Def');Q=R/'results/audit/unified300/ready_queue'
lock=(R/'logs/unified300_independent_watchdog.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
stop=threading.Event();signal.signal(signal.SIGTERM,lambda *a:stop.set())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def alert(x):
 x={'utc':utc(),'delivery':'local watchdog_alerts.jsonl and stdout only',**x}
 with (Q/'watchdog_alerts.jsonl').open('a')as f:f.write(json.dumps(x)+'\n')
 print(json.dumps(x),flush=True)
def snapshot(site):
 prefix=[]if site=='innet'else['ssh','-o','ConnectTimeout=10','node01']
 rows=subprocess.check_output(prefix+['nvidia-smi','--query-gpu=index,memory.used,uuid','--format=csv,noheader,nounits'],text=True,timeout=20)
 procs=subprocess.check_output(prefix+['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=20)
 busy={l.split(',')[0].strip()for l in procs.splitlines()if l.strip()}
 out=[]
 for row in rows.splitlines():
  idx,mem,uuid=map(str.strip,row.split(','))
  if site=='innet'and int(idx)==1:continue
  out.append({'key':site+':'+idx,'memory_MiB':int(mem),'compute_busy':uuid in busy})
 return out
p=Q/'independent_watchdog_state.json';prior=json.loads(p.read_text())if p.exists()else{}
continuous=prior and time.time()-datetime.datetime.fromisoformat(prior['utc']).timestamp()<90
starts=prior.get('idle_started_unix',{})if continuous else{};last=prior.get('last_alert_unix',{})if continuous else{}
while not stop.is_set():
 now=time.time();errors=[];rows=[]
 for site in ['innet','node01']:
  try:rows+=snapshot(site)
  except Exception as e:
   errors.append({'site':site,'type':type(e).__name__})
   for key in list(starts):
    if key.startswith(site+':'):starts.pop(key,None)
 for g in rows:
  key=g['key']
  if not g['compute_busy']and g['memory_MiB']<2000:
   starts.setdefault(key,now)
   if now-starts[key]>=900 and now-last.get(key,0)>=900:
    alert({'kind':'idle_gpu_15min','gpu':key,'observed_idle_seconds':now-starts[key]});last[key]=now
  else:starts.pop(key,None);last.pop(key,None)
 age=None
 try:
  state=json.loads((Q/'state.json').read_text());age=now-datetime.datetime.fromisoformat(state['utc']).timestamp()
  if age>120 and now-last.get('scheduler_stale',0)>300:
   alert({'kind':'scheduler_state_stale','age_seconds':age,'scheduler_pid':state.get('pid')});last['scheduler_stale']=now
 except Exception as e:errors.append({'source':'scheduler_state','type':type(e).__name__})
 save(p,{'utc':utc(),'pid':os.getpid(),'idle_started_unix':starts,'last_alert_unix':last,'rows':rows,'errors':errors,'scheduler_age_seconds':age,'exclusion':'innet GPU1','job_control':False})
 stop.wait(30)
