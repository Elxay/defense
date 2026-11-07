from pathlib import Path
import os,json,fcntl,subprocess,time,datetime
B=Path('/home/dell/Def');O=B/'results/audit/handoff_round11';O.mkdir(exist_ok=True);os.environ['DSH_OWNER']=str(B)
def pulse(phase,**kw):
 p=O/'noise_B_launcher_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),host='node01',physical_gpu=0,phase=phase,n_harm=0,n_pairs=0,**kw),indent=2));q.replace(p)
lock=(B/'logs/idle_gpu0.lock').open('a')
while True:
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:pulse('waiting_original_GPU0_lease');time.sleep(10);continue
 check=subprocess.run(['bash','-c','source /home/dell/Def/tools/handoff_20261106/node01_launch_round9.sh\nwait_gpu cuda:0'],capture_output=True,text=True)
 if check.returncode==0:break
 fcntl.flock(lock,fcntl.LOCK_UN);pulse('waiting_original_wait_gpu');time.sleep(10)
cmd='source /home/dell/Def/tools/handoff_20261106/node01_launch_round9.sh\nexport DEVICE=cuda:0\nlaunch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 /data/ray/env/bin/python -u /home/dell/Def/tools/handoff_20261106/round11_noise_B_generate.py --root /home/dell/Def --seed 3 --card 0 --phase full\n'
with(B/'logs/round11_noise_B_generate.log').open('ab')as log:
 p=subprocess.Popen(['bash','-c',cmd],cwd=B,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'DSH_OWNER':str(B)})
 while p.poll()is None:pulse('generating_noise_B',wrapper_pid=p.pid);time.sleep(10)
pulse('complete'if p.returncode==0 else'failed',returncode=p.returncode)
