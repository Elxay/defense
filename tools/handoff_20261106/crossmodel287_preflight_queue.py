"""CPU dispatch for short, cooperative preflight only; no training/test jobs."""
from pathlib import Path
import datetime, fcntl, hashlib, json, os, subprocess, time
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287';PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');os.replace(q,p)
def main():
 with(R/'logs/crossmodel287_preflight_dispatch.lock').open('a')as singleton:
  fcntl.flock(singleton,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc):
   receipt=O/'qwen_asset_render_receipt.json'
   if not receipt.exists()or json.loads(receipt.read_text())['phase']!='verified':
    save(O/'preflight_queue_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'waiting_verified_assets','GPU_used':False});time.sleep(30);continue
   result=O/'qwen_preflight.json'
   if result.exists()and json.loads(result.read_text()).get('phase')=='targets_complete_no_training':
    save(O/'preflight_queue_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'complete_no_training','GPU_used':False});return
   live=R/'results/audit/pair500/lease_priority/controller_live.json';busy=False
   if live.exists():busy=any('0'in x.get('cards',[])and x.get('kind')in ['prefix','hb']for x in json.loads(live.read_text()).get('jobs',{}).values())
   if busy:
    save(O/'preflight_queue_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'waiting_PAIR_priority','GPU_used':False});time.sleep(15);continue
   script='''cd /data/HZX/Def
source night/launch.sh
export CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
exec 8>>logs/idle_gpu0.lock
flock -n 8 || exit 75
wait_gpu cuda:0 || exit 75
launch_job '''+PY+''' /data/HZX/Def/tools/handoff_20261106/crossmodel287_probe.py qwen --targets
'''
   save(O/'preflight_queue_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'attempting_idle_GPU0_lease','GPU_used':False})
   log=(R/'logs/crossmodel287_preflight_qwen.log').open('ab',buffering=0)
   p=subprocess.run(['bash','-s'],input=script,text=True,stdout=log,stderr=subprocess.STDOUT);log.close()
   if p.returncode not in [0,75]:
    save(O/'preflight_queue_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'failed_preserve_artifacts','exit_code':p.returncode,'GPU_used':False});return
   time.sleep(15)
  save(O/'preflight_queue_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'authorization_ended_resume_requires_new_window','GPU_used':False})
if __name__=='__main__':main()
