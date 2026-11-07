from pathlib import Path
import os,sys,json,time,datetime,hashlib,subprocess,fcntl
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round11';T=B/'results/plain_arm';PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python';NODEPY='/data/ray/env/bin/python';os.environ['DSH_OWNER']=str(B);SLOTS={3:('node01',0),4:('node01',1),5:('node01',2),6:('innet',2),7:('innet',3)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def atomic(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2)+'\n');q.replace(p)

def state(phase,**kw):atomic(O/'plain_pipeline_live.json',dict(utc=now(),pid=os.getpid(),phase=phase,slots={str(s):dict(host=h,card=c)for s,(h,c)in SLOTS.items()},**kw))

def deadline():assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc),'11/10 00:00JST hard stop reached'

def wait_exists(paths,phase):
 while not all(p.exists()for p in paths):deadline();state(phase,missing=[str(p.relative_to(B))for p in paths if not p.exists()]);time.sleep(10)

def run(cmd,logname,stdin=None):
 log=(B/'logs'/logname).open('ab');p=subprocess.Popen(cmd,cwd=B,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,start_new_session=True,env={**os.environ,'DSH_OWNER':str(B),'HF_HUB_OFFLINE':'1','USE_TF':'0','USE_FLAX':'0'})
 if stdin is not None:p.stdin.write(stdin.encode());p.stdin.close()
 log.close();return p

def wait_jobs(jobs,phase):
 while any(p.poll()is None for p in jobs.values()):deadline();state(phase,jobs={str(k):dict(wrapper_pid=p.pid,returncode=p.poll())for k,p in jobs.items()});time.sleep(10)
 assert all(p.returncode==0 for p in jobs.values()),'owned stage failed: '+str({k:p.returncode for k,p in jobs.items()})

def judge(phase,jobs):
 atomic(O/f'judge_jobs_{phase}.json',jobs);locks=[(B/f'logs/idle_gpu{c}.lock').open('a')for c in[2,3]]
 while True:
  deadline();acq=[]
  try:
   for h in locks:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);acq.append(h)
  except BlockingIOError:
   for h in acq:fcntl.flock(h,fcntl.LOCK_UN)
   state('waiting_judge_pair_lease',stage=phase);time.sleep(10);continue
  check=subprocess.run(['bash','-c','source /data/HZX/Def/night/launch.sh\nwait_gpu cuda:2 || exit 1\nwait_gpu cuda:3 || exit 1'],capture_output=True,text=True)
  if check.returncode==0:break
  for h in acq:fcntl.flock(h,fcntl.LOCK_UN)
  state('waiting_original_wait_gpu',stage=phase);time.sleep(30)
 try:
  p=run(['env','CUDA_VISIBLE_DEVICES=2,3',PY,'-u',str(B/'tools/handoff_20261106/round11_judge.py'),'--phase',phase],f'round10_judge_{phase}.log')
  # The judge itself requires CUDA_VISIBLE_DEVICES=2,3; inherit it only for this invocation through env wrapper.
  wait_jobs({'judge':p},'judging_'+phase)
 finally:
  for h in locks:fcntl.flock(h,fcntl.LOCK_UN);h.close()
def trainqueue(card,seeds):
 lines=['source /data/HZX/Def/night/launch.sh','cd /data/HZX/Def','set -e']
 for seed in seeds:
  if(T/f'plain_s{seed}/metadata.json').exists():continue
  lines +=[f'exec 8>>logs/idle_gpu{card}.lock','flock 8',f'export DEVICE=cuda:{card}','while ! wait_gpu "$DEVICE"; do sleep 30; done',f'launch_job env CUDA_VISIBLE_DEVICES={card} DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 {PY} -u tools/handoff_20261106/round11_plain_train.py --mode plain --seed {seed} --physical-card {card} --run-id plain_s{seed}','flock -u 8']
 return run(['bash','-c','\n'.join(lines)],f'round10_trainqueue_gpu{card}.log')
def generate(phase):
 jobs={}
 for seed,(host,card)in SLOTS.items():
  root='/home/dell/Def'if host=='node01'else str(B);python=NODEPY if host=='node01'else PY;launcher='tools/handoff_20261106/node01_launch_round9.sh'if host=='node01'else'night/launch.sh'
  script=f'cd {root}\nsource {root}/{launcher}\nexec 8>>logs/idle_gpu{card}.lock\nflock 8\nexport DEVICE=cuda:{card}\nwhile ! wait_gpu "$DEVICE"; do sleep 30; done\nlaunch_job env CUDA_VISIBLE_DEVICES={card} DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 {python} -u tools/handoff_20261106/round11_plain_generate.py --root {root} --seed {seed} --card {card} --phase {phase}\n'
  jobs[seed]=run(['ssh','node01','bash','-s']if host=='node01'else['bash','-s'],f'round11_generate_{phase}_s{seed}.log',stdin=script)
 wait_jobs(jobs,'plainN5_generating_'+phase)
 for seed in[3,4,5]:
  (T/f'eval_s{seed}').mkdir(exist_ok=True);subprocess.run(['rsync','-a',f'node01:/home/dell/Def/results/plain_arm/eval_s{seed}/',str(T/f'eval_s{seed}')+'/'],check=True);subprocess.run(['rsync','-a',f'node01:/home/dell/Def/results/audit/handoff_round11/generate_{phase}_s{seed}_live.json',str(O)+'/'],check=True)
