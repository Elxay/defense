"""CPU queue; acquire shared leases, then call existing wait_gpu on physical cards."""
from pathlib import Path
import datetime,fcntl,json,os,subprocess,sys,time
ROOT=Path('/data/HZX/Def');kind=sys.argv[1];assert kind in ['guard','wjb']
os.environ['DSH_OWNER']=str(ROOT)
with(ROOT/'logs/pid_registry.txt').open('a')as f:
 fcntl.flock(f,fcntl.LOCK_EX);f.write(str(os.getpid())+'|'+subprocess.check_output(['ps','-p',str(os.getpid()),'-o','lstart='],text=True).strip()+'|'+str(Path(__file__))+' '+kind+'\n');f.flush()
def status(phase,**kw):
 p=ROOT/f'results/audit/handoff_round4/{kind}_queue.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'phase':phase,**kw},indent=2));tmp.replace(p)
while True:
 counts={}
 for tag in ['alpha0','old_s0','rand0','rand1']:
  p=ROOT/f'results/audit/WJB_BENIGN246_{tag}.json'
  counts[tag]=len(json.loads(p.read_text())['items'])if p.exists()else 0
 if all(n==600 for n in counts.values()):break
 status('waiting_docs246',counts=counts);time.sleep(30)
cards=[3]if kind=='guard'else[2,3]
handles=[(ROOT/f'logs/idle_gpu{c}.lock').open('a')for c in cards]
while True:
 acquired=[]
 try:
  for h in handles:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);acquired.append(h)
 except BlockingIOError:
  for h in acquired:fcntl.flock(h,fcntl.LOCK_UN)
  status('waiting_card_lease',cards=cards);time.sleep(30);continue
 checks='source /data/HZX/Def/night/launch.sh\n'+'\n'.join(f'wait_gpu cuda:{c} || exit 1'for c in cards)
 check=subprocess.run(['bash','-c',checks],text=True,capture_output=True)
 if check.returncode==0:break
 for h in acquired:fcntl.flock(h,fcntl.LOCK_UN)
 status('waiting_wait_gpu',cards=cards,reason=check.stdout.strip());time.sleep(30)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=','.join(map(str,cards));env['DSH_OWNER']=str(ROOT);env['USE_TF']='0';env['USE_FLAX']='0';env['HF_HUB_OFFLINE']='1'
worker=ROOT/'tools/handoff_20261106'/('guard_qwen_output.py'if kind=='guard'else'judge_idle23.py')
status('running',physical_cards=cards,worker=str(worker))
try:
 subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','-u',str(worker)],env=env,check=True)
except BaseException as exc:
 status('failed',physical_cards=cards,error=str(exc));raise
else:status('completed',physical_cards=cards)
finally:
 for h in handles:fcntl.flock(h,fcntl.LOCK_UN);h.close()
