"""Pinned, resumable SORRY judge download. No credentials or signed URLs logged."""
from pathlib import Path
import concurrent.futures
import datetime
import hashlib
import json
import os
import sys
import threading
import time
import requests

R = Path('/data/HZX/Def')
O = R / 'results/audit/sorry296'
sys.path.insert(0, str(R / 'tools/handoff_20261106'))
from crossmodel287_download import configured_token, sha
from huggingface_hub import hf_hub_download

REPO = 'sorry-bench/ft-mistral-7b-instruct-v0.2-sorry-bench-202406'
REV = '79ab44668cef557414cb5e15c726a56ebca9cf1e'
DEST = R / 'models/sorry296' / REV

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '120'
    token, source = configured_token()
    assert token, 'No available authorized credential'
    response = requests.get('https://hf-mirror.com/api/models/' + REPO + '/revision/' + REV,
                            params={'blobs': 'true'}, headers={'Authorization': 'Bearer ' + token}, timeout=(10, 30))
    assert response.status_code == 200, 'Pinned model metadata access failed'
    meta = response.json(); assert meta['sha'] == REV
    metadata = O / 'judge_pinned_metadata.private.json'
    metadata.write_text(json.dumps(meta, indent=2) + '\n')
    names = [v['rfilename'] for v in meta['siblings'] if v['rfilename'].endswith(('.json', '.model', '.safetensors', 'README.md', 'LICENSE'))]
    expected = {v['rfilename']: (v.get('lfs') or {}).get('sha256') for v in meta['siblings']}
    assert sum(n.endswith('.safetensors') for n in names) == 6
    assert all(expected[n] for n in names if n.endswith('.safetensors')), 'Missing upstream shard hashes'
    state = {'utc_started': utc(), 'pid': os.getpid(), 'repo': REPO, 'revision': REV,
             'phase': 'downloading', 'credential_source': source, 'credential_value_logged': False,
             'local_path': str(DEST), 'files': {}}
    lock = threading.Lock()
    def write():
        state['utc'] = utc()
        p = O / 'judge_download_live.json'; q = p.with_suffix('.tmp')
        q.write_text(json.dumps(state, indent=2) + '\n'); q.replace(p)
    with lock: write()
    def download(name):
        for attempt in range(1, 5):
            try:
                p = Path(hf_hub_download(REPO, name, revision=REV, endpoint='https://hf-mirror.com',
                                        local_dir=DEST, token=token))
                digest = sha(p)
                assert expected[name] is None or digest == expected[name], 'Upstream LFS digest mismatch'
                with lock:
                    state['files'][name] = {'bytes': p.stat().st_size, 'sha256': digest,
                                            'expected_lfs_sha256': expected[name], 'verified': True}
                    write()
                return
            except Exception as exc:
                with lock:
                    state['last_error'] = {'file': name, 'attempt': attempt, 'type': type(exc).__name__}
                    write()
                if attempt == 4: raise RuntimeError('Download failed: ' + name + ' ' + type(exc).__name__) from None
                time.sleep(3)
    # Fetch small tokenizer/config files first, then parallelize the six large shards.
    try:
        for n in names:
            if not n.endswith('.safetensors'): download(n)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(download, [n for n in names if n.endswith('.safetensors')]))
    except Exception:
        with lock: state['phase'] = 'failed_resumable'; write()
        raise
    with lock:
        state['phase'] = 'complete_verified'; write()
        (O / 'judge_download_complete.json').write_text(json.dumps(state, indent=2) + '\n')
    print(json.dumps({'utc': utc(), 'phase': 'complete_verified', 'files': len(names)}))

if __name__ == '__main__': main()
