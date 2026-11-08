"""Pause only registered project WJB tail workers at the frozen deadline."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/data/HZX/Def')
BASE = ROOT / 'results/audit/pair500'
DEADLINE = datetime.datetime(2026, 11, 9, 9, tzinfo=datetime.timezone.utc)
TAIL = {'old_s7', 'old_s0', 'SYS_A', 'SYS_B'}


def save(phase, **extra):
    x = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'pid': os.getpid(), 'phase': phase, **extra}
    p = BASE / 'pair_priority_deadline_live.json'
    p.with_suffix('.tmp').write_text(json.dumps(x, indent=2) + '\n')
    p.with_suffix('.tmp').replace(p)


def enforce():
    state_path = BASE / 'public255/stage_live.json'
    state = json.loads(state_path.read_text())
    if state.get('detail') not in TAIL or state.get('stage') not in {'harmful_generation', 'harmful_judge'}:
        return []
    stopped = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            args = proc.joinpath('cmdline').read_bytes().split(b'\0')
            args = [a.decode() for a in args if a]
            if not any(a.endswith('/wjb_eval255_run.py') for a in args):
                continue
            if state['detail'] not in args or not ({'harmful', 'score'} & set(args)):
                continue
            env = proc.joinpath('environ').read_bytes().split(b'\0')
            if b'DSH_OWNER=/data/HZX/Def' not in env:
                continue
            # safe_kill also requires the launch_job registry and matching UID.
            manifests = {}
            for folder in ['harmful.private', 'mapped_scores']:
                for p in (BASE / 'public255' / folder / state['detail']).rglob('*.json'):
                    manifests[str(p.relative_to(BASE))] = hashlib.sha256(p.read_bytes()).hexdigest()
            record = BASE / ('priority_pause_' + proc.name + '.json')
            record.write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'pid': int(proc.name), 'condition': state['detail'], 'files': manifests}, indent=2) + '\n')
            subprocess.run(['bash', str(ROOT / 'night/safe_kill.sh'), proc.name], check=True)
            stopped.append(int(proc.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return stopped


if __name__ == '__main__':
    while datetime.datetime.now(datetime.timezone.utc) < DEADLINE:
        save('waiting_deadline', deadline_utc=DEADLINE.isoformat())
        time.sleep(30)
    # Repeat for launch races. The stage entry guard prevents subsequent tails.
    for _ in range(4):
        stopped = enforce()
        save('deadline_enforced', stopped=stopped)
        if stopped:
            with (ROOT / 'docs/PREREG_LOG.txt').open('a') as f:
                f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} WJB_TAIL_PAUSED_FOR_PAIR254 pids={stopped}; atomic completed rows retained, at most one in-flight row per worker discarded.\n')
        time.sleep(5)
