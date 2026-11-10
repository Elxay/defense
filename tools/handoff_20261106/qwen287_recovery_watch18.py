"""Failure-only shard1 lease; never reads judge labels or candidate effects."""
from pathlib import Path
import datetime, fcntl, hashlib, json, os, shlex, subprocess, time

R = Path('/data/HZX/Def')
NR = Path('/home/dell/Def')
C = R / 'results/audit/crossmodel287'
O = C / 'node_recovery18'
D = C / 'qwen_selection'
NO = NR / O.relative_to(R)

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    q = p.with_name(p.name + '.tmp')
    q.write_text(json.dumps(x, indent=2) + '\n'); q.replace(p)
def pulse(phase, **kw):
    save(O / 'recovery_watch_live.json', dict(utc=utc(), pid=os.getpid(), phase=phase, effects_read=False, **kw))
def remote(code):
    return subprocess.check_output(['ssh', 'node01', '/data/ray/env/bin/python', '-'], input=code, text=True)
def node_json(p):
    return json.loads(remote('import pathlib,json\np=pathlib.Path(' + repr(str(p)) + ')\nprint(p.read_text() if p.exists() else "null")'))
def copy_files(paths, direction):
    listing = O / ('transfer_' + direction + '.txt')
    listing.write_text(''.join(p + '\n' for p in sorted(paths)))
    args = ['rsync', '-a', '--ignore-existing', '--files-from=' + str(listing)]
    if direction == 'adopt': args += [str(R) + '/', 'node01:' + str(NR) + '/']
    else: args += ['node01:' + str(NR) + '/', str(R) + '/']
    subprocess.run(args, check=True)

def producer_alive(route):
    p = Path('/proc') / str(route['producer_pid']) / 'stat'
    try:
        fields = p.read_text().rsplit(')', 1)[1].split()
        return fields[0] != 'Z' and fields[19] == route['producer_start_ticks']
    except FileNotFoundError: return False

