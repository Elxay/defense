from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,time
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';G=R/'prereg_repo'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def pulse(phase,**kw):
 p=U/'cap2400_label_queue_live_v4.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(dict(utc=utc(),pid=os.getpid(),phase=phase,absolute_condition_rates_read=False,**kw),indent=2)+'\n');q.replace(p)
def main():
 execution=load(U/'cap2400_label_queue_execution_v4.json');assert sha(__file__)==execution['queue_worker_sha256'];d=U/'acceptance_v4/qwen';start=time.monotonic()
 while not (d/'generation_complete.json').exists():
  if (d/'memory_admission_failed.json').exists():pulse('blocked_memory_gate');return
  if time.monotonic()-start>6*3600:pulse('blocked_timeout');return
  pulse('waiting_generation_metadata');time.sleep(10)
 generation=load(U/'acceptance_generation_plan_v4.json');cal={r['id']:r for r in load(U/'calibration700.private.json')};items=[]
 for condition in generation['conditions']:
  for route in ['legacy_single','candidate_batch']:
   folder=d/'generation.private/cap2400'/condition/route;assert len(list(folder.glob('*.json')))==100
   for k in generation['IDs100']:
    p=folder/(k+'.json');value=load(p)
    if route=='legacy_single':assert sha(p)==generation['reused_legacy_records'][condition+'/'+k]['sha256']
    else:assert value['signature']['plan_sha256']==sha(U/'acceptance_generation_plan_v4.json')
    items.append(dict(cache_id='qwen__'+condition+'__'+route+'__'+k,model='qwen',condition=condition,path=route,id=k,prompt=cal[k]['prompt'],response=value['result']['text'],generation_record_sha256=sha(p)))
 assert len(items)==600
 p=U/'acceptance_cap2400_inputs_v4.private.json';assert not p.exists();p.write_text(json.dumps(items,indent=2)+'\n')
 plan=load(U/'acceptance_cap2400_label_plan.json');plan.update(utc_frozen=utc(),input_sha256=sha(p),worker_sha256=sha(R/'tools/handoff_20261106/unified300_acceptance_label_gate2400_v4.py'),Qwen_fallback_plan_sha256=sha(U/'acceptance_generation_plan_v4.json'),queue_execution_sha256=sha(U/'cap2400_label_queue_execution_v4.json'),models=['qwen'],N=600,new_label_gate_outputs=0,formal_generation_admitted=False)
 p=U/'acceptance_cap2400_label_plan_v4.json';assert not p.exists();p.write_text(json.dumps(plan,indent=2)+'\n');pulse('freezing_label_plan',plan_sha256=sha(p))
 with (R/'logs/prereg_publish.lock').open('a')as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip();rel=p.relative_to(R);(G/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,G/rel)
  subprocess.run(['git','add','--',str(rel)],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Freeze complete Qwen B16 paired-label inputs before scoring'],cwd=G,check=True);subprocess.run(['git','push','origin','HEAD'],cwd=G,check=True)
 subprocess.run(['scp',str(U/'acceptance_cap2400_inputs_v4.private.json'),str(p),'node01:/home/dell/Def/results/audit/unified300/'],check=True)
 subprocess.run(['scp',str(R/'tools/handoff_20261106/unified300_acceptance_label_gate2400_v4.py'),str(R/'tools/handoff_20261106/launch300_cap2400_labels_v4.sh'),'node01:/home/dell/Def/tools/handoff_20261106/'],check=True)
 subprocess.run(['ssh','node01','nohup bash /home/dell/Def/tools/handoff_20261106/launch300_cap2400_labels_v4.sh > /home/dell/Def/logs/unified300_cap2400_labels_v4.log 2>&1 < /dev/null &'],check=True);pulse('label_worker_dispatched')
if __name__=='__main__':main()
