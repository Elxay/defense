from pathlib import Path
import os,sys,json,hashlib,datetime,time
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';sys.path.insert(0,str(R/'tools/handoff_20261106'));from batched_injection300 import generate_batch_with_injection
L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'ready_generation_plan_B4_ml.json');spec=P['models']['llama'];cfg=spec['families']['translate-ml'];I=U/cfg['input_file'];assert H(I)==cfg['input_sha256'];by={str(r['id']):r for r in L(I)['llama']['translate-ml']};mp=spec['model_paths']['node01'];tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32);D=U/'followup35/Lml_node1_reference';selected=set(cfg['ordered_IDs'][:20]);checks=[];start=time.monotonic()
for members in cfg['batches']:
 if not selected.intersection(members):continue
 rows=[by[i] for i in members];torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();zs=generate_batch_with_injection(model,tok,[r['input_ids'] for r in rows],zero,layer=spec['layer'],max_new_tokens=2400,positions=[r['position'] for r in rows],alpha=0);free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();head=total-outside-torch.cuda.max_memory_reserved();assert head>=3*1024**3
 for r,z in zip(rows,zs):
  p=U/cfg['output_root']/'llama/translate-ml/alpha0/generation.private'/f"{r['id']:04d}.json";old=L(p);assert z['injection_count']==1 and z['rho_runtime']==0;checks.append(dict(id=r['id'],selected=str(r['id']) in selected,byte_equal=z['text']==old['result']['text'],source_generation_sha256=H(p),headroom_GiB=head/1024**3));save(D/'observed.private'/f"{r['id']:04d}.json",z)
save(D/'result.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=all(r['byte_equal'] for r in checks),N_selected=sum(r['selected'] for r in checks),N_exact=sum(r['selected'] and r['byte_equal'] for r in checks),checks=checks,elapsed_seconds=time.monotonic()-start,old_gpu=2,new_gpu=1,site='node01',plan_sha256=H(U/'ready_generation_plan_B4_ml.json')))
assert all(r['byte_equal'] for r in checks)
