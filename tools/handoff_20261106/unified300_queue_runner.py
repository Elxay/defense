"""Audited queue execution with shared flock + existing wait_gpu/launch_job."""
from pathlib import Path
import os,sys,json,hashlib,fcntl,subprocess,datetime,time
root=Path(sys.argv[1]);desc=Path(sys.argv[2]);x=json.loads(desc.read_text());directory=desc.parent
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==x['runner_sha256'];assert x['site']in['innet','node01'];assert not(x['site']=='innet'and 1 in x['gpus']);fds=[]
def save(name,o):p=directory/name;q=p.with_suffix('.tmp');q.write_text(json.dumps(o,indent=2)+'\n');q.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
 for g in sorted(x['gpus']):
  f=(root/'logs'/f'idle_gpu{g}.lock').open('a');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fds.append(f)
 helper=root/('night/launch.sh'if x['site']=='innet'else'tools/handoff_20261106/node01_launch_round9.sh');checks='; '.join('wait_gpu cuda:'+str(g) for g in sorted(x['gpus']));shell='set -euo pipefail; source '+str(helper)+'; '+checks+'; launch_job "$@"'
 env=os.environ.copy();env.update(DEF_ROOT=str(root),DEF_SITE=x['site'],DEF_LEASE_DIR=str(directory),DEVICE='cuda:'+str(x['gpus'][0]),CUDA_VISIBLE_DEVICES=','.join(map(str,x['gpus'])),PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True');env.pop('NOGPU',None)
 log=(directory/'worker.log').open('a');start=time.monotonic();save('status.json',dict(utc=utc(),runner_pid=os.getpid(),state='running',task_id=x['task_id'],gpus=x['gpus'],catalog_sha256=x['catalog_sha256']))
 c=subprocess.Popen(['bash','-c',shell,'defense-ready-job',*x['argv']],env=env,stdout=log,stderr=log);save('child.json',dict(utc=utc(),wrapper_pid=c.pid));rc=c.wait();save('exit.json',dict(utc=utc(),returncode=rc,resident_seconds=time.monotonic()-start,task_id=x['task_id'],gpus=x['gpus']))
except Exception as e:save('exit.json',dict(utc=utc(),returncode=79,error_type=type(e).__name__,reason=str(e)[:300],task_id=x['task_id']))
finally:
 for f in fds:f.close()
