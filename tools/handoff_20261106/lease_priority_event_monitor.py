"""Observe first deployment events; never open outcome-label files."""
from pathlib import Path
import datetime,json,time
BASE=Path('/data/HZX/Def/results/audit/pair500');S=BASE/'lease_priority'
def main():
    seen=set();end=time.monotonic()+2700
    while time.monotonic()<end:
        p=S/'controller_live.json'
        if p.exists():
            x=json.loads(p.read_text())
            if x['phase']=='failed':print(json.dumps({'event':'controller_failed','state':x}),flush=True);return
        if 'caught'not in seen:
            caught=sorted((S/'caught_up').glob('*.json'),key=lambda p:p.stat().st_mtime)
            if caught:seen.add('caught');print(json.dumps({'event':'caught','record':json.loads(caught[0].read_text())}),flush=True)
        if 'tail'not in seen:
            paths=list(S.glob('tail_live_gpu*.json'))
            if paths:seen.add('tail');print(json.dumps({'event':'tail_first_rows','records':[json.loads(p.read_text())for p in paths]}),flush=True)
        if 'HBready'not in seen:
            paths=list((S/'hb_windows').glob('*/ready.json'))
            if paths:seen.add('HBready');print(json.dumps({'event':'HB_reference_gate_passed','record':json.loads(paths[0].read_text())}),flush=True)
        if seen=={'caught','tail','HBready'}:return
        time.sleep(10)
    print(json.dumps({'event':'bounded_monitor_end','seen':sorted(seen),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}),flush=True)
if __name__=='__main__':main()
