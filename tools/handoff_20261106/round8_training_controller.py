from pathlib import Path
import os,json,time,datetime,subprocess,fcntl,hashlib
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round8';T=B/'results/style_intervention';PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python';os.environ['DSH_OWNER']=str(B)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def state(phase,**kw):
 p=O/'training_controller_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(dict(utc=now(),pid=os.getpid(),phase=phase,**kw),indent=2));q.replace(p)
def run_card(mode,seed,card):
 args=f'--mode {mode} --seed {seed} --physical-card {card}'
 script=f'source /data/HZX/Def/night/launch.sh\ncd /data/HZX/Def\nexec 8>>logs/idle_gpu{card}.lock\nflock 8\nexport DEVICE=cuda:{card}\nwhile ! wait_gpu "$DEVICE"; do sleep 30; done\nlaunch_job env CUDA_VISIBLE_DEVICES={card} DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 python -u /data/HZX/Def/tools/handoff_20261106/round8_train_old_recipe.py {args}\n'
 log=(B/f'logs/round8_train_{mode}_s{seed}.log').open('ab');return subprocess.Popen(['bash','-c',script],cwd=B,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'DSH_OWNER':str(B)})
try:
 while not(T/'old_recipe_targets.json').exists():state('waiting_old_target_cache');time.sleep(10)
 state('fidelity_training');p=run_card('fidelity',3,2)
 while p.poll()is None:state('fidelity_training',wrapper_pid=p.pid);time.sleep(10)
 assert p.returncode==0,'fidelity training/generation failed; inspect owned log, no intervention starts'
 locks=[(B/f'logs/idle_gpu{c}.lock').open('a')for c in[2,3]]
 while True:
  acquired=[]
  try:
   for h in locks:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);acquired.append(h)
  except BlockingIOError:
   for h in acquired:fcntl.flock(h,fcntl.LOCK_UN)
   state('waiting_idle_pair_for_fidelity_judge');time.sleep(10);continue
  gate=subprocess.run(['bash','-c','source /data/HZX/Def/night/launch.sh\nwait_gpu cuda:2 || exit 1\nwait_gpu cuda:3 || exit 1'],text=True,capture_output=True)
  if gate.returncode==0:break
  for h in acquired:fcntl.flock(h,fcntl.LOCK_UN)
  state('waiting_original_wait_gpu');time.sleep(10)
 try:
  state('judging_fidelity70');subprocess.run([PY,'-u',str(B/'tools/handoff_20261106/round8_judge_fidelity.py')],check=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':'2,3','HF_HUB_OFFLINE':'1','USE_TF':'0','USE_FLAX':'0'})
 finally:
  for h in locks:fcntl.flock(h,fcntl.LOCK_UN);h.close()
 meta=json.loads((T/'fidelity_s3/metadata.json').read_text());a=json.loads((T/'fidelity_s3/judge.json').read_text())['items'];ref=B/'results/hfjudge/JUDGE_HF_innet_window7_old_seed_s3';d=json.loads(ref.read_text())['items'];assert set(a)==set(d)and len(a)==70
 changed=[k for k in a if(a[k]['p_yes']>.5)!=(d[k]['p_yes']>.5)];passed=meta['cosine_to_frozen_old']>.999 and len(changed)<=1
 result=dict(utc=now(),passed=passed,cosine=meta['cosine_to_frozen_old'],label_changes=len(changed),changed_ids=changed,reference_file=str(ref.relative_to(B)),reference_sha256=sha(ref),fidelity_vector_sha256=sha(T/'fidelity_s3/v.npy'),fidelity_judge_sha256=sha(T/'fidelity_s3/judge.json'),initial_theta_sha256=meta['init_sha256'])
 (T/'fidelity_gate.json').write_text(json.dumps(result,indent=2)+'\n');assert passed,'frozen fidelity gate failed; intervention stopped'
 while not(T/'style_training_targets.json').exists():state('waiting_final_audited_targets_after_fidelity');time.sleep(10)
 with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(now()+' STYLE_FIDELITY_GATE_PASS cosine='+str(result['cosine'])+' labelchanges='+str(len(changed))+'; auditedinputsSHA='+sha(T/'style_training_targets.json')+'; now launch treatmentseeds3-7 from frozen same-init files, fixedmean criteria.\n')
 todo=list(range(3,8));active={};done={}
 while todo or active:
  for card in[2,3]:
   if card not in active and todo:
    seed=todo.pop(0);active[card]=(seed,run_card('intervention',seed,card))
  for card,(seed,p)in list(active.items()):
   if p.poll()is not None:done[str(seed)]=dict(returncode=p.returncode,vector_exists=(T/f'treatment_s{seed}/v.npy').exists());del active[card]
  state('training_interventions',active={str(card):dict(seed=seed,wrapper_pid=p.pid)for card,(seed,p)in active.items()},completed=done,pending=todo)
  if todo or active:time.sleep(10)
 assert len(done)==5 and all(x['returncode']==0 for x in done.values()),'some seeds incomplete; never drop them from primary mean'
 state('training_complete_pending_alpha_grid_evaluation',completed=done)
except Exception as exc:state('failed',error=str(exc));raise
