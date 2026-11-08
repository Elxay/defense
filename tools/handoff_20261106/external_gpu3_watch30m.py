"""Record an external PID every 30 minutes; never inspect its environment."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/data/HZX/Def')
BASE = ROOT / 'results/audit/pair500'
PID = 592686


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def observe(expected_start):
    proc = Path('/proc', str(PID))
    x = {'utc': now().isoformat(), 'pid': PID, 'environment_read': False, 'action': 'observe_only'}
    try:
        raw = (proc / 'stat').read_text()
        start = raw[raw.rfind(')') + 2:].split()[19]
        x['same_process_alive'] = start == expected_start
        x['pid_reused'] = start != expected_start
        if x['same_process_alive']:
            x['elapsed_s'] = int(subprocess.check_output(['ps', '-o', 'etimes=', '-p', str(PID)],
                env={'PATH': os.environ['PATH'], 'TZ': 'UTC', 'LC_ALL': 'C'}, text=True).strip())
            x['ps_utc'] = subprocess.check_output(['ps', '-o', 'user=,lstart=,comm=', '-p', str(PID)],
                env={'PATH': os.environ['PATH'], 'TZ': 'UTC', 'LC_ALL': 'C'}, text=True).strip()
            args = [a.decode(errors='replace') for a in (proc / 'cmdline').read_bytes().split(b'\0') if a]
            x['script_names'] = [Path(a).name for a in args if a.endswith(('.py', '.sh'))]
    except (FileNotFoundError, ProcessLookupError, subprocess.CalledProcessError):
        x['same_process_alive'] = False
        x['pid_reused'] = False
    except PermissionError:
        x['same_process_alive'] = None
        x['inspection'] = 'permission_denied'
    try:
        x['gpu3_total_memory_mib'] = int(subprocess.check_output(['nvidia-smi',
            '--query-gpu=memory.used', '--format=csv,noheader,nounits', '-i', '3'], text=True, timeout=15).strip())
    except (subprocess.SubprocessError, ValueError):
        x['gpu3_total_memory_mib'] = None
    return x


def main():
    try:
        raw = Path('/proc', str(PID), 'stat').read_text()
        start = raw[raw.rfind(')') + 2:].split()[19]
    except FileNotFoundError:
        start = 'absent_at_watcher_start'
    identity = BASE / 'gpu3_external_identity.json'
    if identity.exists():
        expected = json.loads(identity.read_text())['start_ticks']
    else:
        expected = start
        identity.write_text(json.dumps({'utc': now().isoformat(), 'pid': PID, 'start_ticks': start,
            'ownership': 'Shared Unix UID; actual person not independently identified; treat as external project.'}, indent=2)+'\n')
    history = BASE / 'gpu3_external_30m.jsonl'
    last = None
    if history.exists():
        lines = history.read_text().splitlines()
        if lines: last = datetime.datetime.fromisoformat(json.loads(lines[-1])['utc'])
    next_record = (last + datetime.timedelta(minutes=30)) if last else now()
    while True:
        stamp = now()
        if stamp >= next_record:
            x = observe(expected)
            with history.open('a') as f: f.write(json.dumps(x)+'\n')
            digest = hashlib.sha256(history.read_bytes()).hexdigest()
            with (ROOT / 'docs/PREREG_LOG.txt').open('a') as f:
                f.write(f'{x["utc"]} GPU3_EXTERNAL_30M pid={PID} same_process_alive={x["same_process_alive"]} memoryMiB={x["gpu3_total_memory_mib"]} historySHA={digest}; no environment read or process modification.\n')
            if x['same_process_alive'] is False: return
            next_record = stamp + datetime.timedelta(minutes=30)
        live = BASE / 'gpu3_external_watch_live.json'
        temp = live.with_suffix('.tmp')
        temp.write_text(json.dumps({'utc': stamp.isoformat(), 'pid': os.getpid(),
            'phase': 'waiting_next_30m_observation', 'next_observation_utc': next_record.isoformat()}, indent=2)+'\n')
        temp.replace(live)
        time.sleep(30)


if __name__ == '__main__': main()
