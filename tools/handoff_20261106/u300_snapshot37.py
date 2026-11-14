from u300_schedule_prepare import *
import shlex,csv,io,re
O=U/'followup37'
code='''import json,subprocess,pathlib,pwd,datetime,re
R=pathlib.Path(ROOT);g=[]
for line in subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().splitlines():
 a=line.split(',');g.append(dict(index=int(a[0]),uuid=a[1].strip(),used_MiB=int(a[2]),free_MiB=int(a[3]),util_pct=int(a[4]),processes=[]))
for line in subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'],text=True).strip().splitlines():
 if not line.strip():continue
 uuid,pid,mem=map(str.strip,line.split(','));p=pathlib.Path('/proc')/pid;record=dict(pid=int(pid),used_MiB=mem)
 try:
  record['account']=pwd.getpwuid(p.stat().st_uid).pw_name;raw=(p/'cmdline').read_bytes().replace(b'\\0',b' ').decode(errors='replace');record['command']=re.sub(r'hf_[A-Za-z0-9]+','[redacted]',raw)[:700]
  env=(p/'environ').read_bytes().split(b'\\0');lease=next((x.split(b'=',1)[1].decode() for x in env if x.startswith(b'DEF_LEASE_DIR=')),None)
  if lease:
   d=pathlib.Path(lease)/'descriptor.json';descriptor=json.loads(d.read_text()) if d.exists() else {};record['registered_task']=descriptor.get('task_id');record['project']='defense/unified300';record['lease']=pathlib.Path(lease).name
  else:record['project']='unregistered; no ownership inference from OS account'
 except (OSError,KeyError) as e:record['inspection_error']=type(e).__name__
 for x in g:
  if x['uuid']==uuid:x['processes'].append(record)
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),gpus=g)))
'''
hardware={}
for site,root,py in [('innet',str(R),'/home/kemove/anaconda3/envs/HZX_GLA/bin/python'),('node01','/home/dell/Def','/data/ray/env/bin/python')]:
 c=code.replace('ROOT',repr(root));args=[py,'-c',c] if site=='innet' else ['ssh','node01',py+' -c '+shlex.quote(c)];hardware[site]=json.loads(subprocess.check_output(args,text=True))
s=L(U/'ready_queue/state.json');cat=L(U/'ready_queue_catalog.json');reg=L(U/'T2_processing37_registry.json');routes={x['cell_id']:x for x in reg['cells']};rows=[]
for t in cat['tasks']:
 if t['kind'] not in ['T2_nonzero_translation'] and not (t['id'].startswith(('B4_ml_llama_','B4_ta_llama_','T2nonzero36_','T2_llama_translate-mr_'))):continue
 st=s['tasks'].get(t['id'],{});rows.append(dict(lane=t['site']+':'+str(t['gpus'][0]),task_id=t['id'],kind=t['kind'],priority=t['priority'],state=st.get('state','pending'),started_UTC=st.get('started_utc',''),requires=json.dumps(t.get('requires',[]),sort_keys=True)))
rows.sort(key=lambda x:(x['lane'],0 if x['state']=='running' else 1,x['priority'],x['task_id']));out=io.StringIO();w=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);(O/'T2_per_card_queue.csv').write_text(out.getvalue())
gates=[]
for lang in ['ml','mr','ta']:
 p=U/'language_gate33'/f'qwen_translate-{lang}_alpha0.json';z=L(p);tid=f'T2nonzero36_qwen_translate-{lang}_s3';starts=[]
 for d in sorted((U/'queue_jobs').glob(tid+'__*')):
  log=d/'execution.log'
  if log.exists():starts.extend([v for v in log.read_text(errors='replace').splitlines() if v.startswith('START')][:1])
 gates.append(dict(language=lang,N=z['N'],fulfilled=z['fulfilled'],INVALID_N=len(z['INVALID_IDs']),rate_bounds=z['rate_bounds'],read_UTC=z['utc'],gate_file_sha256=H(p),s3_start_logs=starts))
save(O/'latest_hardware_and_gates.json',dict(utc=utc(),hardware=hardware,Qwen_alpha0_gates=gates,controller_UTC=s['utc'],active_tasks={k:{x:v.get(x) for x in ['site','gpus','runner_pid','job_dir','started_utc','staging']} for k,v in s['tasks'].items() if v.get('state')=='running'},queue_csv_sha256=H(O/'T2_per_card_queue.csv'),T2_watch=L(O/'T2_watch/live.json')))
gatecode="from pathlib import Path;import json;p=Path('/home/dell/Def/results/audit/unified300/language_processed36/gates/node01/gpu1/reference20.json');print(p.read_text() if p.exists() else json.dumps({'phase':'reference20_in_progress','passed':None}))"
newgate=json.loads(subprocess.check_output(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(gatecode)],text=True));save(O/'B1_translation_newsite_gate37.json',newgate)
print('NEW_REFERENCE_GATE',json.dumps(newgate))
print(json.dumps(L(O/'latest_hardware_and_gates.json'),indent=2))
print('QUEUES',json.dumps([{k:r[k] for k in ['lane','task_id','priority','state']} for r in rows if r['state'] not in ['done','failed']],indent=2))
