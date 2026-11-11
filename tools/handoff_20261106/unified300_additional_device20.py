"""Device/node alpha0 byte gate only; no main label reading."""
from pathlib import Path
import json,hashlib,sys,time,datetime,os,threading
import numpy as np, torch
from transformers import AutoTokenizer,AutoModelForCausalLM
from batched_injection300 import generate_batch_with_injection
ROOT=Path(sys.argv[1]);key=sys.argv[2];physical=int(sys.argv[3]);site=sys.argv[4];U=ROOT/'results/audit/unified300';P=json.loads((U/'parallel_device20_additional_cards_plan.json').read_text());S=P['models'][key]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(o,indent=2)+'\n');q.replace(p)
assert sha(__file__)==P['worker_sha256'];assert sha(ROOT/'tools/handoff_20261106/batched_injection300.py')==P['batch_core_sha256'];assert os.environ['CUDA_VISIBLE_DEVICES']==str(physical)
O=U/'parallel_device20'/site/key;save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='verify_assets',physical_gpu=physical))
modelpath=Path(S['model_paths'][site]);verified={}
for n,h in S['files_sha256'].items():assert sha(modelpath/n)==h,n;verified[n]=h
payload=U/'parallel_device20_inputs.private.json';assert sha(payload)==P['private_input_sha256'];data=json.loads(payload.read_text())[key];tick=time.monotonic()
tok=AutoTokenizer.from_pretrained(modelpath,local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(modelpath,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();pairs=[];zero=np.zeros(model.config.hidden_size,dtype=np.float32)
for batch in data:
 save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='byte_gate_generation',physical_gpu=physical,covered_rows=len(pairs),batch_size=S['batch_size']))
 z=generate_batch_with_injection(model,tok,[r['input_ids']for r in batch],zero,layer=S['layer'],max_new_tokens=2400,positions=[r['position']for r in batch],source_vector_sha256=None,alpha=0)
 for r,out in zip(batch,z):
  assert out['injection_count']==1 and out['rho_runtime']==0
  pairs.append(dict(id=r['id'],selected=r['selected20'],byte_equal=out['text']==r['reference'],source_sha256=hashlib.sha256(r['reference'].encode()).hexdigest(),actual_sha256=hashlib.sha256(out['text'].encode()).hexdigest(),injection_count=out['injection_count'],rho_runtime=out['rho_runtime']))
  save(O/'outputs.private'/f"{r['id']:04d}.json",dict(id=r['id'],result=out))
sel=[x for x in pairs if x['selected']];assert len(sel)==20
save(O/'complete.json',dict(utc=utc(),model=key,site=site,physical_gpu=physical,pid=os.getpid(),N_selected=20,exact_selected=sum(x['byte_equal']for x in sel),covered=len(pairs),passed=all(x['byte_equal']for x in pairs),pairs=pairs,verified_asset_files=len(verified),plan_sha256=sha(U/'parallel_device20_additional_cards_plan.json'),seconds_including_model_load=time.monotonic()-tick,device_uuid=str(torch.cuda.get_device_properties(0).uuid),no_primary_labels_read=True));print('DEVICE_GATE_DONE',key,site,all(x['byte_equal']for x in pairs),flush=True)
