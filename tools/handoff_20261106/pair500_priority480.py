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
PRIMARY = {'old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7'}
AUXILIARY = {'old_s0','SYS_A','SYS_B'}
TAIL = PRIMARY | AUXILIARY


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


def remaining_conditions():
    allowed = {str(row['id']) for row in json.loads((BASE / 'wjb_mapping255.json').read_text())['rows']}
    assert len(allowed) == 2000
    counts = {}
    for name in sorted(TAIL):
        gen = BASE / 'public255/harmful.private' / name / 'wildjailbreak_harmful'
        score = BASE / 'public255/mapped_scores' / name
        g = {p.stem for p in gen.glob('*.json')}
        s = {p.stem for p in score.glob('*.json')}
        assert g <= allowed and s <= allowed
        counts[name] = {'generation': len(g), 'harmbench_top1': len(s)}
    return [name for name, x in counts.items() if min(x.values()) < 2000], counts


def exempt_last_condition(trigger, state):
    remaining = state['remaining_conditions']
    assert len(remaining) == 1 and set(remaining) <= PRIMARY
    manifest = BASE / 'pair_priority_one_remaining_checkpoint.json'
    if not manifest.exists():
        save(manifest, {'utc': utc(), 'files': checkpoint(), 'remaining_conditions': remaining})
    before = json.loads(manifest.read_text())['files']
    pulse('allow_last_condition_to_finish', remaining_conditions=remaining)
    if remaining:
        # This waits on the same leases: the old queue may finish its current
        # operation first. Cached rows are checked and only missing work runs.
        subprocess.run(['bash', str(ROOT / 'tools/handoff_20261106/wjb_tail_resume_queue.sh'), remaining[0]], cwd=ROOT, check=True)
    for rel, expected in before.items(): assert sha(BASE / rel) == expected, rel
    pending, counts = remaining_conditions()
    assert not (set(pending) & PRIMARY), counts
    state.update(exemption_completed_utc=utc(), completion_counts=counts)
    save(trigger, state)
    with (ROOT / 'docs/PREREG_LOG.txt').open('a') as f:
        f.write(f'{utc()} PAIR480_LAST_CONDITION_EXEMPTION_COMPLETED checkpointSHA={sha(manifest)} retained_files_verified={len(before)}; no pause, both generation and HB judge complete.\n')
    pulse('primary_exemption_complete_auxiliary_stays_paused')


def stop_owned_tails(selected=TAIL):
    stopped = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit(): continue
        try:
            args = [a.decode() for a in proc.joinpath('cmdline').read_bytes().split(b'\0') if a]
            if not any(a.endswith('/wjb_eval255_run.py') for a in args): continue
            if not (selected & set(args)) or not ({'harmful', 'score'} & set(args)): continue
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
            remaining, counts = remaining_conditions()
            primary_remaining = sorted(set(remaining) & PRIMARY)
            exempt = len(primary_remaining) == 1
            state = {'utc': utc(), 'active': not exempt,
                     'reason': 'actual_rows_ge480' if observed['n']>=480 else 'frozen_cutoff_prefix',
                     'last_condition_exemption': exempt, 'remaining_conditions': primary_remaining,
                     'all_remaining_conditions': remaining, 'auxiliary_pause': True,
                     'condition_counts': counts, **observed}
            save(trigger, state)
            with (ROOT / 'docs/PREREG_LOG.txt').open('a') as f:
                f.write(f'{utc()} PAIR480_TRIGGER remaining_conditions={remaining} last_condition_exemption={exempt} triggerSHA={sha(trigger)}; remaining means incomplete generation OR HB top1 scoring, metadata only.\n')
            break
        pulse('waiting_actual_480_rows', **observed); time.sleep(30)
    state = json.loads(trigger.read_text())
    stopped = []
    for _ in range(4):
        selected=AUXILIARY if state.get('last_condition_exemption') else TAIL
        stopped += stop_owned_tails(selected); time.sleep(2)
    manifest = BASE / 'pair_priority_checkpoint.json'
    if manifest.exists():
        before_resume = json.loads(manifest.read_text())['files']
    else:
        before_resume = checkpoint()
        save(manifest, {'utc': utc(), 'stopped_pids': sorted(set(stopped)), 'files': before_resume})
        with (ROOT / 'docs/PREREG_LOG.txt').open('a') as f:
            f.write(f'{utc()} WJB_PAUSE_PAIR480 triggerSHA={sha(trigger)} checkpointSHA={sha(manifest)} pids={sorted(set(stopped))}; atomic rows retained, at most one in-flight row lost per worker.\n')
    if state.get('last_condition_exemption') and not state.get('exemption_completed_utc'):
        exempt_last_condition(trigger,state)
    while True:
        p = BASE / 'full_queue_live.json'
        state = json.loads(p.read_text()) if p.exists() else {}
        if state.get('phase') == 'complete': break
        pulse('waiting_canonical_pair_gpu_complete', checkpoint_sha256=sha(manifest)); time.sleep(30)
    for rel, expected in before_resume.items(): assert sha(BASE / rel) == expected, rel
    x = json.loads(trigger.read_text()); x.update(active=False, auxiliary_pause=False, resume_utc=utc()); save(trigger, x)
    with (ROOT / 'docs/PREREG_LOG.txt').open('a') as f:
        f.write(f'{utc()} WJB_RESUME_AFTER_PAIR checkpointSHA={sha(manifest)} existing_files_verified={len(before_resume)}; resume missing rows only, no overwrite.\n')
    pulse('resuming_wjb_tails', existing_files_verified=len(before_resume))
    subprocess.run(['bash', str(ROOT / 'tools/handoff_20261106/wjb_tail_resume_queue.sh')], cwd=ROOT, check=True)
    pulse('wjb_tails_complete')


if __name__ == '__main__': main()
