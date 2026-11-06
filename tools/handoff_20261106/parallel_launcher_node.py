
from pathlib import Path
import os,subprocess,fcntl
b=Path('/home/dell/Def')
def start(name,device,kind,seed):
 used=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits','-i',str(device)],text=True).strip());assert used<2000,(device,used)
 env=dict(os.environ,DEVICE=f'cuda:{device}',DSH_OWNER='/data/HZX/Def',USE_TF='0',USE_FLAX='0',HF_HUB_OFFLINE='1')
 args=['/data/ray/env/bin/python','-u',str(b/'tools/handoff_20261106/wjb_parallel.py'),'--kind',kind,'--seed',str(seed)]
 log=(b/f'logs/parallel_{name}.log').open('a');p=subprocess.Popen(args,cwd=b,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
 st=subprocess.check_output(['ps','-p',str(p.pid),'-o','lstart='],text=True).strip()
 with(b/'logs/pid_registry.txt').open('a')as f:fcntl.flock(f,fcntl.LOCK_EX);f.write(f'{p.pid}|{st}|'+ ' '.join(args)+'\n');f.flush()
 print('REGISTERED',name,p.pid,device,flush=True)
 return p
rand=start('rand1',0,'random',1)
old=start('old_s4',1,'learned',4)
assert rand.wait()==0
assert old.wait()==0
