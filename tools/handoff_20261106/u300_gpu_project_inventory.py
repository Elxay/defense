from pathlib import Path
import json,pwd,subprocess
rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().splitlines()
procs=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'],text=True).strip().splitlines();ps=[]
for row in procs:
 if not row.strip():continue
 uuid,pid,mem=map(str.strip,row.split(','));p=Path('/proc')/pid
 try:
  status=p.joinpath('status').read_text();uid=int(next(x for x in status.splitlines() if x.startswith('Uid:')).split()[1]);args=p.joinpath('cmdline').read_bytes().split(bytes([0]));scripts=[Path(x.decode(errors='replace')).name for x in args if x.endswith(b'.py')]
  command=scripts[0] if scripts else p.joinpath('comm').read_text().strip();account=pwd.getpwuid(uid).pw_name
 except OSError:command='exited';account=None
 ps.append(dict(uuid=uuid,pid=int(pid),memory_MiB=mem,account=account,command_basename=command))
out=[]
for row in rows:
 i,uuid,mem,util=map(str.strip,row.split(','));out.append(dict(card=int(i),uuid=uuid,memory_MiB=int(mem),utilization=int(util),processes=[p for p in ps if p['uuid']==uuid]))
print(json.dumps(out))
