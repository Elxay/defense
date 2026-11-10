"""S0 metadata barrier, then freeze immutable long-label inputs before scoring."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,shutil,subprocess,time
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';G=R/'prereg_repo'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def pulse(phase,**kw):
 p=U/'cap2400_label_queue_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps({'utc':utc(),'pid':os.getpid(),'phase':phase,'absolute_condition_rates_read':False,**kw},indent=2)+'\n');q.replace(p)
def main():
 execution=load(U/'cap2400_label_queue_execution.json');assert sha(__file__)==execution['queue_worker_sha256']
 sources={'qwen':U/'acceptance/qwen','llama':U/'acceptance_v2/llama'};start=time.monotonic()
 while True:
  ready={k:(d/'generation_complete.json').exists()for k,d in sources.items()}
  if all(ready.values()):break
  failed={k:(d/'memory_admission_failed.json').exists()for k,d in sources.items()}
  if any(failed.values()):pulse('blocked_memory_gate',ready=ready,failed=failed);return
  pulse('waiting_generation_metadata',ready=ready)
  if time.monotonic()-start>12*3600:pulse('time_limit_no_scoring');return
  time.sleep(10)
 base=load(U/'acceptance_generation_plan.json');fallback=load(U/'acceptance_generation_plan_v2.json');cal={r['id']:r for r in load(U/'calibration700.private.json')};items=[]
 for model in ['llama','qwen']:
  for condition in ['alpha0','s3','random']:
   for route in ['legacy_single','candidate_batch']:
    folder=sources[model]/'generation.private/cap2400'/condition/route;assert len(list(folder.glob('*.json')))==100
    for k in base['IDs100']:
     p=folder/(k+'.json');value=load(p);signature=value['signature']
     if model=='llama'and condition=='alpha0'and route=='legacy_single':assert sha(p)==fallback['reused_legacy_records'][k]['sha256']
     else:assert signature['plan_sha256']==sha(U/('acceptance_generation_plan.json'if model=='qwen'else'acceptance_generation_plan_v2.json'))
     items.append({'cache_id':model+'__'+condition+'__'+route+'__'+k,'model':model,'condition':condition,'path':route,'id':k,'prompt':cal[k]['prompt'],'response':value['result']['text'],'generation_record_sha256':sha(p)})
 assert len(items)==1200
 p=U/'acceptance_cap2400_inputs.private.json';assert not p.exists();p.write_text(json.dumps(items,indent=2)+'\n')
 plan=load(U/'acceptance_cap120_label_plan.json');plan.update(utc_frozen=utc(),cap=2400,input_sha256=sha(p),worker_sha256=sha(R/'tools/handoff_20261106/unified300_acceptance_label_gate2400.py'),generation_plan_sha256=sha(U/'acceptance_generation_plan.json'),Llama_long_generation_plan_sha256=sha(U/'acceptance_generation_plan_v2.json'),queue_execution_sha256=sha(U/'cap2400_label_queue_execution.json'),new_label_gate_outputs=0,formal_generation_admitted=False)
 p=U/'acceptance_cap2400_label_plan.json';assert not p.exists();p.write_text(json.dumps(plan,indent=2)+'\n')
 pulse('freezing_label_plan',plan_sha256=sha(p))
 line=utc()+' unified300 full2400 paired label inputs complete1200 and frozen before scoring; Llama B8 replacement only, Qwen B32; explicit old B1 references verified. Only WG/v2 paired flips, no absolute condition rates; main test remains locked. planSHA='+sha(p)+'\n'
 for name in ['OPS_LOG','PREREG_LOG.txt']:
  with (R/'docs'/name).open('a')as f:f.write(line)
 files=[p,R/'docs/OPS_LOG',R/'docs/PREREG_LOG.txt']
 with (R/'logs/prereg_publish.lock').open('a')as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip();rels=[]
  for f in files:
   rel=f.relative_to(R);dst=G/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst);rels.append(str(rel))
  subprocess.run(['git','add','--',*rels],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Freeze complete long-panel paired label inputs before S0 scoring'],cwd=G,check=True);subprocess.run(['git','push','origin','HEAD'],cwd=G,check=True)
 subprocess.run(['scp',str(U/'acceptance_cap2400_inputs.private.json'),str(U/'acceptance_cap2400_label_plan.json'),'node01:/home/dell/Def/results/audit/unified300/'],check=True)
 subprocess.run(['scp',str(R/'tools/handoff_20261106/unified300_acceptance_label_gate2400.py'),str(R/'tools/handoff_20261106/launch300_cap2400_labels.sh'),'node01:/home/dell/Def/tools/handoff_20261106/'],check=True)
 subprocess.run(['ssh','node01','nohup bash /home/dell/Def/tools/handoff_20261106/launch300_cap2400_labels.sh > /home/dell/Def/logs/unified300_cap2400_labels.log 2>&1 < /dev/null &'],check=True)
 pulse('label_worker_dispatched')
if __name__=='__main__':main()
