"""Wait for the owned dispatcher to drain; preserve every pre-handoff row."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import time

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
    old=1380947
    while Path('/proc',str(old)).exists():time.sleep(5)
    before=json.loads((BASE/'gpu0_handoff_prefix_before.json').read_text())
    assert all(sha(ROOT/name)==value for name,value in before['files'].items())
    while not(BASE/'gpu0_zero20_result.json').exists():time.sleep(5)
    receipt={'utc':utc(),'old_controller_pid':old,'old_controller_exited':True,'preexisting_rows_verified_unchanged':len(before['files']),'gate_passed':json.loads((BASE/'gpu0_zero20_result.json').read_text())['passed'],'handoff_supervisor_pid':os.getpid()}
    (BASE/'gpu0_handoff_checked.json').write_text(json.dumps(receipt,indent=2)+'\n')
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{utc()} GPU0_THREE_LANE_HANDOFF oldPID={old} drained; all{len(before["files"])} preexisting rows SHA unchanged; handoffSHA={sha(BASE/"gpu0_handoff_checked.json")}; new master launched through registry, GPU0 remains gated and expires18JST.\n')
    shell=f'''set -euo pipefail
cd {ROOT}
source night/launch.sh
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
NOGPU=1 launch_job /home/kemove/anaconda3/envs/HZX_GLA/bin/python -u tools/handoff_20261106/prefix_controller_borrowed.py
'''
    with (ROOT/'logs/prefix254_borrowed_controller.log').open('ab',buffering=0) as log:
        proc=subprocess.Popen(['bash','-s'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);proc.stdin.write(shell.encode());proc.stdin.close()
    launched={'utc':utc(),'launcher_pid':proc.pid,'checked_receipt_sha256':sha(BASE/'gpu0_handoff_checked.json')};(BASE/'gpu0_handoff_launch.json').write_text(json.dumps(launched,indent=2)+'\n');print(json.dumps({**receipt,**launched}))

if __name__=='__main__':main()
