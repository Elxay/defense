"""Verify downloaded Gemma assets, then borrow an idle GPU for norm-only preflight."""
from pathlib import Path
import datetime,fcntl,json,os,subprocess,time
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287';PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(phase,**extra):
 p=O/'gemma_norm_queue_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps({'utc':utc(),'pid':os.getpid(),'phase':phase,'training_started':False,**extra},indent=2)+'\n');q.replace(p)
def run(script,logname):
 with(R/'logs'/logname).open('ab',buffering=0)as f:return subprocess.run(['bash','-s'],input=script,text=True,stdout=f,stderr=subprocess.STDOUT).returncode
def main():
 with(R/'logs/crossmodel287_gemma_norm_dispatch.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  save('verifying_assets_CPU')
  code=run('cd /data/HZX/Def\nsource night/launch.sh\nexport NOGPU=1 DEVICE=cpu USE_TF=0 USE_FLAX=0\nlaunch_job '+PY+' /data/HZX/Def/tools/handoff_20261106/crossmodel287_assets_and_render.py gemma\n','crossmodel287_gemma_assets.log')
  if code!=0:save('asset_verification_failed',exit_code=code);return
  receipt=O/'gemma_asset_render_receipt.json'
  if not receipt.exists()or json.loads(receipt.read_text())['phase']!='verified':save('waiting_complete_assets');return
  while datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc):
   p=O/'gemma_preflight.json'
   if p.exists()and json.loads(p.read_text()).get('phase')=='norm_and_donor_complete':save('norm_complete_no_training');return
   p=R/'results/audit/pair500/lease_priority/controller_live.json'
   if p.exists()and any('0'in x.get('cards',[])and x['kind']in ['prefix','hb']for x in json.loads(p.read_text()).get('jobs',{}).values()):save('waiting_PAIR_priority');time.sleep(15);continue
   save('attempting_idle_GPU0_lease')
   code=run('cd /data/HZX/Def\nsource night/launch.sh\nexport CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 USE_TF=0 USE_FLAX=0 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True\nexec 8>>logs/idle_gpu0.lock\nflock -n 8 || exit 75\nwait_gpu cuda:0 || exit 75\nlaunch_job '+PY+' /data/HZX/Def/tools/handoff_20261106/crossmodel287_probe_v2.py gemma\n','crossmodel287_gemma_norm.log')
   if code not in [0,75]:save('probe_failed_preserve_artifacts',exit_code=code);return
   time.sleep(15)
  save('authorization_ended')
if __name__=='__main__':main()