def main():
    lock = (O / 'recovery_lease.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    admission = load(O / 'watch_plan.json')
    assert sha(Path(__file__)) == admission['watcher_sha256']
    assert sha(O / 'recovery_plan.json') == admission['route_sha256']
    route = load(O / 'recovery_plan.json'); plan = load(D / 'plan.json')
    assert sha(D / 'plan.json') == route['original_plan_sha256']
    names = [f's{s}_a{a:g}' for s in [3, 4, 5] for a in plan['alpha_grid']]
    def complete(): return all((D / 'condition_done' / (n + '_shard1.json')).exists() for n in names)
    while producer_alive(route):
        if complete():
            pulse('all21_original_complete_no_recovery'); return
        last = (D / 'live_1.json').stat().st_mtime
        age = time.time() - last
        pulse('stale_original_do_not_duplicate' if age > 900 else 'original_running_no_migration', heartbeat_age_seconds=round(age, 1))
        time.sleep(30)
    if complete():
        pulse('all21_original_complete_no_recovery'); return
    # A separately restarted original producer must never overlap recovery.
    matches = subprocess.run(['pgrep', '-af', 'qwen287_selection_generate.py'], text=True, capture_output=True).stdout.splitlines()
    if any('qwen287_selection_generate.py 1 3' in line for line in matches):
        raise RuntimeError('A replacement shard1 producer exists; stop rather than duplicate')
    save(O / 'producer_failure.json', dict(utc=utc(), producer_pid=route['producer_pid'], reason='Original producer exited before all21 markers; cause not inferred', effects_read=False))
    pending = dict(utc=utc(), route_sha256=sha(O / 'recovery_plan.json'), owner='qwen_shard1_recovery18')
    save(O / 'recovery_pending.json', pending)
    subprocess.run(['scp', str(O / 'recovery_pending.json'), 'node01:' + str(NO / 'recovery_pending.json')], check=True)
    gates = node_json(NO / 'generation_gates_complete.json')
    assert gates and gates['passed'], 'Byte gates missing/failed; recovery blocked'
    inputs = load(C / 'native_selection_inputs.private.json')
    rows = [('legal400', r) for i in range(0, 400, 8) if (i // 8) % 2 == 1 for r in inputs['legal400'][i:i+8]]
    rows += [('val70', r) for i, r in enumerate(inputs['val70']) if i % 2 == 1]
    assert len(rows) == 235
    files = {}
    for s in [3, 4, 5]:
        for a in plan['alpha_grid']:
            n = f's{s}_a{a:g}'
            for kind, row in rows:
                p = D / 'generation.private' / n / kind / (row['id'] + '.json')
                if not p.exists(): continue
                x = load(p); sig = x['signature']
                assert x['prompt_sha256'] == row['prompt_sha256']
                assert sig['plan_sha256'] == route['original_plan_sha256']
                assert sig['vector_file_sha256'] == plan['vector_sha256'][str(s)] and sig['alpha'] == a
                assert sig['device_uuid'] == route['original_producer_device_uuid']
                files[str(p.relative_to(R))] = sha(p)
    adoption = dict(utc=utc(), producer_failed=True, route_sha256=sha(O / 'recovery_plan.json'), files=files)
    save(O / 'adoption_manifest.json', adoption)
    copy_files(files, 'adopt')
    subprocess.run(['scp', str(O / 'adoption_manifest.json'), 'node01:' + str(NO / 'adoption_manifest.json')], check=True)
    # Verify adopted bytes before a generation model can load.
    verified = remote('import pathlib,json,hashlib\nR=pathlib.Path("/home/dell/Def")\na=json.loads((R/' + repr(str((O / 'adoption_manifest.json').relative_to(R))) + ').read_text())\nassert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in a["files"].items())\nprint(len(a["files"]))')
    pulse('adopted_bytes_verified_waiting_GPU2', adopted_files=int(verified))
    worker = NR / 'tools/handoff_20261106/qwen287_recover_shard1_18.py'
    shell = '''set -e
cd /home/dell/Def
source /home/dell/Def/tools/handoff_20261106/node01_launch_round9.sh
exec 8>>logs/idle_gpu2.lock
flock 8
unset NOGPU
export DEVICE=cuda:2
while ! wait_gpu "$DEVICE"; do sleep 15; done
launch_job env CUDA_VISIBLE_DEVICES=2 DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 /data/ray/env/bin/python -u ''' + shlex.quote(str(worker)) + '\n'
    with (O / 'node_launch.log').open('a') as log:
        proc = subprocess.Popen(['ssh', 'node01', 'bash', '-s'], stdin=subprocess.PIPE, stdout=log, stderr=log, text=True)
        proc.stdin.write(shell); proc.stdin.close()
        merged = set()
        while True:
            for n in names:
                dest = D / 'condition_done' / (n + '_shard1.json')
                if dest.exists(): continue
                m = node_json(NO / 'recovered_conditions' / (n + '.json'))
                if not m: continue
                assert m['plan_sha256'] == route['original_plan_sha256'] and m['route_sha256'] == sha(O / 'recovery_plan.json')
                expected = {str((D / 'generation.private' / n / k / (r['id'] + '.json')).relative_to(R)) for k,r in rows}
                assert set(m['files']) == expected and len(expected) == 235
                copy_files(expected, 'return')
                assert all(sha(R / p) == h for p,h in m['files'].items()), 'Merge mismatch; never overwrite original'
                save(dest, dict(utc=utc(), plan_sha256=route['original_plan_sha256'], n_legal=200, n_val=35, recovery_route_sha256=sha(O / 'recovery_plan.json'), source_manifest_sha256=hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()))
                merged.add(n)
            pulse('recovery_running_or_waiting_GPU2', merged_conditions=sorted(merged))
            if complete(): break
            if proc.poll() is not None:
                raise RuntimeError('Recovery process exited before all condition markers; pending lease retained')
            time.sleep(20)
        rc = proc.wait(timeout=60)
        assert rc == 0
    # Remove only our own request by archiving it; Gemma may now resume.
    (O / 'recovery_pending.json').replace(O / 'recovery_pending.completed.json')
    remote('from pathlib import Path\np=Path(' + repr(str(NO / 'recovery_pending.json')) + ')\np.replace(p.with_name("recovery_pending.completed.json"))')
    pulse('recovery_complete_Gemma_released', merged_conditions=sorted(merged))

if __name__ == '__main__':
    try: main()
    except Exception as e:
        pulse('blocked_no_gate_relaxation', error=type(e).__name__ + ': ' + str(e))
        raise
