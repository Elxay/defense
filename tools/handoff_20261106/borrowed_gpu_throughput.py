"""Measured generation timing only; no response or judge-label inspection."""
from pathlib import Path
import datetime
import hashlib
import json
import statistics

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';PREFIX=BASE/'prefix254'
def main():
    now=datetime.datetime.now(datetime.timezone.utc);names=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B'];finished={n:[] for n in names}
    for p in (PREFIX/'live').glob('*.json'):
        x=json.loads(p.read_text());name=x.get('condition')
        if name in finished and x.get('phase')=='generation' and x.get('done')==x.get('total') and x.get('done',0)>=25 and x.get('seconds_per_row'):
            finished[name].append(x)
    rows=[];work=0;accepted_work=0;source=json.loads((PREFIX/'triple_live.json').read_text())['source_rows']
    for n in names:
        batches=sorted(finished[n],key=lambda x:x['utc'])[-3:];assert batches,n
        seconds=sum(x['done']*x['seconds_per_row'] for x in batches)/sum(x['done'] for x in batches)
        done=len(list((PREFIX/'generation.private'/n).glob('*.json')));work+=(500-done)*seconds;accepted_work+=max(0,source-done)*seconds
        rows.append({'condition':n,'saved_rows':done,'timed_completed_rows':sum(x['done'] for x in batches),'completed_batches_used':len(batches),'seconds_per_row':seconds,'rows_per_hour_per_active_card':3600/seconds,'source_worker_pids':[x['pid'] for x in batches]})
    result={'utc':now.isoformat(),'rows':rows,'accepted_source_rows':source,'remaining_to_accepted_prefix_gpu_hours':accepted_work/3600,'remaining_to500_gpu_hours':work/3600,'load_wait_excluded':True,'reading_labels':False,'ETA_interpretation':'Work estimate uses the last up-to-three completed >=25-row timing batches per condition, not a1.5x throughput claim. Counts are moving snapshots. Loading, contention, future prompt lengths, search closure and classifier windows add time. Borrowed GPU0 expires18JST. Final completion cannot precede the still-running PAIR search; do not turn card-hours into a promised finish time.'}
    p=BASE/'borrowed_gpu_measured_throughput.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
