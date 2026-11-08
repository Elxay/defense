"""Verify pinned local judge bytes and preserve per-launch provenance."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import socket

ROOT = Path('/data/HZX/Def')
BASE = ROOT / 'results/audit/pair500'
MANIFEST = BASE / 'hb_judge_model_sha256.json'
MANIFEST_SHA256 = '35df6528783271ff63b0dd44537f50c4d09c022b9fdb786cd1de0c574e43af99'


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(16*1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def save(p, x):
    t = p.with_suffix('.tmp'); t.write_text(json.dumps(x, indent=2)+'\n'); t.replace(p)


def prepare(conditions, model_root):
    stamp = utc(); key = stamp.replace(':', '').replace('+', '_') + '_' + str(os.getpid())
    launch = BASE / 'public255/judge_launches' / key
    launch.mkdir(parents=True, exist_ok=False)
    record = {'utc': stamp, 'pid': os.getpid(), 'host': socket.gethostname(),
        'backend': 'hf_innet', 'conditions': conditions, 'model_root': str(model_root),
        'physical_device': os.environ.get('DEVICE'), 'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES'),
        'manifest_sha256': MANIFEST_SHA256, 'preflight_source_sha256': sha(Path(__file__)),
        'stage': 'verifying_model_hashes', 'model_hash_verified': False, 'reference20_passed': False}
    save(launch / 'started.json', record)
    save(BASE / 'public255/judge_window_live.json', {**record, 'launch_directory': str(launch.relative_to(ROOT))})
    try:
        assert sha(MANIFEST) == MANIFEST_SHA256, 'Judge manifest changed'
        expected = json.loads(MANIFEST.read_text())
        model = Path(model_root)
        assert model.resolve() == Path(expected['model_root']).resolve()
        for name, spec in expected['files'].items():
            path = model / name
            assert path.stat().st_size == spec['bytes'] and sha(path) == spec['sha256'], f'Judge artifact mismatch: {name}'
            save(launch / 'hash_progress.json', {'utc': utc(), 'last_verified_file': name})
    except Exception as e:
        save(launch / 'failed.json', {'utc': utc(), 'stage': 'model_hashes', 'error_type': type(e).__name__})
        raise
    record.update(utc=utc(), stage='model_hashes_verified', model_hash_verified=True,
                  verified_files=len(expected['files']), verified_bytes=sum(x['bytes'] for x in expected['files'].values()))
    save(launch / 'model_preflight.json', record)
    return launch, record


def reference_failed(launch, error):
    save(launch / 'failed.json', {'utc': utc(), 'stage': 'reference20', 'error_type': type(error).__name__})


def reference_passed(launch, record):
    record.update(utc=utc(), stage='reference20_passed', reference20_passed=True,
                  reference20_sha256=sha(launch / 'judge20_gate.json'))
    save(launch / 'ready.json', record)
    save(BASE / 'public255/judge_window_live.json', {**record, 'launch_directory': str(launch.relative_to(ROOT))})
