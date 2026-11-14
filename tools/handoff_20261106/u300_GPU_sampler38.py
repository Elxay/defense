"""Persist observed per-card GPU samples; no command lines, tokens or judge labels."""
from u300_schedule_prepare import *
import shlex,time,os
O=U/'followup38/GPU_samples';O.mkdir(exist_ok=True)
code="""import json,subprocess,datetime
g=[]
for line in subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,utilization.gpu,memory.used,memory.free','--format=csv,noheader,nounits'],text=True).strip().splitlines():
 a=list(map(str.strip,line.split(',')));g.append(dict(index=int(a[0]),uuid=a[1],utilization_pct=int(a[2]),used_MiB=int(a[3]),free_MiB=int(a[4])))
p=[]
for line in subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'],text=True).strip().splitlines():
 if line.strip():
  a=list(map(str.strip,line.split(',')));p.append(dict(uuid=a[0],pid=int(a[1]),used_MiB=a[2]))
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),gpus=g,compute_processes=p)))
"""
while True:
 try:
  data={'utc':utc(),'sampler_pid':os.getpid(),'sites':{}}
  for site,py in [('innet','/home/kemove/anaconda3/envs/HZX_GLA/bin/python'),('node01','/data/ray/env/bin/python')]:
   args=[py,'-c',code] if site=='innet' else ['ssh','node01',py+' -c '+shlex.quote(code)];data['sites'][site]=json.loads(subprocess.check_output(args,text=True,timeout=30))
  data['innet_GPU1_excluded_from_dispatch']=True
  with (O/'samples.jsonl').open('a') as f:f.write(json.dumps(data)+'\n')
  save(O/'live.json',data)
 except Exception as e:save(O/'error.json',dict(utc=utc(),error=type(e).__name__,reason=str(e)[:300]))
 time.sleep(60)
