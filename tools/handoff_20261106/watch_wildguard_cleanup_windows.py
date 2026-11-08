"""Remove only the same pre-existing server token, after verified acquisition."""
import json
from pathlib import Path
import subprocess
import time

ROOT=Path('D:/Documents/defense/output/wildguard_download')
probe="from pathlib import Path; import hashlib; p=Path.home()/'.cache/huggingface/token'; print(hashlib.sha256(p.read_bytes().strip()).hexdigest() if p.exists() else 'ABSENT')"
fingerprint=subprocess.run(['ssh','innet','python3','-'],input=probe,text=True,capture_output=True,check=True).stdout.strip()
while True:
    state=json.loads((ROOT/'status.json').read_text())
    if state['stage']=='failed':raise SystemExit('Download failed: no credential deleted')
    if state['stage']=='complete':break
    time.sleep(15)
code='''from pathlib import Path
import hashlib,json,os,re,datetime
p=Path.home()/'.cache/huggingface/token';expected=EXPECTED
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_token_created':False,'revocation':'not performed: credential pre-existed this task'}
if not p.exists():result['token_file']='already_absent'
elif hashlib.sha256(p.read_bytes().strip()).hexdigest()!=expected:raise RuntimeError('Credential changed: do not delete another token')
else:
 token=p.read_bytes().strip()
 for name in ['.bash_history','.zsh_history']:
  h=Path.home()/name
  if h.exists():
   lines=h.read_bytes().splitlines(keepends=True);kept=[x for x in lines if token not in x];result[name+'_exact_lines_removed']=len(lines)-len(kept)
   if len(kept)!=len(lines):
    mode=h.stat().st_mode & 0o777;t=h.with_name(h.name+'.wildguard-cleanup');t.write_bytes(b''.join(kept));os.chmod(t,mode);os.replace(t,h)
 p.unlink();result['token_file']='removed_matching_original'
result['token_file_exists_after']=p.exists()
dest=Path('/data/HZX/Def/results/audit/pair500/wildguard/credential_cleanup.json');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,indent=2));print(json.dumps(result))
'''.replace('EXPECTED',repr(fingerprint))
r=subprocess.run(['ssh','innet','python3','-'],input=code,text=True,capture_output=True,check=True)
(ROOT/'credential_cleanup.json').write_text(r.stdout)
print(r.stdout)
