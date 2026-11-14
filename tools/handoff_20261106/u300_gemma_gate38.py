"""Bounded single-card Gemma zero-hook engineering window, no model-result reads."""
from pathlib import Path
import os,sys,time,json,hashlib,datetime
os.environ['TORCHDYNAMO_DISABLE']='1'
import torch,numpy as np
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T))
from batched_injection300 import generate_batch_with_injection
from crossmodel287_assets_and_render import model_path,render
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
L=lambda p:json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'followup38/Gemma_zero20_plan.json');assert H(__file__)==P['worker_sha256'];assert H(T/'batched_injection300.py')==P['batch_core_sha256'];I=R/P['input_relative'];assert H(I)==P['input_sha256'];rows=L(I)['legal400'][:20];D=U/'followup38/Gemma_zero20';lease=Path(os.environ['DEF_LEASE_DIR']);start=time.monotonic()
save(lease/'live.json',dict(utc=utc(),phase='Gemma_assets_and_model_loading',N=0,total=20))
tok=AutoTokenizer.from_pretrained(model_path('gemma'),local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token_id=tok.eos_token_id
model=AutoModelForCausalLM.from_pretrained(model_path('gemma'),local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager',device_map={'':'cuda:0'}).eval();model.generation_config.disable_compile=True
def forbid(*args,**kwargs):raise RuntimeError('Gemma automatic compilation forbidden')
model.get_compiled_call=forbid;assert model.config._attn_implementation=='eager' and model.generation_config.disable_compile is True and not hasattr(model.forward,'_torchdynamo_orig_callable')
zero=np.zeros(model.config.hidden_size,dtype=np.float32);checks=[]
for i,r in enumerate(rows):
 if time.monotonic()-start>7200:
  save(D/'budget_stop.json',dict(utc=utc(),N=len(checks),cap_GPUh=2,partial=True,no_forced_kill=True));sys.exit(0)
 ids=render(tok,'gemma',r['prompt']);enc=tok.pad({'input_ids':[ids]},padding=True,return_tensors='pt').to('cuda:0');width=enc.input_ids.shape[1];torch.cuda.reset_peak_memory_stats()
 with torch.inference_mode():raw=model.generate(**enc,max_new_tokens=2400,do_sample=False,pad_token_id=tok.pad_token_id)
 eos=model.generation_config.eos_token_id;eos={eos} if isinstance(eos,int) else set(eos or []);tail=raw[0,width:].tolist();cut=next((j+1 for j,t in enumerate(tail) if t in eos),len(tail));ref=tok.decode(tail[:cut],skip_special_tokens=True)
 z=generate_batch_with_injection(model,tok,[ids],zero,layer=12,max_new_tokens=2400,alpha=0)[0];free,total=torch.cuda.mem_get_info();head=total-(total-free-torch.cuda.memory_reserved())-torch.cuda.max_memory_reserved();assert head>=3*1024**3
 check=dict(id=r['id'],byte_equal=z['text']==ref,injection_count=z['injection_count'],rho_runtime=z['rho_runtime'],headroom_GiB=head/1024**3,input_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),device_uuid=str(torch.cuda.get_device_properties(0).uuid));checks.append(check);save(D/'rows.private'/f'{i:03d}.json',dict(check=check,response=z['text'],reference=ref));save(lease/'live.json',dict(utc=utc(),phase='Gemma_B1_eager_zero20',N=i+1,total=20));assert check['byte_equal'] and z['injection_count']==1 and z['rho_runtime']==0
save(D/'complete.json',dict(utc=utc(),N=20,passed=True,checks=checks,elapsed_seconds=time.monotonic()-start,scope='B1 native/nohook versus zero hook 2400; no historical compiled equivalence or 100-label admission claimed',training_admitted=False,plan_sha256=H(U/'followup38/Gemma_zero20_plan.json')))
