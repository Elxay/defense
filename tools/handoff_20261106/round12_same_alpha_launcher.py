"""Release original node01 slots first; respect the already queued seed3-B reference."""
import argparse,datetime,json,os,subprocess,time,fcntl
from pathlib import Path
B=Path('/home/dell/Def');O=B/'results/audit/handoff_round12';O.mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--seed',type=int,choices=[3,5],required=True);a=p.parse_args();card={3:0,5:2}[a.seed]
def pulse(phase):
 p=O/f'same_alpha_s{a.seed}_launcher_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),physical_gpu=card,phase=phase)));q.replace(p)
def status(p):
 return json.loads(p.read_text()).get('phase') if p.exists() else None
def wait_for(path,phase):
 while status(path)!='complete':
  assert status(path)!='failed'
  assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc)
  pulse(phase);time.sleep(10)
wait_for(B/f'results/audit/handoff_round9/generate_full_s{a.seed}_live.json','waiting_original_generation')
if a.seed==3:wait_for(B/'results/audit/handoff_round11/noise_B_launcher_live.json','waiting_seed3_B_priority')
with (B/f'logs/idle_gpu{card}.lock').open('a') as lock:
 while True:
  pulse('waiting_gpu_lease')
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:time.sleep(10)
 script=f'source tools/handoff_20261106/node01_launch_round9.sh\nwait_gpu cuda:{card} || exit 10\nlaunch_job env CUDA_VISIBLE_DEVICES={card} DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 /data/ray/env/bin/python -u tools/handoff_20261106/round12_same_alpha_generate.py --seed {a.seed}'
 try:
  pulse('generating');subprocess.run(['bash','-c',script],cwd=B,env={**os.environ,'DSH_OWNER':str(B)},check=True);pulse('complete')
 except BaseException:pulse('failed');raise
