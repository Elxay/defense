"""Wait for verified assets, mirror them, and run only five frozen fixtures."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path('/data/HZX/Def');MODEL=ROOT/'models/WildGuard';OUT=ROOT/'results/audit/pair500/wildguard'
OUT.mkdir(parents=True,exist_ok=True)


def pulse(stage):
    import os
    p=OUT/'fixture_queue_live.json';t=p.with_suffix('.tmp')
    t.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'stage':stage}));t.replace(p)


while not (MODEL/'DOWNLOAD_SHA256.json').exists():
    pulse('waiting_download_manifest');time.sleep(15)
pulse('verifying_innet_assets')
record=json.loads((MODEL/'DOWNLOAD_SHA256.json').read_text())
assert record['revision']=='cbba4823f3e8020e5a74a5e29bf85072def6f2ff'
for name,expected in record['files'].items():
    with (MODEL/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
expected=json.loads((ROOT/'results/audit/pair500/wildguard_expected_shards.json').read_text())
assert all(record['files'][name]==row['expected_sha256'] for name,row in expected.items())
pulse('copying_assets_to_node01')
subprocess.run(['ssh','node01','mkdir','-p','/home/dell/Def/models/WildGuard'],check=True)
subprocess.run(['rsync','-a','--partial',str(MODEL)+'/', 'node01:/home/dell/Def/models/WildGuard/'],check=True)
subprocess.run(['scp',str(ROOT/'tools/handoff_20261106/wildguard_format.py'),'node01:/home/dell/Def/tools/handoff_20261106/wildguard_format.py'],check=True)
pulse('waiting_node01_gpu0_or_running_fixtures')
shell='''set -euo pipefail
cd /home/dell/Def
source tools/handoff_20261106/node01_launch_round9.sh
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu0.lock
flock 8
until wait_gpu cuda:0; do sleep 15; done
DEVICE=cuda:0 launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 /data/ray/env/bin/python -u tools/handoff_20261106/wildguard_format.py
'''
subprocess.run(['ssh','node01','bash','-s'],input=shell,text=True,check=True)
pulse('copying_fixture_outputs')
subprocess.run(['scp','node01:/home/dell/Def/results/audit/pair500/wildguard/format5.json',str(OUT/'format5.json')],check=True)
assert json.loads((OUT/'format5.json').read_text())['passed_format']
with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:
    f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} WILDGUARD_FORMAT5_COMPLETE labels saved; no dataset batch started. Cross-node20 remains pending.\n')
pulse('format5_complete_no_dataset_batch')
