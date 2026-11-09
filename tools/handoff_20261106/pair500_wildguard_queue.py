"""Score the canonical PAIR snapshot on node01 GPU0, without reading effects."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/data/HZX/Def')
BASE = ROOT / 'results/audit/pair500'
OUT = BASE / 'wildguard_pair254'
REMOTE = '/home/dell/Def/results/audit/pair500/wildguard_pair254'
NAMES = ['alpha0', 'old_s3', 'rand0', 'old_s4', 'rand1', 'old_s5', 'rand2', 'old_s6', 'rand3', 'old_s7', 'old_s0', 'SYS_A', 'SYS_B']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    t = path.with_suffix('.tmp')
    t.write_text(json.dumps(value, indent=2) + '\n')
    t.replace(path)


def pulse(phase, name=None):
    save(OUT / 'queue_live.json', {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'pid': os.getpid(), 'phase': phase, 'condition': name})


def main():
    os.umask(0o077)
    while not (BASE / 'frozen_prompt_snapshot.json').exists():
        pulse('waiting_search_snapshot'); time.sleep(30)
    while not (BASE/'prefix_wg_drained.json').exists():
        pulse('waiting_prefix_wildguard_batch_boundary');time.sleep(15)
    # This queue does not pre-empt the higher-priority WJB harmful classifier.
    nine = ['old_s3', 'rand0', 'old_s4', 'rand1', 'old_s5', 'rand2', 'old_s6', 'rand3', 'old_s7']
    while not all(len(list((BASE / 'wildguard' / (name + '_scores')).glob('*.json'))) == 2000 for name in nine):
        state = json.loads((BASE / 'wildguard/conditions_queue_live.json').read_text())
        trigger = BASE / 'pair_priority_trigger.json'
        if (trigger.exists() and json.loads(trigger.read_text()).get('active')
                and state['phase'] == 'waiting_complete_target_outputs'):
            # A WJB primary unit may itself be paused for PAIR priority. It
            # cannot be a dependency of the job needed to release those lanes.
            break
        pulse('waiting_wjb_wildguard'); time.sleep(30)
    subprocess.run(['ssh', 'node01', 'mkdir', '-p', REMOTE], check=True)
    worker = ROOT / 'tools/handoff_20261106/pair500_wildguard_run.py'
    subprocess.run(['scp', str(worker), 'node01:/home/dell/Def/tools/handoff_20261106/pair500_wildguard_run.py'], check=True)
    snapshot = json.loads((BASE / 'frozen_prompt_snapshot.json').read_text())
    rows = {r['id']: r for r in json.loads((BASE / 'rows.private.json').read_text())}
    for name in NAMES:
        folder = BASE / 'canonical254/generation.private' / name
        keys = [r['id'] for r in snapshot['rows']]
        while not all((folder / (k + '.json')).exists() for k in keys):
            pulse('waiting_complete_target_condition', name); time.sleep(30)
        route=BASE/'prefix254/resource_route.json'
        while route.exists() and json.loads(route.read_text()).get('fallback') and not (BASE/'prefix254/node_lane0_complete.json').exists():
            pulse('waiting_node01_gpu0_target_lane',name);time.sleep(15)
        payload = []; hashes = {}
        for key in keys:
            g = folder / (key + '.json'); a = BASE / 'generations.private' / (key + '.json')
            generation = json.loads(g.read_text())
            assert generation['signature']['snapshot_sha256'] == sha(BASE / 'frozen_prompt_snapshot.json')
            hashes[key] = sha(g)
            payload.append({'id': key, 'prompt': json.loads(a.read_text())['best']['prompt'],
                            'response': generation['result']['text'], 'layer': rows[key]['layer']})
        private = OUT / (name + '_inputs.private.json'); save(private, payload)
        save(OUT / (name + '_input_manifest.json'), {'n': len(keys), 'input_sha256': sha(private),
             'snapshot_sha256': sha(BASE / 'frozen_prompt_snapshot.json'), 'generation_sha256': hashes,
             'worker_sha256': sha(worker)})
        from prefix_wg_reuse import import_verified
        reused=import_verified(name,payload,sha(private))
        if reused:
            subprocess.run(['rsync','-a','--ignore-existing',str(OUT/(name+'_scores'))+'/', 'node01:'+REMOTE+'/'+name+'_scores/'],check=True)
        save(OUT/(name+'_prefix_reuse_receipt.json'),{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reused_rows':reused,'no_effect_summary':True})
        subprocess.run(['scp', str(private), 'node01:' + REMOTE + '/' + private.name], check=True)
        pulse('remote_gpu0_dispatched', name)
        shell = f'''set -euo pipefail
cd /home/dell/Def
source tools/handoff_20261106/node01_launch_round9.sh
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
export HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0
exec 8>>logs/idle_gpu0.lock
flock 8
until wait_gpu cuda:0; do sleep 15; done
DEVICE=cuda:0 launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 /data/ray/env/bin/python -u tools/handoff_20261106/pair500_wildguard_run.py {name}
'''
        with (ROOT / 'logs/pair500_wildguard_queue.log').open('ab', buffering=0) as log:
            subprocess.run(['ssh', 'node01', 'bash', '-s'], input=shell.encode(), stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run(['rsync', '-a', 'node01:' + REMOTE + '/' + name + '_scores/', str(OUT / (name + '_scores')) + '/'], check=True)
        for suffix in ['_done.json', '_live.json']:
            subprocess.run(['scp', 'node01:' + REMOTE + '/' + name + suffix, str(OUT / (name + suffix))], check=True)
        pulse('condition_complete_no_effect_read', name)
    pulse('all_conditions_complete_no_effect_read')


if __name__ == '__main__':
    main()
