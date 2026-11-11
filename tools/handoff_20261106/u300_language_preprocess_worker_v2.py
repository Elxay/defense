"""Frozen B1 local response translation. No outcome judge or main effect reads."""
from pathlib import Path
import datetime,hashlib,json,os,sys,time
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106'
sys.path.insert(0,str(T));from language300_local_translation import preprocess_reply
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def L(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
P=L(U/'language_preprocess_execution_v2.json');assert H(__file__)==P['worker_sha256']
assert H(T/'language300_local_translation.py')==P['helper_sha256']
plan=L(U/'language_preprocessing_plan.json');assert H(U/'language_preprocessing_plan.json')==P['parent_plan_sha256']
I=U/'language_preprocess_inputs.private.json';assert H(I)==P['inputs_sha256'];data=L(I)
lease=Path(os.environ['DEF_LEASE_DIR']);D=U/'language_processed_alpha0_v1';start=time.monotonic()
assets=L(U/'translator_Qwen3_asset_manifest.json')
assert H(U/'translator_Qwen3_asset_manifest.json')==plan['translator_asset_manifest_sha256']
for n,h in assets['files_sha256'].items():assert H(Path(plan['runtime_model_path'])/n)==h
tok=AutoTokenizer.from_pretrained(plan['runtime_model_path'],local_files_only=True)
model=AutoModelForCausalLM.from_pretrained(plan['runtime_model_path'],local_files_only=True,
    torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval()
group=sys.argv[1];assert group in ['CF','India']
cells=[c for c in P['cells'] if (c['family'] in ['translate-zh-cn','translate-fr'])==(group=='CF')]
for cell in cells:
 key=cell['key'];folder=D/key;rows=data[key];pack=[]
 for i,r in enumerate(rows):
  p=folder/'processed.private'/f"{r['id']:04d}.json"
  if not p.exists():
   if (lease/'yield.request').exists():
    save(lease/'yielded.json',dict(utc=utc(),cell=key,before_row=i));sys.exit(75)
   z=preprocess_reply(r['response'],model,tok,plan)
   save(p,dict(id=r['id'],model=r['model'],family=r['family'],generation_sha256=r['generation_sha256'],
               preprocessing_plan_sha256=H(U/'language_preprocessing_plan.json'),**z))
  else:z=L(p);assert z['generation_sha256']==r['generation_sha256']
  pack.append({**r,'response':z['processed_response'] or '',
      'raw_response_sha256':r['response_sha256'],
      'response_sha256':z.get('processed_response_sha256'),
      'preprocessing_sha256':H(p),'primary_preprocessing_INVALID':z['primary_INVALID']})
  save(lease/'live.json',dict(utc=utc(),phase='frozen_local_reply_translation',cell=key,
       completed_rows=i+1,N=len(rows),elapsed_seconds=time.monotonic()-start,no_judge_labels_read=True))
 wave='language_alpha0_'+key;W=U/'score_waves'/wave
 save(W/'inputs.private.json',pack)
 save(W/'manifest.json',dict(utc=utc(),N=len(pack),judges=['SORRY'],inputs_sha256=H(W/'inputs.private.json'),
          preprocessing_plan_sha256=H(U/'language_preprocessing_plan.json'),scope='descriptive alpha0 language gate only'))
 save(folder/'complete.json',dict(utc=utc(),N=len(rows),wave=wave,manifest_sha256=H(W/'manifest.json'),
       no_judge_labels_or_condition_language_proportions_aggregated=True))
save(D/('complete_'+group+'.json'),dict(utc=utc(),N_cells=len(cells),N_rows=sum(len(v) for v in data.values())))
