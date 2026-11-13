from pathlib import Path
import os,sys,json,hashlib,datetime,time
import numpy as np,torch
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T))
from batched_injection300 import generate_batch_with_injection
from u300_calibration_contract34 import assert_runtime_norm
sys.path.insert(0,str(R/'src'));from judge.refusal import new_rule
L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
P=L(U/'Mistral_calibration32_plan.json');raw=L(P['input_path']);rows=raw if isinstance(raw,list) else raw.get('rows') or raw['items'];v=np.load(P['vectors']['3']['path']).astype(np.float32)*np.float32(1.5);rho=P['vectors']['3']['norm'];D=U/'followup34/Mistral_alpha150_reference20';D.mkdir(parents=True,exist_ok=True)
tok=AutoTokenizer.from_pretrained(P['model']['path'],local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(P['model']['path'],local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();ids=[tok.apply_chat_template([dict(role='user',content=r.get('prompt') or r.get('text'))],add_generation_prompt=True) for r in rows[:24]]
start=time.monotonic();out={}
for B in [8,1]:
 limit=24 if B==8 else 20;pack=[]
 for k in range(0,limit,B):
  zs=generate_batch_with_injection(model,tok,ids[k:k+B],v,layer=9,max_new_tokens=120,alpha=1.5)
  for i,z in enumerate(zs,k):
   assert z['injection_count']==1;assert_runtime_norm(z['rho_runtime'],1.5,rho);save(D/f'B{B}.private'/f'{i:04d}.json',z);pack.append(z)
 out[B]=pack
cached=Path(P['output_root'])/'s3_a1.50/generation.private';checks=[]
for i in range(20):
 old=L(cached/f'{i:04d}.json')['result'];a=out[8][i];b=out[1][i];checks.append(dict(id=i,B8_cross_card_byte_equal=a['text']==old['text'],B1_vs_B8_byte_equal=b['text']==a['text'],B1_v2=bool(new_rule(b['text'])),B8_v2=bool(new_rule(a['text']))))
z=dict(utc=utc(),N=20,alpha=1.5,seed=3,cap=120,B8_cross_card_exact=sum(r['B8_cross_card_byte_equal'] for r in checks),B1_B8_exact=sum(r['B1_vs_B8_byte_equal'] for r in checks),v2_B1_only=sum(r['B1_v2'] and not r['B8_v2'] for r in checks),v2_B8_only=sum(r['B8_v2'] and not r['B1_v2'] for r in checks),checks=checks,elapsed_seconds=time.monotonic()-start,main2400_gate_passed=False)
save(D/'result.json',z);print(json.dumps(z))
