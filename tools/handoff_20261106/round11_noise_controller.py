from pathlib import Path
import os,json,time,datetime,hashlib,subprocess,fcntl,shlex
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round11';PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python';os.environ['DSH_OWNER']=str(B)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2)+'\n');q.replace(p)
def state(phase,**kw):save(O/'noise_controller_live.json',dict(utc=now(),pid=os.getpid(),phase=phase,**kw))
probe="""from pathlib import Path
import json
B=Path('/home/dell/Def');O=B/'results/audit/handoff_round11';D=B/'results/noise_reference/seed3_B';out={}
for n in ['noise_B_launcher_live.json','noise_B_live.json']:
 p=O/n
 if p.exists():out[n]=json.loads(p.read_text())
out['counts']={n:len(json.loads((D/n).read_text())['items'])if(D/n).exists()else 0 for n in['repeatB_a1_wjb300.json','repeatB_a1_pairs600.json']};print(json.dumps(out))"""
try:
 assert sha(B/'docs/252_ADDENDUM4_FIVE_PLAIN_SEEDS_NOISE_REFERENCE.md')=='95b9605403552e2c7503d5a74f9222c4c2fadf08fa186643fbf18dc5e137f64f'
 while True:
  d=json.loads(subprocess.check_output(['ssh','node01','python3','-c',shlex.quote(probe)],text=True));save(O/'noise_B_remote_snapshot.json',d);state('waiting_node_noise_B',remote=d)
  launcher=d.get('noise_B_launcher_live.json',{});assert launcher.get('phase')!='failed','node noise worker failed'
  if d['counts']['repeatB_a1_wjb300.json']==300 and d['counts']['repeatB_a1_pairs600.json']==600 and launcher.get('phase')=='complete':break
  assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc),'deadline';time.sleep(30)
 D=B/'results/noise_reference/seed3_B';D.mkdir(parents=True,exist_ok=True);subprocess.run(['rsync','-a','node01:/home/dell/Def/results/noise_reference/seed3_B/',str(D)+'/'],check=True)
 # Original two-arm judge/analysis window has priority. Its report explicitly notes this noise reference is pending.
 while True:
  prior=json.loads((B/'results/audit/handoff_round9/pipeline_live.json').read_text())
  if prior['phase']=='complete':break
  assert prior['phase']!='failed','original window incomplete';state('waiting_original_window');time.sleep(10)
 jobs=[dict(tag='seed3_repeatB_noise',kind='wjb',n=300,input_file='results/noise_reference/seed3_B/repeatB_a1_wjb300.json',target_file='results/noise_reference/seed3_B/repeatB_a1_wjb300_judge.json',baseline_file='results/style_retrained/eval_s3/control_a1_wjb300.json')];save(O/'judge_jobs_noise.json',jobs)
 locks=[(B/f'logs/idle_gpu{x}.lock').open('a')for x in[2,3]]
 while True:
  acq=[]
  try:
   for h in locks:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);acq.append(h)
  except BlockingIOError:
   for h in acq:fcntl.flock(h,fcntl.LOCK_UN)
   state('waiting_noise_HF_pair');time.sleep(10);continue
  ready=subprocess.run(['bash','-c','source /data/HZX/Def/night/launch.sh\nwait_gpu cuda:2 || exit 1\nwait_gpu cuda:3 || exit 1'],capture_output=True,text=True)
  if ready.returncode==0:break
  for h in acq:fcntl.flock(h,fcntl.LOCK_UN)
  state('waiting_original_wait_gpu');time.sleep(10)
 try:
  state('judging_noise_B')
  with(B/'logs/round11_judge_noise.log').open('ab')as log:subprocess.run([PY,'-u',str(B/'tools/handoff_20261106/round11_judge.py'),'--phase','noise'],check=True,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'CUDA_VISIBLE_DEVICES':'2,3','HF_HUB_OFFLINE':'1','USE_TF':'0','USE_FLAX':'0'})
 finally:
  for h in locks:fcntl.flock(h,fcntl.LOCK_UN);h.close()
 state('analyzing_complete_noise_pair')
 with(B/'logs/round11_noise_analyze.log').open('ab')as log:subprocess.run([PY,str(B/'tools/handoff_20261106/round11_noise_analyze.py')],check=True,stdout=log,stderr=subprocess.STDOUT)
 state('complete')
except Exception as e:state('failed',error=str(e));raise
