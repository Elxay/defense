"""Public pinned Vicuna download using resumable HTTP ranges, with LFS SHA checks."""
from pathlib import Path
import datetime, hashlib, json, os, time
import requests
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 q=p.with_name(p.name+'.http.tmp');q.write_text(json.dumps(x,indent=2)+'\n');os.replace(q,p)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 probe=json.loads((O/'model_access_probe.json').read_text())['models']['vicuna'];rev=probe['revision'];repo=probe['repo']
 directory=R/'models/crossmodel287/vicuna'/rev;status_path=O/'vicuna_download_http.json'
 state={'utc_started':utc(),'pid':os.getpid(),'revision':rev,'repo':repo,'transport':'public_https_range','credential_used':False,'files':{},'phase':'downloading'}
 for row in probe['files']:
  name=row['name']
  if not name.endswith('.bin'):continue
  target=directory/name;partial=target.with_name(name+'.http.partial');expected=row['lfs_sha256'];size=row['bytes']
  for attempt in range(1,31):
   try:
    if target.exists():assert target.stat().st_size==size and sha(target)==expected;break
    offset=partial.stat().st_size if partial.exists() else 0
    if offset<size:
     url=probe['endpoint']+'/'+repo+'/resolve/'+rev+'/'+name+'?download=true'
     z=requests.get(url,headers={'Range':f'bytes={offset}-'},stream=True,timeout=(25,120))
     if z.status_code==206:assert z.headers.get('Content-Range','').startswith('bytes '+str(offset)+'-')
     elif z.status_code==200:assert offset==0,'Do not append full-file response to a partial range'
     else:z.close();raise RuntimeError('public_range_http_'+str(z.status_code))
     updated=0.0
     with partial.open('ab')as f:
      for block in z.iter_content(1024*1024):
       if not block:continue
       f.write(block);offset+=len(block)
       if time.monotonic()-updated>5:
        f.flush();state.update(utc=utc(),phase='downloading',current_file=name,downloaded_bytes=offset,total_bytes=size,attempt=attempt);save(status_path,state);updated=time.monotonic()
     z.close()
    assert partial.stat().st_size==size
    actual=sha(partial);assert actual==expected,'LFS hash mismatch; preserve failed artifact'
    partial.replace(target);break
   except Exception as e:
    state.update(utc=utc(),phase='retrying_resumable',current_file=name,error_type=type(e).__name__,attempt=attempt);save(status_path,state)
    if isinstance(e,AssertionError):raise
    time.sleep(min(5*attempt,45))
  else:state.update(utc=utc(),phase='failed_resumable');save(status_path,state);return
  state['files'][name]={'sha256':expected,'bytes':size,'verified':True};state.update(utc=utc());save(status_path,state)
 state.update(utc=utc(),phase='complete_verified');save(status_path,state)
 print(json.dumps({'phase':state['phase'],'verified_weight_files':len(state['files'])}),flush=True)
if __name__=='__main__':main()
