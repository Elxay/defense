import csv,json,subprocess,shutil
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
source=U/'figtxt_safebench_download.private.csv';assert source.stat().st_size==78942
with source.open(newline='') as f:
 reader=csv.DictReader(f);rows=list(reader);headers=reader.fieldnames
category_keys=[k for k in headers if 'categor' in k.lower()]
counts={k:{} for k in category_keys}
for row in rows:
 for k in category_keys:
  value=row[k];counts[k][value]=counts[k].get(value,0)+1
target=R/'repos/HiddenDetect/data/FigStep/safebench.csv';assert not target.exists();shutil.copy2(source,target)
note=U/'HiddenDetect_FigTxt_upstream_asset.json'
save(note,dict(utc=utc(),source='https://raw.githubusercontent.com/ThuCCSLab/FigStep/main/data/question/safebench.csv',
 bytes=source.stat().st_size,sha256=H(source),headers=headers,N_rows=len(rows),category_counts=counts,
 loader_sha256=H(R/'repos/HiddenDetect/code/load_datasets.py'),author_README_claim='350 unsafe, 7 scenarios',
 loader_filters_scenarios=False,native_subset_provenance_verified=len(rows)==350,
 rule='Do not silently choose seven scenarios if upstream has500; keep source data and resolve exact author subset before native threshold claim.'))
m=next(x for x in L(U/'HiddenDetect_ModelScope_asset_probe.json')['rows'] if x['repo'].startswith('AI-ModelScope/'))
hf=next(x for x in L(U/'detector_native_asset_availability.json')['models'] if x['repo'].startswith('liuhaotian/'))
orig={v['name']:v.get('lfs_sha256') for v in hf['files']};w=[v for v in m['files'] if v['name'].endswith('.safetensors')]
checks=[dict(name=v['name'],equal=v['sha256']==orig[v['name']]) for v in w];assert len(checks)==3 and all(c['equal'] for c in checks)
bind=U/'HiddenDetect_ModelScope_weight_identity.json';save(bind,dict(utc=utc(),original_HF_revision=hf['revision'],checks=checks,public_full_precision=True,no_quantized_substitute=True))
commit=publish([note,bind,U/'HiddenDetect_ModelScope_asset_probe.json',T/'u300_modelscope_native_download.py',__import__('pathlib').Path(__file__)],
 'Verify full-precision ModelScope weight identity and preserve unresolved native FigTxt subset provenance')
log=open(R/'logs/u300_modelscope_native_download.log','a')
p=subprocess.Popen(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(T/'u300_modelscope_native_download.py')],stdout=log,stderr=log,start_new_session=True)
print(json.dumps(dict(commit=commit,FigTxt_rows=len(rows),category_counts=counts,weight_hash_checks=checks,download_pid=p.pid)))
