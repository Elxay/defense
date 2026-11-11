"""Download public native-reproduction assets, no tokens or test text in logs."""
from pathlib import Path
import datetime,hashlib,json,urllib.request,time
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def H(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(16*1024*1024),b''):h.update(b)
 return h.hexdigest()
audit=json.loads((U/'detector_native_asset_availability.json').read_text())
info=next(x for x in audit['models'] if x['repo'].startswith('liuhaotian/'))
assert info['status']==200 and info['gated'] is False
revision=info['revision'];target=R/'models'/('HiddenDetect_llava-v1.6-vicuna-7b_'+revision[:8])
target.mkdir(parents=True,exist_ok=True)
files=info['files'];names={v['name'] for v in files}
# Choose one complete original weight format, never both redundant formats.
fmt='.safetensors' if any(n.endswith('.safetensors') for n in names) else '.bin'
selected=[v for v in files if '/' not in v['name'] and
          (v['name'].endswith(fmt) or v['name'].endswith(('.json','.model','.md')))]
save(U/'detector_native_download_plan.json',dict(utc=utc(),repo=info['repo'],revision=revision,files=selected,
     path=str(target),requires_additional_vision_tower_check=True,not_a_reproduction_pass=True))
completed={}
for v in selected:
 n=v['name'];p=target/n
 if p.exists() and (not v.get('lfs_sha256') or H(p)==v['lfs_sha256']):
  completed[n]=dict(bytes=p.stat().st_size,sha256=H(p));continue
 q=p.with_suffix(p.suffix+'.part')
 try:
  req=urllib.request.Request('https://hf-mirror.com/'+info['repo']+'/resolve/'+revision+'/'+n)
  with urllib.request.urlopen(req,timeout=45) as src,q.open('wb') as dst:
   while True:
    b=src.read(8*1024*1024)
    if not b:break
    dst.write(b)
    save(U/'detector_native_download_live.json',dict(utc=utc(),file=n,bytes_current=dst.tell(),completed_files=len(completed),phase='downloading_public_native_assets'))
  sh=H(q)
  if v.get('lfs_sha256'):assert sh==v['lfs_sha256']
  q.replace(p);completed[n]=dict(bytes=p.stat().st_size,sha256=sh)
 except Exception as e:
  save(U/'detector_native_download_blocked.json',dict(utc=utc(),file=n,error_type=type(e).__name__,
       status=getattr(e,'code',None),completed_files=len(completed),no_access_bypass=True));raise
save(target/'DOWNLOAD_SHA256.json',dict(utc=utc(),repo=info['repo'],revision=revision,files=completed))
save(U/'detector_native_download_complete.json',dict(utc=utc(),path=str(target),manifest_sha256=H(target/'DOWNLOAD_SHA256.json'),
    requires_vision_tower_runtime_gate=True,not_a_reproduction_pass=True))
