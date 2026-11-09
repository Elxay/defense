"""Operational snapshot only: progress, timing, processes and file counts."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500'
sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
from operational_metadata import capture

def main():
    x=capture();now=datetime.datetime.now(datetime.timezone.utc)
    live=[]
    for p in (BASE/'prefix254/live').glob('*.json'):
        v=json.loads(p.read_text())
        if Path('/proc',str(v.get('pid',0))).exists():
            v={k:v[k] for k in ['utc','pid','phase','condition','device','done','total','seconds_per_row'] if k in v}
            v['heartbeat_age_s']=(now-datetime.datetime.fromisoformat(v['utc'])).total_seconds();live.append(v)
    x['prefix_active_workers']=live
    x['dual_controller']=json.loads((BASE/'prefix254/dual_live.json').read_text())
    x['early_wg_progress']=json.loads((BASE/'prefix_wildguard_live.json').read_text())
    x['early_wg_cached_rows']={p.stem:len(json.loads(p.read_text())) for p in (BASE/'prefix254/wg_pre_index').glob('*.json')}
    x['nvidia_processes_innet']=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader'],text=True).splitlines()
    x['node01_processes']=subprocess.check_output(['ssh','node01',"nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader"],text=True).splitlines()
    x['utc']=now.isoformat();x['reads_outcome_labels']=False
    out=BASE/'public_nine_completion_status.json';out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'utc':x['utc'],'pair':x['pair'],'prefix_workers':live,'coverage':x['prefix_generation_coverage'],'early_wg':x['early_wg_progress'],'early_wg_cached_rows':x['early_wg_cached_rows'],'node_gpu_memory':x['gpu_memory'],'innet_gpu_memory':x['innet_gpu_memory'],'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},ensure_ascii=False))

if __name__=='__main__':main()
