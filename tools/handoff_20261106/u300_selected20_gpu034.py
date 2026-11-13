from pathlib import Path
import os,sys,json,hashlib,datetime
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T));from batched_injection300 import generate_batch_with_injection
L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
spec=L(U/'ready_generation_plan.json')['models']['qwen'];D=U/'search132_alpha0_v31/PAIR/qwen';rows=L(D/'inputs.private.json')[:20];mp=spec['model_paths']['innet'];tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32);checks=[];O=U/'followup34/selected20_GPU0'
for k in range(0,20,4):
 zs=generate_batch_with_injection(model,tok,[r['input_ids'] for r in rows[k:k+4]],zero,layer=spec['layer'],max_new_tokens=2400,alpha=0)
 for r,z in zip(rows[k:k+4],zs):
  old=D/'generation.private'/f"{r['id']:04d}.json";baseline=L(old);assert z['injection_count']==1 and z['rho_runtime']==0;checks.append(dict(id=r['id'],byte_equal=z['text']==baseline['result']['text'],baseline_generation_sha256=H(old),new_response_sha256=hashlib.sha256(z['text'].encode()).hexdigest()));save(O/'observed.private'/f"{r['id']:04d}.json",z)
save(O/'result.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),N=20,byte_equal=sum(r['byte_equal'] for r in checks),passed=all(r['byte_equal'] for r in checks),cap=2400,B=4,selected_reference_GPU=2,replay_GPU=0,device_uuid=str(torch.cuda.get_device_properties(0).uuid),checks=checks,posthoc_engineering_check=True,no_effect_selection_changed=True))
