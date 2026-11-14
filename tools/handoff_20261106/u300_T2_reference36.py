from pathlib import Path
import os,sys,json,hashlib,datetime,math
import torch,numpy as np
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T));from batched_injection300 import generate_batch_with_injection
L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
m,f,physical=sys.argv[1:];P=L(U/'T2_routing36.json');assert H(__file__)==P['reference_worker_sha256'];spec=P['generation_cells'][m+'_'+f];p=R/spec['plan_relative'];assert H(p)==spec['plan_sha256'];plan=L(p);s=plan['models'][m];cfg=s['families'][f];I=U/cfg['input_file'];assert H(I)==cfg['input_sha256'];by={str(r['id']):r for r in L(I)[m][f]};B=s['batch_size'];wanted=cfg['ordered_IDs'][:20];groups=cfg['batches'][:math.ceil(20/B)];mp=Path(s['model_paths']['innet'])
for n,h in s['asset_interface_sha256'].items():assert H(mp/n)==h
tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token;model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32);checks=[]
for group in groups:
 rs=[by[str(i)] for i in group];zs=generate_batch_with_injection(model,tok,[r['input_ids'] for r in rs],zero,layer=s['layer'],max_new_tokens=2400,positions=[r['position'] for r in rs],alpha=0)
 for r,z in zip(rs,zs):
  gp=R/cfg['historical_alpha0_relative']/'generation.private'/f"{int(r['id']):04d}.json";old=L(gp);assert z['injection_count']==1 and z['rho_runtime']==0;checks.append(dict(id=r['id'],selected=str(r['id']) in set(map(str,wanted)),byte_equal=z['text']==old['result']['text'],reference_sha256=H(gp)))
out=U/'followup36/Indian_reference36'/f'{m}_{f}_gpu{physical}.json';save(out,dict(utc=utc(),N_selected=20,N_covered=len(checks),passed=all(x['byte_equal'] for x in checks),checks=checks,plan_sha256=H(p),device_uuid=str(torch.cuda.get_device_properties(0).uuid),site='innet',physical_gpu=int(physical),B=B,cap=2400));assert all(x['byte_equal'] for x in checks)
