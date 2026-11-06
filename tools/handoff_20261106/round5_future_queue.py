from pathlib import Path
import json,datetime,fcntl,os,subprocess,time,hashlib
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round5';os.environ['DSH_OWNER']=str(b)
with(b/'logs/pid_registry.txt').open('a')as f:
 fcntl.flock(f,fcntl.LOCK_EX);f.write(str(os.getpid())+'|'+subprocess.check_output(['ps','-p',str(os.getpid()),'-o','lstart='],text=True).strip()+'|'+str(Path(__file__))+'\n');f.flush()
def progress(phase,**kw):
 p=o/'future_queue_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'phase':phase,**kw},indent=2));q.replace(p)
while True:
 code="from pathlib import Path;import json;b=Path('/home/dell/Def');p=b/'results/audit/WJB_old_s5_a1.0.json';s=(b/'logs/wjb_s5.log').read_text();print(json.dumps({'done':'WJB_DONE old_s5_a1.0 300'in s,'n':len(json.loads(p.read_text()))if p.exists()else 0}))"
 try:
  r=subprocess.run(['ssh','node01','python3','-'],input=code,text=True,capture_output=True,check=True);state={5:json.loads(r.stdout)}
  for seed in[6,7]:
   p=b/f'results/audit/WJB_old_s{seed}_a1.0.json';s=(b/f'logs/wjb_s{seed}.log').read_text();state[seed]={'done':f'WJB_DONE old_s{seed}_a1.0 300'in s,'n':len(json.loads(p.read_text()))if p.exists()else 0}
 except(Exception)as exc:progress('waiting_checkpoint',error=str(exc));time.sleep(30);continue
 if all(x['done']and x['n']==300 for x in state.values()):break
 progress('waiting_all_generation',counts=state);time.sleep(30)
subprocess.run(['rsync','-a','node01:/home/dell/Def/results/audit/WJB_old_s5_a1.0.json',str(b/'results/audit')+'/'],check=True)
for seed in[5,6,7]:
 p=b/f'results/audit/WJB_old_s{seed}_a1.0.json';d=json.loads(p.read_text());assert len(d)==300
 assert all(x['injection_count']==1 and abs(x['rho_runtime']-5.21)<.05 for x in d.values()),'runtime injection audit failed'
 meta={'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actual_generation_host':'node01'if seed==5 else'innet','host_field_in_generated_bytes':'node01 (legacy hardcoded; do not infer host from it)','baseline_file':'results/hfjudge/JUDGE_HF_wjb_a0_innet_round2','refusal_fn_sha256':hashlib.sha256((b/'src/judge/refusal.py').read_bytes()).hexdigest()};(o/f'WJB_s{seed}_generation_provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
handles=[(b/f'logs/idle_gpu{c}.lock').open('a')for c in[2,3]]
while True:
 acquired=[]
 try:
  for h in handles:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);acquired.append(h)
 except BlockingIOError:
  for h in acquired:fcntl.flock(h,fcntl.LOCK_UN)
  progress('waiting_leases');time.sleep(30);continue
 r=subprocess.run(['bash','-c','source /data/HZX/Def/night/launch.sh\nwait_gpu cuda:2 || exit 1\nwait_gpu cuda:3 || exit 1'],text=True,capture_output=True)
 if not r.returncode:break
 for h in acquired:fcntl.flock(h,fcntl.LOCK_UN)
 progress('waiting_original_wait_gpu',reason=r.stdout.strip());time.sleep(30)
try:
 progress('judging',physical_cards=[2,3]);env=dict(os.environ,CUDA_VISIBLE_DEVICES='2,3',USE_TF='0',USE_FLAX='0',HF_HUB_OFFLINE='1')
 subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','-u',str(b/'tools/handoff_20261106/round5_judge_seeds.py')],env=env,check=True)
finally:
 for h in handles:fcntl.flock(h,fcntl.LOCK_UN);h.close()
progress('aggregating')
subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','-u',str(b/'tools/handoff_20261106/round5_future_aggregate.py')],check=True)
progress('complete')