def analyze(phase):
 with(B/f'logs/round10_analyze_{phase}.log').open('ab')as log:subprocess.run([PY,str(B/'tools/handoff_20261106/round11_plain_analyze.py'),'--phase',phase],stdout=log,stderr=subprocess.STDOUT,check=True)
try:
 assert sha(B/'docs/252_ADDENDUM4_FIVE_PLAIN_SEEDS_NOISE_REFERENCE.md')=='95b9605403552e2c7503d5a74f9222c4c2fadf08fa186643fbf18dc5e137f64f'
 assert sha(B/'docs/252_ADDENDUM3_PLAIN_ARM_INTERPOLATION.md')=='e92456d65278081f8b1c6b6acd1b165c8219b4c9a62af0bcbb2e6e58ad852195'
 wait_exists([T/'plain_training_targets.json'],'waiting_audited_reviewed_plain_targets');data=json.loads((T/'plain_training_targets.json').read_text());assert data['n_inputs']==120 and data['addendum3_sha256']==sha(B/'docs/252_ADDENDUM3_PLAIN_ARM_INTERPOLATION.md')and data['gpt_followup_sha256']
 wait_jobs({2:trainqueue(2,[7]),3:trainqueue(3,[6])},'plain_training')
 wait_exists([T/f'plain_s{x}/metadata.json'for x in range(3,8)],'waiting_all5_plain_vectors')
 files=['tools/handoff_20261106/round11_plain_generate.py','docs/252_ADDENDUM3_PLAIN_ARM_INTERPOLATION.md','docs/252_ADDENDUM4_FIVE_PLAIN_SEEDS_NOISE_REFERENCE.md']+[f'results/plain_arm/plain_s{x}/{n}'for x in[3,4,5]for n in['v.npy','metadata.json']];subprocess.run(['rsync','-aR',*files,'node01:/home/dell/Def/'],cwd=B,check=True)
 if not(T/'alpha_plan_frozen.json').exists():
  while True:
   prior=json.loads((B/'results/audit/handoff_round9/pipeline_live.json').read_text())
   if prior['phase']=='complete':break
   assert prior['phase']not in['failed','stopped_incomparable_seed'],'original#2 incomplete'
   deadline();state('waiting_original_2arm_before_plain_grid',original_phase=prior['phase']);time.sleep(10)
  generate('grid')
  # Give the already-running #2 window priority, and never read partial third-arm effects.
  while True:
   prior=json.loads((B/'results/audit/handoff_round9/pipeline_live.json').read_text())
   if prior['phase']=='complete':break
   assert prior['phase']not in['failed','stopped_incomparable_seed'],'original#2 did not complete; preserve missingness'
   deadline();state('waiting_original_2arm_window',original_phase=prior['phase']);time.sleep(10)
  jobs=[]
  for seed in range(3,8):
   for alpha in[.25,.5,.75,1.,1.25,1.5]:
    tag=f'plain_a{alpha:g}';base=f'results/plain_arm/eval_s{seed}/';jobs.append(dict(tag=f'plain_s{seed}_a{alpha}',kind='val',n=70,input_file=base+tag+'_val70.json',target_file=base+tag+'_val70_judge.json',baseline_file=f'results/style_retrained/eval_s{seed}/control_a1_val70.json'))
  judge('grid',jobs);analyze('grid')
 plan=json.loads((T/'alpha_plan_frozen.json').read_text())
 if not plan['all_comparable']:state('plain_incomparable',rows=plan['rows']);raise SystemExit(0)
 subprocess.run(['rsync','-a','results/plain_arm/alpha_plan_frozen.json','node01:/home/dell/Def/results/plain_arm/'],cwd=B,check=True);generate('full');jobs=[]
 for seed in range(3,8):
  for alpha in plan['rows'][str(seed)]['endpoint_alphas']:
   tag=f'plain_a{alpha:g}';base=f'results/plain_arm/eval_s{seed}/';jobs.append(dict(tag=f'plain_s{seed}_a{alpha}',kind='wjb',n=300,input_file=base+tag+'_wjb300.json',target_file=base+tag+'_wjb300_judge.json',baseline_file=f'results/style_retrained/eval_s{seed}/control_a1_wjb300.json'))
 judge('full',jobs)
 with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(now()+' PLAIN_ARM_FIRST_COMPLETE_EFFECT_READ all5seeds_allendpoints300harm600pairs complete; endpointplanSHA='+sha(T/'alpha_plan_frozen.json')+'\n')
 analyze('full');state('complete',result='results/audit/handoff_round11/plain_arm_complete_results.json')
except Exception as e:state('failed',error=str(e));raise
