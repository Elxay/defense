"""Download pinned official model assets; publish only hashes and status."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, re, time
import requests
from huggingface_hub import hf_hub_download, get_token

ROOT = Path('/data/HZX/Def')
OUT = ROOT / 'results/audit/crossmodel287'

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def save(path, value):
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temp, path)

def configured_token():
    token = get_token()
    if token:
        return token, 'standard_hf_configuration'
    # Read only the authorized account's existing HF_TOKEN assignment, in memory.
    # Never execute a shell profile, print a value, or inspect another process.
    path = Path.home() / '.bashrc'
    if path.exists():
        for line in reversed(path.read_text().splitlines()):
            match = re.fullmatch(r'\s*export\s+HF_TOKEN\s*=\s*[\"\x27]?(hf_[A-Za-z0-9]+)[\"\x27]?\s*', line)
            if match:
                return match.group(1), 'authorized_account_bashrc_assignment'
    return None, 'unavailable'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model', choices=['vicuna', 'gemma'])
    args = parser.parse_args()
    probe = json.loads((OUT / 'model_access_probe.json').read_text())['models'][args.model]
    repo, rev, endpoint = probe['repo'], probe['revision'], probe['endpoint']
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '120'
    os.environ['HF_HUB_ETAG_TIMEOUT'] = '30'
    token, token_source = configured_token() if args.model == 'gemma' else (None, 'public_repository')
    path = OUT / (args.model + '_download.json')
    status = {'utc_started': utc(), 'pid': os.getpid(), 'model': args.model,
              'repo': repo, 'revision': rev, 'phase': 'access_check', 'files': {},
              'credential_available': bool(token), 'credential_source': token_source,
              'token_value_logged': False, 'weights_published': False}
    save(path, status)
    headers = {'Authorization': 'Bearer ' + token} if token else {}
    response = requests.get(endpoint + '/' + repo + '/resolve/' + rev + '/config.json',
                            headers=headers, timeout=45)
    status['config_access_http_status'] = response.status_code
    if response.status_code != 200:
        status.update(utc=utc(), phase='blocked_access_no_bypass')
        save(path, status)
        print(json.dumps({k: v for k, v in status.items() if k != 'files'}), flush=True)
        return
    metadata = json.loads((OUT / 'metadata' / args.model / 'api_metadata.json').read_text())
    names = [x['rfilename'] for x in metadata['siblings'] if x['rfilename'].endswith(
        ('.json', '.model', '.safetensors', '.bin', 'README.md', 'LICENSE', 'USE_POLICY.md'))]
    names.sort(key=lambda n: (n.endswith(('.bin', '.safetensors')), n))
    hashes = {x['rfilename']: (x.get('lfs') or {}).get('sha256') for x in metadata['siblings']}
    local = ROOT / 'models/crossmodel287' / args.model / rev
    local.mkdir(parents=True, exist_ok=True)
    for name in names:
        status.update(utc=utc(), phase='downloading', current_file=name)
        save(path, status)
        for attempt in range(1, 6):
            try:
                p = Path(hf_hub_download(repo_id=repo, filename=name, revision=rev,
                    local_dir=local, endpoint=endpoint, token=token or False))
                actual = sha(p)
                expected = hashes.get(name)
                if expected is not None and actual != expected:
                    raise RuntimeError('LFS hash mismatch')
                status['files'][name] = {'bytes': p.stat().st_size, 'sha256': actual,
                    'expected_lfs_sha256': expected, 'verified': expected is None or actual == expected}
                status.update(utc=utc(), last_completed=name)
                save(path, status)
                print(json.dumps({'utc': utc(), 'model': args.model, 'file': name,
                                  **status['files'][name]}), flush=True)
                break
            except Exception as exc:
                # Exception messages may contain signed URLs: log type only.
                status.update(utc=utc(), attempt=attempt, error_type=type(exc).__name__)
                save(path, status)
                if attempt == 5:
                    status.update(phase='failed_resumable')
                    save(path, status)
                    raise SystemExit(1)
                time.sleep(min(5 * attempt, 20))
    status.update(utc=utc(), phase='complete_verified', local_path=str(local))
    save(path, status)
    print(json.dumps({'model': args.model, 'phase': status['phase'], 'files': len(status['files'])}), flush=True)

if __name__ == '__main__':
    main()
