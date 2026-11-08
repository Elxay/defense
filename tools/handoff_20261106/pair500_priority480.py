"""Pause owned WJB tails at actual PAIR >=480; resume after canonical GPU work."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/data/HZX/Def')
BASE = ROOT / 'results/audit/pair500'
TAIL = {'old_s7', 'old_s0', 'SYS_A', 'SYS_B'}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, x):
    path.parent.mkdir(parents=True, exist_ok=True)
    t = path.with_suffix('.tmp'); t.write_text(json.dumps(x, indent=2) + '\n'); t.replace(path)


def pulse(phase, **extra):
    save(BASE / 'pair_priority480_live.json', {'utc': utc(), 'pid': os.getpid(), 'phase': phase, **extra})


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def should_pause(rows, snapshot):
    return rows >= 480 or snapshot


def observed_rows():
    code = """from pathlib import Path
import json,hashlib
b=Path('/home/dell/Def/results/audit/pair500')
assert hashlib.sha256((b/'config.json').read_bytes()).hexdigest()=='9e46b2e78bb191363b1dadbe458815871a00f8e9f91cea0202687ca70a83fca1'
allowed={r['id'] for r in json.loads((b/'rows.private.json').read_text())}
ids=sorted(p.stem for p in (b/'generations.private').glob('*.json'))
assert len(ids)==len(set(ids)) and set(ids)<=allowed
print(json.dumps({'n':len(ids),'ids_sha256':hashlib.sha256(('\\n'.join(ids)+'\\n').encode()).hexdigest()}))
"""
    return json.loads(subprocess.check_output(['ssh', 'node01', 'python3', '-'], input=code, text=True, timeout=30))


def checkpoint():
    files = {}
    for folder in ['harmful.private', 'mapped_scores']:
        for name in sorted(TAIL):
            for p in (BASE / 'public255' / folder / name).rglob('*.json'):
                files[str(p.relative_to(BASE))] = sha(p)
    return files


def stop_owned_tails():
    stopped = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit(): continue
        try:
            args = [a.decode() for a in proc.joinpath('cmdline').read_bytes().split(b'\0') if a]
            if not any(a.endswith('/wjb_eval255_run.py') for a in args): continue
            if not (TAIL & set(args)) or not ({'harmful', 'score'} & set(args)): continue
            if b'DSH_OWNER=/data/HZX/Def' not in proc.joinpath('environ').read_bytes().split(b'\0'): continue
            subprocess.run(['bash', str(ROOT / 'night/safe_kill.sh'), proc.name], check=True)
            stopped.append(int(proc.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError): continue
    return stopped


def main():
    trigger = BASE / 'pair_priority_trigger.json'
    while not trigger.exists():
        try:
            observed = observed_rows()
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            pulse('row_count_unavailable_no_action', error=type(e).__name__); time.sleep(30); continue
        snapshot = (BASE / 'frozen_prompt_snapshot.json').exists()
        if should_pause(observed['n'], snapshot):
            save(trigger, {'utc': utc(), 'active': True, 'reason': 'actual_rows_ge480' if observed['n']>=480 else 'frozen_cutoff_prefix', **observed})
            break
        pulse('waiting_actual_480_rows', **observed); time.sleep(30)
    if not json.loads(trigger.read_text()).get('active'): return
    stopped = []
    for _ in range(4):
        stopped += stop_owned_tails(); time.sleep(2)
    manifest = BASE / 'pair_priority_checkpoint.json'
    if manifest.exists():
        before_resume = json.loads(manifest.read_text())['files']
    else:
        before_resume = checkpoint()
        save(manifest, {'utc': utc(), 'stopped_pids': sorted(set(stopped)), 'files': before_resume})
        with (ROOT / 'docs/PREREG_LOG.txt').open('a') as f:
            f.write(f'{utc()} WJB_PAUSE_PAIR480 triggerSHA={sha(trigger)} checkpointSHA={sha(manifest)} pids={sorted(set(stopped))}; atomic rows retained, at most one in-flight row lost per worker.\n')
    while True:
        p = BASE / 'full_queue_live.json'
        state = json.loads(p.read_text()) if p.exists() else {}
        if state.get('phase') == 'complete': break
        pulse('waiting_canonical_pair_gpu_complete', checkpoint_sha256=sha(manifest)); time.sleep(30)
    for rel, expected in before_resume.items(): assert sha(BASE / rel) == expected, rel
    x = json.loads(trigger.read_text()); x.update(active=False, resume_utc=utc()); save(trigger, x)
    with (ROOT / 'docs/PREREG_LOG.txt').open('a') as f:
        f.write(f'{utc()} WJB_RESUME_AFTER_PAIR checkpointSHA={sha(manifest)} existing_files_verified={len(before_resume)}; resume missing rows only, no overwrite.\n')
    pulse('resuming_wjb_tails', existing_files_verified=len(before_resume))
    subprocess.run(['bash', str(ROOT / 'tools/handoff_20261106/wjb_tail_resume_queue.sh')], cwd=ROOT, check=True)
    pulse('wjb_tails_complete')


if __name__ == '__main__': main()
