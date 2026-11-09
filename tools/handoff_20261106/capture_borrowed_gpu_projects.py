"""Project-aware GPU inventory; command names and registry lineage, no environments."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import pwd
import subprocess

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    remote=r'''from pathlib import Path
import datetime,json,pwd,subprocess
root=Path('/home/dell/Def');reg=(root/'logs/pid_registry.txt').read_text().splitlines();rows=[]
raw=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader'],text=True)
for line in raw.splitlines():
 fields=[x.strip() for x in line.split(',')]
 if len(fields)!=3:continue
 pid=int(fields[0]);p=Path('/proc',str(pid));cmd=(p/'cmdline').read_bytes().replace(b'\x00',b' ').decode();parent=int((p/'stat').read_text().split(') ',1)[1].split()[1]);registered=[s.split('|',1)[0] for s in reg if s.startswith((str(pid)+'|',str(parent)+'|'))]
 rows.append({'pid':pid,'ppid':parent,'gpu_uuid':fields[1],'memory':fields[2],'account':pwd.getpwuid(p.stat().st_uid).pw_name,'project':'Def/PAIR-search' if 'pair500_search_telemetry.py' in cmd else 'Def/early-WildGuard' if 'prefix_wg_batch_runner.py' in cmd else 'unidentified','registry_pids':registered,'command':cmd})
batch_workers=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:cmd=(p/'cmdline').read_bytes().replace(b'\x00',b' ').decode()
 except (OSError,UnicodeDecodeError):continue
 if 'tools/handoff_20261106/prefix_wg_batch_runner.py --batch ' in cmd and cmd.startswith('/data/ray/env/bin/python'):
  batch_workers.append({'pid':int(p.name),'account':pwd.getpwuid(p.stat().st_uid).pw_name,'registry_pids':[s.split('|',1)[0] for s in reg if s.startswith(p.name+'|')],'command':cmd,'CUDA_context_currently_listed':any(r['pid']==int(p.name) for r in rows)})
display=[]
for pid in [2142,2311,4155,4270,4522,4595,4617,4684]:
 p=Path('/proc',str(pid))
 if p.exists():display.append({'pid':pid,'account':pwd.getpwuid(p.stat().st_uid).pw_name,'command_name':(p/'comm').read_text().strip(),'project':'system desktop/remote desktop, not Def compute'})
base=root/'results/audit/pair500';live=json.loads((base/'generation_live.json').read_text());data=[json.loads(p.read_text())['seconds'] for p in (base/'generations.private').glob('*.json')]
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'compute':rows,'early_WG_batch_workers':batch_workers,'display_processes':display,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu,temperature.gpu,clocks.current.sm','--format=csv,noheader'],text=True).splitlines(),'pair':{'completed_rows':len(data),'seconds_per_row':sum(data)/len(data),'worker_pid':live['pid'],'heartbeat_utc':live['utc'],'historical_restart_count':1}}))
'''
    node=json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=remote,text=True))
    reg=(ROOT/'logs/pid_registry.txt').read_text().splitlines();rows=[]
    raw=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader'],text=True)
    for line in raw.splitlines():
        fields=[x.strip() for x in line.split(',')]
        if len(fields)!=3:continue
        pid=int(fields[0]);p=Path('/proc',str(pid));cmd=(p/'cmdline').read_bytes().replace(b'\x00',b' ').decode();parent=int((p/'stat').read_text().split(') ',1)[1].split()[1]);registered=[s.split('|',1)[0] for s in reg if s.startswith((str(pid)+'|',str(parent)+'|'))]
        project='MTA (external to Def)' if '/data/wangjiahui/MTA' in cmd else 'Urban3D point-cloud project (external; operator unconfirmed)' if 'train_unregistered_stage2.py' in cmd and '/data/PanTeng/Urban3D/' in cmd else 'Def/prefix-generation' if 'prefix_generate' in cmd else 'Def/public-400-followup' if 'public_uncertain400.py' in cmd else 'unidentified'
        rows.append({'pid':pid,'ppid':parent,'gpu_uuid':fields[1],'memory':fields[2],'account':pwd.getpwuid(p.stat().st_uid).pw_name,'project':project,'registry_pids':registered,'command':cmd})
    triple=BASE/'prefix254/triple_live.json';live=json.loads(triple.read_text()) if triple.exists() else None
    active=[]
    for p in (BASE/'prefix254/live').glob('*.json'):
        x=json.loads(p.read_text())
        if Path('/proc',str(x['pid'])).exists():active.append(x)
    timings={}
    for p in (BASE/'prefix254/generation.private').glob('*/*.json'):
        x=json.loads(p.read_text())
        if 'row_seconds' not in x:continue
        key=x['signature']['condition']+'/'+x['physical_gpu'];timings.setdefault(key,[]).append(x['row_seconds'])
    timing={key:{'n':len(v),'seconds_per_row':sum(v)/len(v),'rows_per_hour':3600*len(v)/sum(v)} for key,v in timings.items()}
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'innet':{'compute':rows,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu,temperature.gpu,clocks.current.sm','--format=csv,noheader'],text=True).splitlines()},'node01':node,'triple_dispatcher':live,'active_prefix_workers':active,'measured_new_worker_throughput':timing,'read_PAIR_outcomes':False,'interpretation':'OS account does not identify project. PAIR target/attacker alternate; instantaneous0 utilization is not a waiting/stall diagnosis. Historical PAIR restart count remains1.'}
    p=BASE/'borrowed_gpu_projects_status.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
