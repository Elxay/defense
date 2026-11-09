"""Wait for the PAIR GPU stage, then collect Qwen native baselines, without training."""
from pathlib import Path
import datetime,fcntl,json,os,subprocess,time
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287';PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python'
def now():return datetime.datetime.now(datetime.timezone.utc)
def pulse(phase,**kw):
 p=O/'qwen_admission_queue_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps({'utc':now().isoformat(),'pid':os.getpid(),'phase':phase,'training_started':False,**kw},indent=2)+'\n');q.replace(p)
def main():
 with(R/'logs/crossmodel287_admission_queue.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while now()<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc):
   if not(R/'results/audit/pair500/lease_priority/PAIR_GPU_complete.json').exists():pulse('waiting_PAIR_GPU_complete');time.sleep(30);continue
   if(O/'qwen_native_selection_complete.json').exists():
    p=O/'qwen_refusal_admission/sample_manifest.json'
    if not p.exists():
     script='cd /data/HZX/Def\nsource night/launch.sh\nexport NOGPU=1 DEVICE=cpu\nlaunch_job '+PY+' /data/HZX/Def/tools/handoff_20261106/crossmodel287_sample_refusal_admission.py qwen\n'
     with(R/'logs/crossmodel287_qwen_sampling.log').open('ab',buffering=0)as f:code=subprocess.run(['bash','-s'],input=script,text=True,stdout=f,stderr=subprocess.STDOUT).returncode
     if code: pulse('sample_preparation_failed',exit_code=code);return
    pulse('waiting_model_review_before_training');return
   pulse('attempting_idle_GPU0_native_alpha0')
   script='cd /data/HZX/Def\nsource night/launch.sh\nexport CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 USE_TF=0 USE_FLAX=0 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True\nexec 8>>logs/idle_gpu0.lock\nflock -n 8 || exit 75\nwait_gpu cuda:0 || exit 75\nlaunch_job '+PY+' /data/HZX/Def/tools/handoff_20261106/crossmodel287_native_baseline.py\n'
   with(R/'logs/crossmodel287_qwen_native_baseline.log').open('ab',buffering=0)as f:code=subprocess.run(['bash','-s'],input=script,text=True,stdout=f,stderr=subprocess.STDOUT).returncode
   if code not in [0,75]:pulse('native_baseline_failed_preserve_rows',exit_code=code);return
   time.sleep(15)
  pulse('authorization_ended_resume_requires_new_window')
if __name__=='__main__':main()
