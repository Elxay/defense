from pathlib import Path
import os,subprocess,time,json,datetime
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round9'
def state(phase,**kw):
 p=O/'repeat_controller_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),phase=phase,**kw),indent=2));q.replace(p)
for runid in ['repeatA_s3','repeatB_s3']:
 script=f'source /data/HZX/Def/night/launch.sh\ncd /data/HZX/Def\nexec 8>>logs/idle_gpu2.lock\nflock 8\nexport DEVICE=cuda:2\nwhile ! wait_gpu "$DEVICE"; do sleep 30; done\nlaunch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 python -u tools/handoff_20261106/round9_train.py --mode control --seed 3 --physical-card 2 --run-id {runid}\n'
 with(B/f'logs/round9_{runid}.log').open('ab')as log:
  p=subprocess.Popen(['bash','-c',script],cwd=B,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'DSH_OWNER':str(B)})
  while p.poll()is None:state('running_repeat',run_id=runid,wrapper_pid=p.pid);time.sleep(10)
  if p.returncode!=0:state('failed',run_id=runid,returncode=p.returncode);raise SystemExit(p.returncode)
state('repeats_generated_waiting_hf_judge')
