"""Owned unattended pipeline. No treatment evaluation until frozen targets; no holdout generation before alpha freeze."""
from pathlib import Path
import os,sys,subprocess,json,time,datetime,hashlib,fcntl
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round9';T=B/'results/style_retrained';PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python';NODEPY='/data/ray/env/bin/python';os.environ['DSH_OWNER']=str(B)
SLOTS={3:('node01',0),4:('node01',1),5:('node01',2),6:('innet',2),7:('innet',3)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2)+'\n');q.replace(p)
def state(phase,**kw):atomic(O/'pipeline_live.json',dict(utc=now(),pid=os.getpid(),phase=phase,slots={str(s):dict(host=h,card=c)for s,(h,c)in SLOTS.items()},**kw))
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
  p=run(['env','CUDA_VISIBLE_DEVICES=2,3',PY,'-u',str(B/'tools/handoff_20261106/round9_judge.py'),'--phase',phase],f'round9_judge_{phase}.log')
  # The judge itself requires CUDA_VISIBLE_DEVICES=2,3; inherit it only for this invocation through env wrapper.
  wait_jobs({'judge':p},'judging_'+phase)
 finally:
  for h in locks:fcntl.flock(h,fcntl.LOCK_UN);h.close()
def analyze(phase):
 with(B/f'logs/round9_analyze_{phase}.log').open('ab')as log:subprocess.run([PY,str(B/'tools/handoff_20261106/round9_analyze.py'),'--phase',phase],stdout=log,stderr=subprocess.STDOUT,check=True,env={**os.environ,'USE_TF':'0','USE_FLAX':'0'})
def train_queue(card,seeds):
 lines=['source /data/HZX/Def/night/launch.sh','cd /data/HZX/Def','set -e']
 for seed in seeds:
  for mode,runid in[('control','repeatA_s3'if seed==3 else f'control_s{seed}'),('treatment',f'treatment_s{seed}')]:
   root=T/runid
   complete=(root/'metadata.json').exists()and(root/'v.npy').exists()and(mode=='treatment'or((root/'val70.json').exists()and len(json.loads((root/'val70.json').read_text()))==70))
   if complete:continue
   lines +=[f'exec 8>>logs/idle_gpu{card}.lock','flock 8',f'export DEVICE=cuda:{card}','while ! wait_gpu "$DEVICE"; do sleep 30; done',f'launch_job env CUDA_VISIBLE_DEVICES={card} DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 {PY} -u tools/handoff_20261106/round9_train.py --mode {mode} --seed {seed} --physical-card {card} --run-id {runid}','flock -u 8']
 return run(['bash','-c','\n'.join(lines)],f'round9_trainqueue_gpu{card}.log')
def generate(phase):
 jobs={}
 for seed,(host,card)in SLOTS.items():
  deadline();root='/home/dell/Def'if host=='node01'else str(B);python=NODEPY if host=='node01'else PY;launch='tools/handoff_20261106/node01_launch_round9.sh'if host=='node01'else'night/launch.sh'
  script=f'cd {root}\nsource {root}/{launch}\nexec 8>>logs/idle_gpu{card}.lock\nflock 8\nexport DEVICE=cuda:{card}\nwhile ! wait_gpu "$DEVICE"; do sleep 30; done\nlaunch_job env CUDA_VISIBLE_DEVICES={card} DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 {python} -u tools/handoff_20261106/round9_generate.py --root {root} --seed {seed} --card {card} --phase {phase}\n'
  jobs[seed]=run(['ssh','node01','bash','-s']if host=='node01'else['bash','-s'],f'round9_generate_{phase}_s{seed}.log',stdin=script)
 wait_jobs(jobs,'generating_'+phase)
 for seed in[3,4,5]:
  (T/f'eval_s{seed}').mkdir(exist_ok=True);subprocess.run(['rsync','-a',f'node01:/home/dell/Def/results/style_retrained/eval_s{seed}/',str(T/f'eval_s{seed}')+'/'],check=True)
  subprocess.run(['rsync','-a',f'node01:/home/dell/Def/results/audit/handoff_round9/generate_{phase}_s{seed}_live.json',str(O)+'/'],check=True)
