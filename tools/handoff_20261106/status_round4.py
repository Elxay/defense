from pathlib import Path
import json,subprocess,datetime
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round4'
node_code="""from pathlib import Path
import json,subprocess,datetime
b=Path('/home/dell/Def');out=[]
for tag,pid,gpu in [('old_s3_a1.0',1756300,2),('old_s4_a1.0',1758204,1),('rand1',1758200,0)]:
 p=b/f'results/audit/WJB_{tag}.json';m=p.with_suffix('.meta.json');n=len(json.loads(p.read_text()))if p.exists()else 0
 ps=subprocess.getoutput(f'ps -p {pid} -o etime=,args=');span=p.stat().st_mtime-m.stat().st_mtime if p.exists()and m.exists()else None
 out.append({'condition':tag,'pid':pid,'gpu':gpu,'n':n,'target':300,'status':'complete'if n==300 else'running'if ps.strip()else'stopped_incomplete','etime_and_command':ps.strip(),'measured_seconds_per_item':span/n if span and n else None,'measurement':'checkpoint mtime minus metadata mtime written after model load, divided by completed items','last_write_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()if p.exists()else None})
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'jobs':out,'gpu':subprocess.getoutput('nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader')}))"""
r=subprocess.run(['ssh','node01','python3','-'],input=node_code,text=True,capture_output=True,check=True);node=json.loads(r.stdout)
first=json.loads((b/'results/audit/handoff_20261106/doc246_first_generation_stat.json').read_text())['first_output_mtime_ns']/1e9
jobs=[];prev=first
for tag in ['alpha0','old_s0','rand0','rand1']:
 p=b/f'results/audit/WJB_BENIGN246_{tag}.json';n=len(json.loads(p.read_text())['items'])if p.exists()else 0;last=p.stat().st_mtime if p.exists()else None
 jobs.append({'condition':tag,'n':n,'target':600,'measured_seconds_per_item':(last-prev)/(n-1 if tag=='alpha0'else n)if n else None,'measurement':'checkpoint duration since previous condition completion, excludes initial model load'})
 if last:prev=last
snap={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'node01':node,'innet_pairs':{'pid':1041097,'gpu':2,'counts':jobs,'etime_and_command':subprocess.getoutput('ps -p 1041097 -o etime=,args=')},'innet_gpus':subprocess.getoutput('nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader'),'guard_queue':json.loads((o/'guard_queue.json').read_text()),'wjb_controller_pid':1118089,'judge_cards':'isolated physical2/3 after complete+wait_gpu; GPU0/1 forbidden'}
p=o/'guard_v2/guard_qwen_progress.json'
if p.exists():snap['guard_progress']=json.loads(p.read_text())
reg=[line for line in(b/'logs/pid_registry.txt').read_text().splitlines()if line.endswith('/guard_qwen_output.py')]
if reg:snap['guard_worker_pid']=int(reg[-1].split('|')[0]);snap['guard_worker_status']=subprocess.getoutput('ps -p '+str(snap['guard_worker_pid'])+' -o etime=,args=')
snap['wjb_controller_status']=subprocess.getoutput('ps -p 1118089 -o etime=,args=')
p=o/'process_snapshot.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n');q.replace(p)
print(json.dumps(snap,ensure_ascii=False,indent=2))
