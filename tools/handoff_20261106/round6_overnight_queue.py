from pathlib import Path
import json,datetime,subprocess,time,fcntl,os
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round6';PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python';os.environ['DSH_OWNER']=str(B)
def progress(phase,**kw):
 p=O/'overnight_queue_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),phase=phase,**kw),indent=2));q.replace(p)
node_code="from pathlib import Path;import json;b=Path('/home/dell/Def');print(json.dumps({str(s):len(json.loads(p.read_text())['items'])if(p:=b/f'results/audit/WJB_BENIGN246_old_s{s}.json').exists()else 0 for s in range(3,8)}))"
benign_done=(B/'docs/265_BENIGN_SEEDS_RESULTS.md').exists();random_done=(B/'docs/264_WJB_RANDOM_REFERENCES.md').exists()
while not(benign_done and random_done):
 counts={};error=None
 if not benign_done:
  try:
   r=subprocess.run(['ssh','node01','python3','-'],input=node_code,text=True,capture_output=True,check=True,timeout=30);counts=json.loads(r.stdout)
  except(subprocess.TimeoutExpired,subprocess.CalledProcessError,json.JSONDecodeError)as exc:error=str(exc)
  if len(counts)==5 and all(x==600 for x in counts.values()):
   for s in range(3,8):subprocess.run(['rsync','-a',f'node01:/home/dell/Def/results/audit/WJB_BENIGN246_old_s{s}.json',str(B/'results/audit')+'/'],check=True)
   progress('analyzing_complete_doc250',counts=counts)
   subprocess.run([PY,str(B/'tools/handoff_20261106/round6_analyze_benign.py')],check=True);benign_done=True
 heart=[]
 for s in[2,3]:
  p=O/f'rand{s}_heartbeat.json';heart.append(json.loads(p.read_text())if p.exists()else{})
 if not random_done and all(h.get('phase')=='complete'and h.get('n')==300 for h in heart):
  locks=[(B/f'logs/idle_gpu{c}.lock').open('a')for c in[2,3]];acquired=[]
  try:
   for lock in locks:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);acquired.append(lock)
   gate=subprocess.run(['bash','-c','source /data/HZX/Def/night/launch.sh\nwait_gpu cuda:2 || exit 1\nwait_gpu cuda:3 || exit 1'],text=True,capture_output=True)
   if not gate.returncode:
    progress('judging_random2_and3',physical_gpus=[2,3]);subprocess.run([PY,'-u',str(B/'tools/handoff_20261106/round6_judge_randoms.py')],env={**os.environ,'CUDA_VISIBLE_DEVICES':'2,3','USE_TF':'0','USE_FLAX':'0','HF_HUB_OFFLINE':'1'},check=True)
    subprocess.run([PY,str(B/'tools/handoff_20261106/round6_analyze_random_refs.py')],check=True);random_done=True
  except BlockingIOError:pass
  finally:
   for lock in acquired:fcntl.flock(lock,fcntl.LOCK_UN)
   for lock in locks:lock.close()
 progress('waiting'if not(benign_done and random_done)else'complete',doc250_completed=benign_done,random_references_completed=random_done,doc250_counts=counts,random_counts={str(h.get('random_seed')):h.get('n')for h in heart},error=error)
 if not(benign_done and random_done):time.sleep(30)
