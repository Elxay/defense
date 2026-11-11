from pathlib import Path
import os,json,time,datetime,signal,hashlib
R=Path('/home/dell/Def');U=R/'results/audit/unified300';D=U/'AutoDAN_build'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
p=json.loads((U/'rule17_autodan_phase_read_frozen.json').read_text());deadline=datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
def owned():
 out=[]
 for z in Path('/proc').iterdir():
  if not z.name.isdigit():continue
  try:
   a=(z/'cmdline').read_bytes().split(b'\0');a=[v.decode() for v in a if v]
   if (z/'comm').read_text().strip().startswith('python') and '/home/dell/Def/tools/handoff_20261106/unified300_autodan_worker_v4.py' in a and a[-2:]==['warmup','qwen'] and z.stat().st_uid==os.getuid():out.append(int(z.name))
  except (OSError,UnicodeError):pass
 return out
save(U/'rule17_wallcap_watch_live.json',dict(utc=now(),deadline=p['deadline_utc'],pids=owned(),watcher_pid=os.getpid()))
while time.time()<deadline:time.sleep(min(5,deadline-time.time()))
files=list((D/'requests.private').glob('*.json'))+list((D/'library_versions.private').glob('*.json'))
before={str(f.relative_to(D)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
pids=owned();signals=[]
for pid in pids:os.kill(pid,signal.SIGINT);signals.append(dict(pid=pid,signal='SIGINT',utc=now()))
for _ in range(60):
 if not any(x in owned() for x in pids):break
 time.sleep(1)
for pid in pids:
 if pid in owned():os.kill(pid,signal.SIGTERM);signals.append(dict(pid=pid,signal='SIGTERM',utc=now()))
unchanged=all((D/k).exists() and hashlib.sha256((D/k).read_bytes()).hexdigest()==v for k,v in before.items())
rows=[]
for f in sorted((D/'requests.private').glob('*.json')):
 z=json.loads(f.read_text());rows.append({k:z.get(k) for k in ['utc','index','id','success','seconds','resident_GPUh','library_sha256','call_counts']})
elapsed=(time.time()-datetime.datetime.fromisoformat(p['autodan_started_utc']).timestamp())
save(U/'rule17_autodan_wallcap_receipt.json',dict(utc=now(),started_utc=p['autodan_started_utc'],deadline_utc=p['deadline_utc'],signals=signals,completed_requests=len(rows),requests=rows,prior_completed_files_unchanged=unchanged,preserved_file_count=len(before),reserved_GPUh=elapsed*2/3600,worker_remaining=owned(),unfinished_request_right_censored=True,not_fake_pilot20_complete=True))
