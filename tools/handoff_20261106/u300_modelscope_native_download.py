"""Public mirror download admitted only after exact original weight-hash match."""
from pathlib import Path
import concurrent.futures,csv,datetime,hashlib,json,shutil,urllib.request,urllib.parse
from u300_schedule_prepare import R,U,T,H,L,utc,save
audit=L(U/'HiddenDetect_ModelScope_asset_probe.json');m=next(r for r in audit['rows'] if r['repo']=='AI-ModelScope/llava-v1.6-vicuna-7b')
hf=next(r for r in L(U/'detector_native_asset_availability.json')['models'] if r['repo']=='liuhaotian/llava-v1.6-vicuna-7b')
expected={v['name']:v for v in hf['files']};weights=[v for v in m['files'] if v['name'].endswith('.safetensors')]
checks=[dict(name=v['name'],match_original_LFS_sha256=v['sha256']==expected[v['name']]['lfs_sha256']) for v in weights]
assert len(weights)==3 and all(v['match_original_LFS_sha256'] for v in checks)
dest=R/'models/HiddenDetect_llava_v16_vicuna7b_modelscope';dest.mkdir(parents=True,exist_ok=True)
need={v['name'] for v in weights}|{'config.json','generation_config.json','model.safetensors.index.json','tokenizer.model','tokenizer_config.json','special_tokens_map.json','README.md'}
files=[v for v in m['files'] if v['name'] in need]
save(U/'HiddenDetect_ModelScope_download_plan.json',dict(utc=utc(),repo=m['repo'],source_revision='master',
 original_HF_revision=hf['revision'],weight_hash_checks=checks,files=files,path=str(dest),
 pinning='Every file expected SHA256 frozen from mirror metadata before download; all 3 weight hashes identical to original HF LFS',
 native_reproduction_not_yet_passed=True,vision_tower_still_requires_verification=True))
def download(v):
 p=dest/v['name'];q=p.with_suffix(p.suffix+'.part')
 if p.exists():assert H(p)==v['sha256'];return dict(name=p.name,sha256=H(p),bytes=p.stat().st_size)
 url='https://www.modelscope.cn/api/v1/models/'+m['repo']+'/repo?Revision=master&FilePath='+urllib.parse.quote(v['name'])
 try:
  with urllib.request.urlopen(url,timeout=60) as src,q.open('wb') as dst:
   tick=0
   while True:
    b=src.read(8*1024*1024)
    if not b:break
    dst.write(b);tick+=1
    if tick%8==0:save(U/'HiddenDetect_ModelScope_download_progress'/v['name'],dict(utc=utc(),bytes_written=dst.tell(),expected_bytes=v['size']))
  assert q.stat().st_size==v['size'] and H(q)==v['sha256'];q.replace(p)
  return dict(name=p.name,sha256=H(p),bytes=p.stat().st_size)
 except Exception as e:
  save(U/'HiddenDetect_ModelScope_download_progress'/(v['name']+'.error.json'),dict(utc=utc(),error_type=type(e).__name__,http_status=getattr(e,'code',None)))
  raise
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:done=list(ex.map(download,files))
save(dest/'DOWNLOAD_SHA256.json',dict(utc=utc(),repo=m['repo'],original_HF_revision=hf['revision'],files=done,weight_hash_checks=checks))
save(U/'HiddenDetect_ModelScope_download_complete.json',dict(utc=utc(),N_files=len(done),path=str(dest),manifest_sha256=H(dest/'DOWNLOAD_SHA256.json'),native_reproduction_not_yet_passed=True))
