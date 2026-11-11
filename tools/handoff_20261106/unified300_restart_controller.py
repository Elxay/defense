from pathlib import Path
import os,signal,json,subprocess,time,datetime,fcntl
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';lock=(R/'logs/queue_restart.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
cat=json.loads((U/'ready_queue_catalog.json').read_text());s=json.loads((U/'ready_queue/state.json').read_text());pid=s['pid'];proc=Path(f'/proc/{pid}/cmdline')
if proc.exists()and proc.read_bytes():
 cmd=proc.read_bytes().replace(b'\0',b' ').decode();assert str(R/'tools/handoff_20261106/unified300_ready_queue_')in cmd
 if 'unified300_ready_queue_v7.py'not in cmd:
  for _ in range(600):
   s=json.loads((U/'ready_queue/state.json').read_text());age=time.time()-datetime.datetime.fromisoformat(s['utc']).timestamp();w=Path(f'/proc/{pid}/wchan').read_text().strip()
   if w=='hrtimer_nanosleep'and age<20:break
   time.sleep(.1)
  else:raise RuntimeError('old controller not at safe between-dispatch point; no process stopped')
 os.kill(pid,signal.SIGTERM)
 for _ in range(600):
  if not proc.exists()or not proc.read_bytes():break
  time.sleep(.1)
 else:raise RuntimeError('graceful stop pending; no replacement controller started')
p=R/cat['controller_relative'];log=(R/('logs/'+p.stem+'.log')).open('ab');q=subprocess.Popen(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','-u',str(p)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);print('controller',q.pid,'workers untouched')
