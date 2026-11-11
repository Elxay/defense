"""Short prospective rendering/position engineering gate; not a batch label gate."""
from pathlib import Path
import os,sys,json,hashlib,time,datetime
import torch,numpy as np
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';T=R/'tools/handoff_20261106'
sys.path.insert(0,str(T));from batched_injection300 import generate_batch_with_injection
from crossmodel287_assets_and_render import model_path
key=sys.argv[1];P=U/'model_gate_schedule_rule17.json';plan=json.loads(P.read_text())
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(__file__)==plan['worker_sha256'];assert H(T/'batched_injection300.py')==plan['batch_core_sha256']
spec=plan['models'][key];D=U/'new_model_short_gates_rule17'/key;D.mkdir(parents=True,exist_ok=True)
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
source={r['id']:r for r in json.loads((U/'calibration700.private.json').read_text())}
assert H(U/'calibration700.private.json')==plan['engineering_source_sha256']
path=Path(spec['path']);tok=AutoTokenizer.from_pretrained(path,local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation=spec['attention']).eval()
assert model.config._attn_implementation==spec['attention']
model.generation_config.disable_compile=True
if key=='gemma':
 def forbidden(*a,**kw):raise RuntimeError('Auto compilation forbidden in Gemma engineering gate')
 model.get_compiled_call=forbidden
assert not hasattr(model.forward,'_torchdynamo_orig_callable')
zero=np.zeros(model.config.hidden_size,dtype=np.float32);vec=zero.copy();vec[0]=spec['rho']*.01
fixed=json.loads((U/'fixed_texts.private.json').read_text());assert H(U/'fixed_texts.private.json')==plan['fixed_texts_sha256']
block=model.model.layers[spec['layer']];orig=block.register_forward_hook;expected={};observed=[]
def checked_registration(fn,*a,**kw):
 def checked(module,args,output):
  h=output[0] if isinstance(output,tuple) else output;before=h.detach().clone();z=fn(module,args,output);after=(z[0] if isinstance(z,tuple) else z) if z is not None else h
  changed=(after.detach()!=before).any(-1);where=changed.nonzero().tolist()
  if expected.get('nonzero') and len(observed)==0:assert where==[[0,expected['position']]],where
  else:assert not where,where
  observed.append(where);return z
 return orig(checked,*a,**kw)
block.register_forward_hook=checked_registration
rows=[];torch.cuda.reset_peak_memory_stats();start=time.monotonic()
for rid in plan['engineering20_IDs']:
 prompt=source[rid]['prompt'];native=tok.apply_chat_template([dict(role='user',content=prompt)],add_generation_prompt=True)
 rendered=tok.apply_chat_template([dict(role='user',content=prompt)],add_generation_prompt=True,tokenize=False)
 pref=tok(rendered+fixed['prefill'],add_special_tokens=False)['input_ids'];assert pref[:len(native)]==native
 for name,ids,pos in [('native',native,len(native)-1),('P1',pref,len(pref)-1),('P2',pref,len(native)-1)]:
  expected.update(nonzero=False,position=pos);observed.clear()
  with torch.no_grad():ref=model.generate(torch.tensor([ids],device='cuda:0'),attention_mask=torch.ones((1,len(ids)),device='cuda:0',dtype=torch.long),max_new_tokens=32,do_sample=False,pad_token_id=tok.pad_token_id,disable_compile=True)
  ref_text=tok.decode(ref[0,len(ids):],skip_special_tokens=True)
  z=generate_batch_with_injection(model,tok,[ids],zero,layer=spec['layer'],positions=[pos],max_new_tokens=32,alpha=0)[0]
  assert z['text']==ref_text,(rid,name,'zero differs');assert z['injection_count']==1
  expected.update(nonzero=True,position=pos);observed.clear()
  y=generate_batch_with_injection(model,tok,[ids],vec,layer=spec['layer'],positions=[pos],max_new_tokens=1,alpha=1)[0]
  assert observed and y['injection_count']==1 and y['injection_position']==pos
  p=D/'references.private'/f'{rid}_{name}.json';save(p,dict(id=rid,variant=name,input_ids=ids,input_ids_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),plan_sha256=H(P),zero_result=z,nonzero_diagnostic=y))
  rows.append(dict(id=rid,variant=name,zero_bytes_equal=True,only_declared_position_changed=True,position=pos,reference_sha256=H(p)))
 save(D/'live.json',dict(utc=utc(),completed_prompts=len(rows)//3,N=20,phase='short_execution_gate_no_main_effects'))
free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();headroom=total-outside-torch.cuda.max_memory_reserved()
assert headroom>=3*1024**3,'Short gate headroom below3GiB; long family still locked'
save(D/'complete.json',dict(utc=utc(),N_prompts=20,variants=3,zero_bytes=60,position_checks=60,layer=spec['layer'],attention=spec['attention'],automatic_compile_forbidden=key=='gemma',headroom_GiB=headroom/1024**3,peak_reserved_GiB=torch.cuda.max_memory_reserved()/1024**3,elapsed_seconds=time.monotonic()-start,rows=rows,plan_sha256=H(P),not_2400_batch_label_gate=True,not_historical_same_batch_gate=True,reference_scope='prospective engineering B1 cap32 only',formal_generation_allowed=False))