def grid_jobs():
 jobs=[]
 for seed in range(3,8):
  for condition,alphas in[('control',[1.]),('treatment',[.25,.5,.75,1.,1.25,1.5])]:
   for alpha in alphas:
    tag=f'{condition}_a{alpha:g}';base=f'results/style_retrained/eval_s{seed}/';jobs.append(dict(tag=f's{seed}_{tag}',kind='val',n=70,input_file=base+tag+'_val70.json',target_file=base+tag+'_val70_judge.json',baseline_file=base+'control_a1_val70.json'))
 return jobs
try:
 assert sha(B/'docs/252_ADDENDUM2_RETRAINED_CONTROLS.md')=='493094393b6f2294498c3cf01a449f2b7557f23784530f9e8e002066f56e1896'
 wait_exists([T/'style_training_targets.json'],'waiting_reviewed_targets');assert sha(T/'style_training_targets.json')=='fb944571e6ee6c21fc5eb47d688c7f9b6fa77e8e8861a7c5fa3173517071340e'
 wait_exists([T/'repeatA_s3/val70.json',T/'repeatB_s3/val70.json'],'waiting_repeat_training')
 while json.loads((O/'repeat_controller_live.json').read_text())['phase']!='repeats_generated_waiting_hf_judge':state('waiting_repeats_complete');time.sleep(10)
 if not(O/'repeat_comparison.json').exists():
  judge('repeats',[dict(tag='repeat'+x,kind='val',n=70,input_file=f'results/style_retrained/repeat{x}_s3/val70.json',target_file=f'results/style_retrained/repeat{x}_s3/judge.json',baseline_file='results/style_retrained/repeatA_s3/val70.json')for x in['A','B']]);analyze('repeats')
 state('training_paired_conditions');wait_jobs({2:train_queue(2,[3,5,7]),3:train_queue(3,[4,6])},'training_paired_conditions')
 # Copy only private source inputs/vectors between nodes, never stage them in the Git repository.
 files=[]
 for seed in range(3,8):
  for runid in['repeatA_s3'if seed==3 else f'control_s{seed}',f'treatment_s{seed}']:
   for n in['v.npy','metadata.json']:files.append(f'results/style_retrained/{runid}/{n}')
 subprocess.run(['rsync','-aR',*files,'node01:/home/dell/Def/'],cwd=B,check=True)
 if not(T/'alpha_matches_frozen.json').exists():generate('grid');judge('grid',grid_jobs());analyze('grid')
 matches=json.loads((T/'alpha_matches_frozen.json').read_text())
 if not matches['all_comparable']:state('stopped_incomparable_seed',matches=matches['rows']);raise SystemExit(0)
 subprocess.run(['rsync','-a','results/style_retrained/alpha_matches_frozen.json','node01:/home/dell/Def/results/style_retrained/'],cwd=B,check=True)
 generate('full');jobs=[]
 for seed in range(3,8):
  for condition,alpha in[('control',1.),('treatment',matches['rows'][str(seed)]['selected_alpha'])]:
   tag=f'{condition}_a{alpha:g}';base=f'results/style_retrained/eval_s{seed}/';jobs.append(dict(tag=f's{seed}_{tag}',kind='wjb',n=300,input_file=base+tag+'_wjb300.json',target_file=base+tag+'_wjb300_judge.json',baseline_file=base+'control_a1_wjb300.json'))
 judge('full',jobs)
 with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(now()+' RETRAINED_STYLE_FIRST_ALL10_CONDITIONS_COMPLETE_EFFECT_READ all300harm+600pairs each, matchedalphasSHA='+sha(T/'alpha_matches_frozen.json')+'\n')
 analyze('full');state('complete',results_file='results/audit/handoff_round9/intervention_complete_results.json')
except Exception as exc:state('failed',error=str(exc));raise
