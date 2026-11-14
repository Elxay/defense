"""B1 translation with fixed cross-card reference and complete row failure metadata."""
from pathlib import Path
import os,sys,json,hashlib,datetime,time
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T));from language300_unicode_routing20 import preprocess_reply
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def L(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'language_nonzero36_execution.json');assert H(__file__)==P['worker_sha256'];assert H(T/'language300_unicode_routing20.py')==P['helper_sha256'];assert H(U/'language_preprocessing_route20_plan.json')==P['route_plan_sha256'];plan=L(U/'language_preprocessing_route20_plan.json');key=sys.argv[1];I=U/'language_nonzero36_inputs'/(key+'.private.json');reference_only=key=='reference_only';data=None
if not reference_only:
 binding=L(U/'language_nonzero36_bindings'/(key+'.json'));assert H(I)==binding['inputs_sha256'];data={key:L(I)}
assets=L(U/'language_assets33.json');assert H(U/'language_assets33.json')==P['assets_manifest_sha256'];lease=Path(os.environ['DEF_LEASE_DIR']);site=os.environ['DEF_SITE'];mp=Path(P['model_paths'][site]);gpu=os.environ['CUDA_VISIBLE_DEVICES'];D=U/'language_processed36'
for n,h in assets['files_sha256'].items():assert H(mp/n)==h
tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval()
gate=D/'gates'/site/('gpu'+gpu)/'reference20.json'
if not gate.exists():
 ref=U/'language_reference20_33.private.json';assert H(ref)==P['reference_sha256'];checks=[]
 for r in L(ref):
  z=preprocess_reply(r['response'],model,tok,plan);e=r['expected'];ok=z.get('translated_response')==e.get('translated_response') and z.get('processed_response')==e.get('processed_response') and z['status']==e['status']
  checks.append(dict(id=r['id'],byte_equal=ok));save(lease/'live.json',dict(utc=utc(),phase='B1_reference20',N=len(checks),total=20,no_judge_labels_read=True))
 save(gate,dict(utc=utc(),passed=all(z['byte_equal'] for z in checks),N=20,checks=checks,plan_sha256=H(U/'language_nonzero36_execution.json'),helper_sha256=P['helper_sha256'],site=site,physical_gpu=gpu))
assert L(gate)['passed'],'B1 translation reference20 failed; do not translate formal rows'
if reference_only:sys.exit(0)
key=sys.argv[1];rows=data[key];folder=D/key;start=time.monotonic()
if (folder/'complete.json').exists():sys.exit(0)
for i,r in enumerate(rows):
 p=folder/'processed.private'/f"{r['id']:04d}.json"
 if p.exists():assert L(p)['source_generation_sha256']==r['generation_sha256'];continue
 if (lease/'yield.request').exists():save(lease/'yielded.json',dict(utc=utc(),before_row=i));sys.exit(75)
 tick=time.monotonic()
 try:z=preprocess_reply(r['response'],model,tok,plan)
 except Exception as e:
  save(p,dict(id=r['id'],source_generation_sha256=r['generation_sha256'],translation_status='exception',failure_type=type(e).__name__,translation_input_tokens=None,translation_output_tokens=None,primary_INVALID=True,plan_sha256=H(U/'language_nonzero36_execution.json')));raise
 status=z['status'];ok=not z['primary_INVALID'];top='empty' if status=='empty_passthrough' else 'ok' if ok else 'over_context_limit' if status=='translator_context_overflow' else 'exception'
 save(p,dict(id=r['id'],model=r['model'],family=r['family'],condition=r['condition'],source_generation_sha256=r['generation_sha256'],translation_status=top,failure_type=None if ok else status,translation_input_tokens=z.get('translator_input_tokens',0),translation_output_tokens=z.get('translator_new_tokens',0),elapsed_seconds=time.monotonic()-tick,site=site,physical_gpu=gpu,device_uuid=str(torch.cuda.get_device_properties(0).uuid),plan_sha256=H(U/'language_nonzero36_execution.json'),**z))
 save(lease/'live.json',dict(utc=utc(),phase='B1_reply_translation',cell=key,N=i+1,total=440,elapsed_seconds=time.monotonic()-start,no_judge_labels_read=True))
pack=[]
for r in rows:
 p=folder/'processed.private'/f"{r['id']:04d}.json";z=L(p);assert all(k in z for k in ['translation_status','failure_type','translation_input_tokens','translation_output_tokens']);response=z.get('processed_response') or ''
 pack.append({**r,'response':response,'raw_response_sha256':r['response_sha256'],'response_sha256':hashlib.sha256(response.encode()).hexdigest(),'preprocessing_sha256':H(p),'primary_preprocessing_INVALID':z['primary_INVALID']})
wave='language36_'+key;W=U/'score_waves'/wave;save(W/'inputs.private.json',pack);save(W/'manifest.json',dict(utc=utc(),N=440,judges=['SORRY'],inputs_sha256=H(W/'inputs.private.json'),scope='Indian nonzero preprocessing and cache only; no effect reads',translation_execution_sha256=H(U/'language_nonzero36_execution.json')));save(folder/'complete.json',dict(utc=utc(),N=440,wave=wave,metadata_coverage=1.,row_sha256={p.name:H(p) for p in (folder/'processed.private').glob('*.json')},plan_sha256=H(U/'language_nonzero36_execution.json')))
