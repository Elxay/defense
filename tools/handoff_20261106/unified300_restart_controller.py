from pathlib import Path
import os,signal,json,subprocess,time
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
cat=json.loads((U/'ready_queue_catalog.json').read_text());s=json.loads((U/'ready_queue/state.json').read_text());pid=s['pid'];proc=Path(f'/proc/{pid}/cmdline')
if proc.exists():
 cmd=proc.read_bytes().replace(b'\0',b' ').decode();assert str(R/'tools/handoff_20261106/unified300_ready_queue_')in cmd;os.kill(pid,signal.SIGTERM)
 for _ in range(30):
  if not proc.exists()or not proc.read_bytes():break
  time.sleep(.1)
p=R/cat['controller_relative'];log=(R/('logs/'+p.stem+'.log')).open('ab');q=subprocess.Popen(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','-u',str(p)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);print('controller',q.pid,'workers untouched')
