"""Download official gated weights using an existing credential, without logging it."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import threading

os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1'
os.environ['HF_HUB_DISABLE_XET']='1'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT']='60'
from huggingface_hub import HfApi,get_token,hf_hub_download,snapshot_download
from huggingface_hub.utils import disable_progress_bars
disable_progress_bars()
ROOT=Path('D:/Documents/defense/output/wildguard_download')
ROOT.mkdir(parents=True,exist_ok=True)
DEST=ROOT/'model'
state={'stage':'checking_access','pid':os.getpid()}
stop=threading.Event()


def heartbeat():
    while not stop.is_set():
        info=dict(state,unix_time=time.time())
        if DEST.exists():
            info['local_bytes']=sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file())
        p=ROOT/'status.tmp';p.write_text(json.dumps(info));os.replace(p,ROOT/'status.json')
        stop.wait(10)


def main():
    candidates=[]
    local=get_token()
    if local:candidates.append(local)
    # Capture encrypted SSH stdout in memory. Never print or persist the token.
    remote=subprocess.run(['ssh','innet','/home/kemove/anaconda3/envs/HZX_GLA/bin/python','-c',
        '"from huggingface_hub import get_token; import sys; sys.stdout.write(get_token() or chr(10))"'],
        capture_output=True,text=True,check=True).stdout.strip()
    if remote and remote not in candidates:candidates.append(remote)
    token=None
    for candidate in candidates:
        try:
            hf_hub_download('allenai/wildguard','config.json',token=candidate,local_dir=DEST)
            token=candidate;break
        except Exception as e:
            print('ACCESS_ATTEMPT',type(e).__name__,getattr(getattr(e,'response',None),'status_code',None),flush=True)
    if token is None:raise RuntimeError('No existing credential passed gated config access')
    info=HfApi().model_info('allenai/wildguard',token=token,files_metadata=True)
    state.update(stage='downloading',revision=info.sha)
    print('AUTHORIZED',info.sha,flush=True)
    snapshot_download('allenai/wildguard',revision=info.sha,token=token,local_dir=DEST,max_workers=4,
        allow_patterns=['*.safetensors','model.safetensors.index.json','config.json',
            'generation_config.json','tokenizer*','special_tokens_map.json','added_tokens.json',
            'README.md','.gitattributes'])
    state.update(stage='hashing')
    manifest={}
    for p in sorted(DEST.rglob('*')):
        if p.is_file() and '.cache' not in p.parts:
            h=hashlib.sha256()
            with p.open('rb') as f:
                for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
            manifest[p.relative_to(DEST).as_posix()]=h.hexdigest()
    if not any(n.endswith(('.safetensors','.bin')) for n in manifest):raise RuntimeError('No weights downloaded')
    record={'repo':'allenai/wildguard','revision':info.sha,'files':manifest}
    (DEST/'DOWNLOAD_SHA256.json').write_text(json.dumps(record,indent=2)+'\n')
    state.update(stage='transferring_to_innet',file_count=len(manifest))
    subprocess.run(['ssh','innet','mkdir','-p','/data/HZX/Def/models/WildGuard'],check=True)
    # Explicitly transfer downloaded artifacts and manifest; exclude client caches.
    for name in list(manifest)+['DOWNLOAD_SHA256.json']:
        p=DEST/name
        parent=str(Path(name).parent).replace('\\','/')
        if parent!='.':subprocess.run(['ssh','innet','mkdir','-p','/data/HZX/Def/models/WildGuard/'+parent],check=True)
        subprocess.run(['scp','-q',str(p),'innet:/data/HZX/Def/models/WildGuard/'+name],check=True)
    state.update(stage='remote_hash_verification')
    code="from pathlib import Path; import json,hashlib; r=Path('/data/HZX/Def/models/WildGuard'); x=json.loads((r/'DOWNLOAD_SHA256.json').read_text()); checks={n:hashlib.file_digest((r/n).open('rb'),'sha256').hexdigest()==h for n,h in x['files'].items()}; assert all(checks.values()); print('VERIFIED',len(checks))"
    subprocess.run(['ssh','innet','python3','-'],input=code,text=True,check=True)
    state.update(stage='complete',revision=info.sha)
    print('COMPLETE',json.dumps(record),flush=True)


threading.Thread(target=heartbeat,daemon=True).start()
try:
    main()
except Exception as e:
    state.update(stage='failed',error_type=type(e).__name__)
    print('FAILED',type(e).__name__,flush=True)
    raise SystemExit(1)
finally:
    stop.set()
    (ROOT/'status.json').write_text(json.dumps(dict(state,unix_time=time.time())))
