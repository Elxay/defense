"""Read-only job heartbeat snapshot for both nodes; no output text is read."""
from pathlib import Path
import json,datetime,subprocess,os,shlex
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round9';now=datetime.datetime.now(datetime.timezone.utc)
rows=[]
def take(host,files):
 for name,d in files.items():
  if name in ['pipeline_live.json','repeat_controller_live.json']or name.endswith('_live.json'):
   stamp=datetime.datetime.fromisoformat(d['utc']);row=dict(host=host,file=name,pid=d.get('pid'),GPU=d.get('physical_gpu',d.get('physical_gpus')),phase=d.get('phase'),n=d.get('n',d.get('step')),total=d.get('total',d.get('total_steps')),seconds_per_item=d.get('seconds_per_item'),seconds_per_step=d.get('seconds_per_step'),heartbeat_age_seconds=round((now-stamp).total_seconds(),1));rows.append(row)
local={p.name:json.loads(p.read_text())for p in O.glob('*live.json')};take('innet',local)
code='from pathlib import Path;import json;p=Path("/home/dell/Def/results/audit/handoff_round9");print(json.dumps({f.name:json.loads(f.read_text())for f in p.glob("generate_*live.json")}))'
try:take('node01',json.loads(subprocess.check_output(['ssh','node01','python3','-c',shlex.quote(code)],text=True,timeout=15)))
except Exception as e:rows.append(dict(host='node01',read_error=str(e)))
result=dict(utc=now.isoformat(),JST=(now+datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S'),rows=rows);p=O/'status_latest.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(result,indent=2)+'\n');q.replace(p);print(json.dumps(result,indent=2))
