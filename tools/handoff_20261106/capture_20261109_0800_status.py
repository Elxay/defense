"""One requested morning snapshot of operational metadata, without labels."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/data/HZX/Def')
BASE=ROOT/'results/audit/pair500'
DUE=datetime.datetime(2026,11,8,23,tzinfo=datetime.timezone.utc)


def main():
    dest=BASE/'morning_20261109_0800_status.json'
    if dest.exists():return
    while datetime.datetime.now(datetime.timezone.utc)<DUE:
        p=BASE/'morning_0800_capture_live.json';t=p.with_suffix('.tmp')
        t.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'phase':'waiting_0800_JST','due_utc':DUE.isoformat()},indent=2)+'\n');t.replace(p)
        time.sleep(30)
    sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
    from operational_metadata import capture
    x=capture()
    x['requested_jst']='2026-11-09T08:00:00+09:00'
    temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');temp.replace(dest)
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{x["utc"]} REQUESTED_0800JST_STATUS_CAPTURED SHA={hashlib.sha256(dest.read_bytes()).hexdigest()} progress/timing only; no outcome labels loaded.\n')


if __name__=='__main__':main()
