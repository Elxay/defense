from pathlib import Path
import json,subprocess,datetime,re,sys
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round5'
code="""from pathlib import Path
import json,subprocess,re
b=Path('/home/dell/Def');p=b/'results/audit/WJB_old_s5_a1.0.json';s=(b/'logs/wjb_s5.log').read_text();m=re.search(r'SPEED_25 ([0-9.]+)s',s)
try:n=len(json.loads(p.read_text()))
except:n=None
print(json.dumps({'host':'node01','seed':5,'pid':1789174,'gpu':2,'n_checkpoint':n,'done': 'WJB_DONE old_s5_a1.0 300'in s,'first25_seconds':float(m.group(1))if m else None,'last_write_epoch':p.stat().st_mtime if p.exists()else None,'process':subprocess.getoutput('ps -p1789174 -o etime=,args=').strip()}))"""
r=subprocess.run(['ssh','node01','python3','-'],input=code,text=True,capture_output=True,check=True);jobs=[json.loads(r.stdout)]
for seed,pid,gpu in[(6,1329826,2),(7,1329827,3)]:
 p=b/f'results/audit/WJB_old_s{seed}_a1.0.json';s=(b/f'logs/wjb_s{seed}.log').read_text();m=re.search(r'SPEED_25 ([0-9.]+)s',s)
 try:n=len(json.loads(p.read_text()))
 except:n=None
 jobs.append({'host':'innet','seed':seed,'pid':pid,'gpu':gpu,'n_checkpoint':n,'done':f'WJB_DONE old_s{seed}_a1.0 300'in s,'first25_seconds':float(m.group(1))if m else None,'last_write_epoch':p.stat().st_mtime if p.exists()else None,'process':subprocess.getoutput(f'ps -p{pid} -o etime=,args=').strip()})
now=datetime.datetime.now(datetime.timezone.utc)
for x in jobs:
 x['first25_seconds_per_item']=x['first25_seconds']/25 if x['first25_seconds']else None
 x['completed_utc']=datetime.datetime.fromtimestamp(x['last_write_epoch'],datetime.timezone.utc).isoformat()if x['done']else None
 if not x['done']and x['n_checkpoint']is not None and x['first25_seconds_per_item']:
  n=x['n_checkpoint'];sp=x['first25_seconds_per_item'];x['eta_range_utc']=[(now+datetime.timedelta(seconds=max(0,300-n-24)*sp)).isoformat(),(now+datetime.timedelta(seconds=(300-n)*sp)).isoformat()]
result={'utc':now.isoformat(),'jobs':jobs,'first25_timing_excludes_model_load':True,'checkpoint_every':25,'eta_note':'Progress-based projection with first25 sec/item;0..24 generated items can be absent from checkpoint. Future output lengths may differ.','future_queue':json.loads((o/'future_queue_live.json').read_text()),'gpu':subprocess.getoutput('nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader')}
name=sys.argv[1]if len(sys.argv)>1 else'generation_snapshot_live.json';assert '/'not in name and name.endswith('.json');p=o/name;q=p.with_suffix('.tmp');q.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');q.replace(p);print(json.dumps(result,ensure_ascii=False,indent=2))
