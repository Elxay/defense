
from pathlib import Path
import subprocess,time,json,datetime,hashlib
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round3';o.mkdir(exist_ok=True)
cmd=['ssh','node01','DSH_OWNER=/data/HZX/Def python3 /home/dell/Def/tools/handoff_20261106/parallel_launcher.py']
p=subprocess.Popen(cmd)
while True:
 code="import json,os;from pathlib import Path;b=Path('/home/dell/Def/results/audit');print(json.dumps({tag:len(json.loads((b/f'WJB_{tag}.json').read_text())) if (b/f'WJB_{tag}.json').exists() else 0 for tag in ['old_s3_a1.0','old_s4_a1.0','rand1']}))"
 r=subprocess.run(['ssh','node01','python3 -'],input=code,text=True,capture_output=True,check=True);counts=json.loads(r.stdout)
 (o/'parallel_progress.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':counts},indent=2))
 if all(n==300 for n in counts.values()):break
 if p.poll() is not None and p.returncode:raise RuntimeError('parallel generation failed; inspect logs')
 time.sleep(45)
for tag in counts:
 subprocess.run(['rsync','-a',f'node01:/home/dell/Def/results/audit/WJB_{tag}.json',str(b/'results/audit')+'/'],check=True)
print('SYNC_DONE',flush=True)
# Judge launcher is prepared separately; it checks available memory and gate before judging.
subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(b/'tools/handoff_20261106/judge_parallel_innet.py')],check=True)
