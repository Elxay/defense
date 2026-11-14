from pathlib import Path
import os,sys,json,hashlib,datetime,time,gc
import torch,numpy as np
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T));from batched_injection300 import generate_batch_with_injection
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();L=lambda p:json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'encoding_missing36_plan.json');assert H(__file__)==P['worker_sha256'];f=sys.argv[1];assert f in ['caesar','morse'];parent=U/'encoding_alpha0_plan_v2.json';assert H(parent)==P['parent_plan_sha256'];spec=L(parent)['models']['llama'];cfg=spec['families'][f];I=U/cfg['input_file'];assert H(I)==cfg['input_sha256'];by={str(r['id']):r for r in L(I)['llama'][f]};old=U/cfg['output_root']/'llama'/f/'alpha0/generation.private';D=U/'encoding_missing36'/f;mp=Path(spec['model_paths']['innet']);lease=Path(os.environ['DEF_LEASE_DIR'])
for n,h in spec['asset_interface_sha256'].items():assert H(mp/n)==h
tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token;model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32);attempts=L(D/'attempts.json') if (D/'attempts.json').exists() else []
def run(ids,B):
 paths=[D/'generation.private'/f'{int(i):04d}.json' for i in ids]
 if all(p.exists() for p in paths):return
 if (lease/'yield.request').exists():save(lease/'yielded.json',dict(utc=utc(),before_IDs=ids));sys.exit(75)
 rs=[by[str(i)] for i in ids];torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();tick=time.monotonic();failed=None;zs=None
 try:
  zs=generate_batch_with_injection(model,tok,[r['input_ids'] for r in rs],zero,layer=spec['layer'],max_new_tokens=2400,positions=[r['position'] for r in rs],alpha=0);free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();head=total-outside-torch.cuda.max_memory_reserved();assert head>=3*1024**3,'peak headroom below3GiB';assert all(z['injection_count']==1 and z['rho_runtime']==0 for z in zs)
 except (torch.OutOfMemoryError,AssertionError) as e:failed=dict(type=type(e).__name__,reason=str(e)[:160]);zs=None
 if failed:
  attempts.append(dict(utc=utc(),IDs=ids,B=B,passed=False,wall_seconds=time.monotonic()-tick,**failed));save(D/'attempts.json',attempts)
  if B==1:raise RuntimeError('B1 memory assertion failed; keep gap visible')
  gc.collect();torch.cuda.empty_cache();n=4 if B==8 else 1
  for k in range(0,len(ids),n):run(ids[k:k+n],n)
  return
 seconds=time.monotonic()-tick;attempts.append(dict(utc=utc(),IDs=ids,B=B,passed=True,headroom_GiB=head/1024**3,wall_seconds=seconds));save(D/'attempts.json',attempts)
 for r,z,p in zip(rs,zs,paths):save(p,dict(id=r['id'],prompt_sha256=r['prompt_sha256'],behavior_sha256=r['behavior_sha256'],result=z,batch_size_actual=B,batch_wall_seconds=seconds,device_uuid=str(torch.cuda.get_device_properties(0).uuid),parent_plan_sha256=H(parent),plan_sha256=H(U/'encoding_missing36_plan.json')))
for batch in cfg['batches']:
 missing=[i for i in batch if not (old/f'{int(i):04d}.json').exists()]
 if missing:assert len(missing)==len(batch);run(missing,8)
records={}
for i in cfg['ordered_IDs']:
 p=old/f'{int(i):04d}.json';p=p if p.exists() else D/'generation.private'/p.name;assert p.exists();records[str(i)]=dict(path=str(p.relative_to(R)),sha256=H(p),batch_size=L(p).get('batch_size_actual',8))
assert len(records)==440;save(D/'complete.json',dict(utc=utc(),N=440,records=records,old_prefix_preserved=True,plan_sha256=H(U/'encoding_missing36_plan.json')))
