from pathlib import Path
import os,sys,json,hashlib,datetime,time,gc
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T));from batched_injection300 import generate_batch_with_injection
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();L=lambda p:json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'ASCII_tail34_plan.json');assert H(__file__)==P['worker_sha256'];oldP=U/'encoding_alpha0_plan_v2.json';assert H(oldP)==P['parent_plan_sha256'];E=L(oldP);spec=E['models']['llama'];cfg=spec['families']['ascii'];source=U/cfg['input_file'];assert H(source)==cfg['input_sha256'];by={str(r['id']):r for r in L(source)['llama']['ascii']};ids=cfg['ordered_IDs'][424:];assert len(ids)==16;D=U/'encoding_ASCII_tail34';mp=Path(spec['model_paths']['innet'])
for n,h in spec['asset_interface_sha256'].items():assert H(mp/n)==h
tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32);attempts=[];start=time.monotonic()
def run(members,B):
 rows=[by[str(i)] for i in members];paths=[D/'generation.private'/f'{int(i):04d}.json' for i in members]
 if all(p.exists() for p in paths):return
 torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();tick=time.monotonic();zs=None
 try:
  zs=generate_batch_with_injection(model,tok,[r['input_ids'] for r in rows],zero,layer=spec['layer'],max_new_tokens=2400,positions=[r['position'] for r in rows],alpha=0)
  torch.cuda.synchronize();free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();head=total-outside-torch.cuda.max_memory_reserved();assert head>=3*1024**3,'headroom below 3GiB'
  assert all(z['injection_count']==1 and z['rho_runtime']==0 for z in zs)
 except (torch.OutOfMemoryError,AssertionError) as e:
  attempts.append(dict(utc=utc(),IDs=[int(i) for i in members],B=B,passed=False,error=type(e).__name__,reason=str(e)[:150],seconds=time.monotonic()-tick));save(D/'attempts.json',attempts);del zs;gc.collect();torch.cuda.empty_cache()
  if B==1:raise
  for k in range(0,len(members),B//2):run(members[k:k+B//2],B//2)
  return
 attempts.append(dict(utc=utc(),IDs=[int(i) for i in members],B=B,passed=True,headroom_GiB=head/1024**3,seconds=time.monotonic()-tick));save(D/'attempts.json',attempts)
 for r,z,p in zip(rows,zs,paths):save(p,dict(id=r['id'],prompt_sha256=r['prompt_sha256'],behavior_sha256=r['behavior_sha256'],result=z,batch_size_actual=B,attempts_sha256_at_write=H(D/'attempts.json'),parent_plan_sha256=H(oldP),plan_sha256=H(U/'ASCII_tail34_plan.json'),device_uuid=str(torch.cuda.get_device_properties(0).uuid)))
for k in range(0,16,8):run(ids[k:k+8],8)
old=U/cfg['output_root']/'llama/ascii/alpha0/generation.private';files={}
for i in cfg['ordered_IDs']:
 p=old/f'{int(i):04d}.json' if str(i) not in set(map(str,ids)) else D/'generation.private'/f'{int(i):04d}.json';assert p.exists();files[str(i)]=dict(path=str(p.relative_to(R)),sha256=H(p),batch_size=L(p).get('batch_size_actual',8))
assert len(files)==440;save(D/'complete.json',dict(utc=utc(),N=440,old424_preserved=True,tail16_N=16,records=files,tail_seconds=time.monotonic()-start,mixed_batch_tail=True,plan_sha256=H(U/'ASCII_tail34_plan.json')))
