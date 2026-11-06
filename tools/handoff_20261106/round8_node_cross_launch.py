from pathlib import Path
import os,subprocess,fcntl,time
B=Path('/home/dell/Def')
def launch_job():
 lock=(B/'logs/idle_gpu2.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
 while int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits','-i','2'],text=True).strip())>2000:time.sleep(30)
 env={**os.environ,'CUDA_VISIBLE_DEVICES':'2','DSH_OWNER':'/data/HZX/Def','USE_TF':'0','USE_FLAX':'0','HF_HUB_OFFLINE':'1'};args=['/data/ray/env/bin/python','-u',str(B/'tools/handoff_20261106/round8_short_jobs.py'),'--mode','cross20','--root',str(B)];p=subprocess.Popen(args,cwd=B,env=env)
 with(B/'logs/pid_registry.txt').open('a')as f:fcntl.flock(f,fcntl.LOCK_EX);f.write(str(p.pid)+'|'+subprocess.check_output(['ps','-p',str(p.pid),'-o','lstart='],text=True).strip()+'|'+' '.join(args)+chr(10));f.flush()
 print('LAUNCHED_CROSS20',p.pid,flush=True);raise SystemExit(p.wait())
launch_job()
