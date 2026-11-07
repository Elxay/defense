"""Status table for the PAIR search and the checkpointed competing work."""
import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/audit/pair500"


def remote():
    code = """
from pathlib import Path
import json, subprocess
a=Path('/home/dell/Def/results/audit')
r=a/'pair500'
out={}
for p in [r/'generation_live.json',a/'handoff_round11/noise_B_launcher_live.json',a/'handoff_round12/same_alpha_s3_launcher_live.json',a/'handoff_round12/same_alpha_s5_launcher_live.json',*(a/f'handoff_round11/generate_grid_s{s}_live.json' for s in (3,4,5))]:
 if p.exists():out[p.stem]=json.loads(p.read_text())
handoff=r/'priority_checkpoint_handoff.json'
out['paused_grid']=json.loads(handoff.read_text()) if handoff.exists() else {}
out['full_start_utc']=(r/'full_start_utc').read_text().strip() if (r/'full_start_utc').exists() else None
import os,time
times=[]
saved_files=list((r/'generations.private').glob('*.json'))
worker=out.get('generation_live',{})
pid=worker.get('pid')
try:
 cmd=(Path('/proc')/str(pid)/'cmdline').read_bytes().replace(bytes([0]),b' ').decode()
 alive='pair500_search_telemetry.py' in cmd or 'pair500_generate.py' in cmd
except FileNotFoundError:
 alive=False
out['worker_alive']=alive
out['worker_cmd']=cmd if alive else None
out['latest_output_epoch']=max((p.stat().st_mtime for p in saved_files),default=0)
out['output_age_s']=time.time()-out['latest_output_epoch']
out['gpu_processes']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'],text=True).splitlines()
out['gpu_inventory']=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used','--format=csv,noheader'],text=True).splitlines()
for p in (r/'generations.private').glob('*.json'):
 d=json.loads(p.read_text());times.append(d['seconds'])
out['done_rows']=len(times)
out['seconds_per_row']=sum(times)/len(times) if times else None
out['gpu_mib']=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used','--format=csv,noheader,nounits'],text=True).splitlines()
print(json.dumps(out))
"""
    return json.loads(subprocess.check_output(
        ["ssh", "-o", "ConnectTimeout=10", "node01", "python3", "-"], input=code, text=True, timeout=20,
    ))


def main():
    node = remote()
    t = datetime.datetime.now(datetime.timezone.utc)
    records = []
    def add(name, detail, gpu, progress, rate=None, active=True):
        age = (t - datetime.datetime.fromisoformat(detail["utc"].replace("Z", "+00:00"))).total_seconds()
        records.append(dict(name=name, pid=detail.get("pid"), gpu=gpu, progress=progress,
                            seconds_per_row=rate, heartbeat_age_s=round(max(0,age),1),
                            alert="🔴 心跳超过 10 分钟" if active and age >= 600 else None,
                            phase=detail.get("phase","generation")))
    queue = json.loads((OUT / "full_queue_live.json").read_text())
    phase = "running" if node["worker_alive"] else "waiting_cards"
    if node["full_start_utc"] and node["done_rows"] < 500 and node["output_age_s"] > 900:
        phase = "stalled"
    if node["done_rows"] == 500:
        phase = "complete"
    queue = {**queue, "phase": phase, "stage_record_utc": queue["utc"],
             "observed_utc": t.isoformat(), "worker_alive": node["worker_alive"],
             "output_age_s": round(node["output_age_s"], 1)}
    add("PAIR 搜索控制器",queue,"CPU",f"{node['done_rows']}/500",node["seconds_per_row"],
        active=False)
    records[-1]["heartbeat_source"] = "controller stage transition, not a periodic heartbeat"
    if phase == "stalled":
        records[-1]["alert"] = "🔴 落盘超过 15 分钟未增长"
    w={**node["generation_live"], "phase": phase}
    add("node01 PAIR worker",w,",".join(w["gpus"]),
        f"{node['done_rows']}/500",node["seconds_per_row"],active=w["phase"]!="complete")
    for seed in (3,4,5):
        x=node.get(f"generate_grid_s{seed}_live")
        if x:
            pause = node["paused_grid"].get(str(seed))
            paused = pause is not None and pause["pid"] == x["pid"]
            if paused:
                x = {**x, "phase": "checkpoint_paused", "n": pause["checkpoint_n"]}
            add(f"第三臂 s{seed} 网格",x,f"node01:{x['physical_gpu']}",
                f"{x.get('alpha','')} {x.get('n','—')}/{x.get('total','—')}",
                x.get("seconds_per_item"), not paused and x["phase"]!="complete")
    for shard in (0,1):
        p=OUT/f"public_wjb_gen{shard}_live.json"
        if p.exists():
            x=json.loads(p.read_text())
            add(f"WildJailbreak 官方 eval α0 分片 {shard}",x,f"innet:{x['card']}",f"{x['n']}/{x['of']}",x["seconds_per_row"],x["n"]<x["of"])
    d=dict(utc=t.isoformat(),rows=records,queue=queue,node_gpu_mib=node["gpu_mib"],
           full_start_utc=node["full_start_utc"], worker_alive=node["worker_alive"],
           output_age_s=round(node["output_age_s"],1), node_gpu_processes=node["gpu_processes"],
           node_gpu_inventory=node["gpu_inventory"])
    print(json.dumps(d,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
