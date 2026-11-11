"""Mistral training-prerequisite native baseline, not unified700 or test data."""
from pathlib import Path
import datetime,hashlib,json,os,sys,time
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T))
from batched_injection300 import generate_batch_with_injection
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def L(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
P=L(U/'mistral_prereview_baseline_plan.json');assert H(__file__)==P['worker_sha256']
assets=L(R/P['assets_relative']);assert H(R/P['assets_relative'])==P['assets_sha256']
assert H(R/P['inputs_relative'])==P['inputs_sha256'];data=L(R/P['inputs_relative']);mp=Path(assets['model_path'])
for n,v in assets['files'].items():
 h=v['sha256'] if isinstance(v,dict) else v;assert H(mp/n)==h
lease=Path(os.environ['DEF_LEASE_DIR']);D=U/'mistral_native_prereview_v1';start=time.monotonic()
def pulse(phase,**kw):save(lease/'live.json',dict(utc=utc(),pid=os.getpid(),phase=phase,**kw))
pulse('loading_native_Mistral');tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,device_map={'':'cuda:0'}).eval()
zero=np.zeros(model.config.hidden_size,dtype=np.float32)
def gen(group,cap,hook):
 ids=[tok.apply_chat_template([{'role':'user','content':r['prompt']}],add_generation_prompt=True) for r in group]
 if hook:return generate_batch_with_injection(model,tok,ids,zero,layer=9,max_new_tokens=cap,positions=[len(v)-1 for v in ids],source_vector_sha256=None,alpha=0)
 enc=tok.pad({'input_ids':ids},padding=True,return_tensors='pt').to('cuda:0');width=enc.input_ids.shape[1]
 with torch.inference_mode():z=model.generate(**enc,max_new_tokens=cap,do_sample=False,pad_token_id=tok.pad_token_id)
 eos=model.generation_config.eos_token_id;eos={eos} if isinstance(eos,int) else set(eos or [])
 out=[]
 for row in z[:,width:].tolist():
  cut=next((i+1 for i,v in enumerate(row) if v in eos),len(row));out.append(tok.decode(row[:cut],skip_special_tokens=True))
 return out
if not (D/'zero20_gate.json').exists():
 checks=[]
 for i in range(0,24,8):
  group=data['legal400'][i:i+8];ref=gen(group,120,False);z=gen(group,120,True)
  checks += [dict(id=r['id'],selected=i+j<20,byte_equal=a==b['text']) for j,(r,a,b) in enumerate(zip(group,ref,z))]
 passed=all(r['byte_equal'] for r in checks)
 save(D/'zero20_gate.json',dict(utc=utc(),passed=passed,N_selected=20,selected_exact=sum(r['selected'] and r['byte_equal'] for r in checks),checks=checks,plan_sha256=H(U/'mistral_prereview_baseline_plan.json')))
 assert passed
assert L(D/'zero20_gate.json')['passed']
for split,B,cap in [('legal400',8,120),('val70',1,2400)]:
 for i in range(0,len(data[split]),B):
  group=data[split][i:i+B];paths=[D/split/(r['id']+'.json') for r in group]
  if all(p.exists() for p in paths):
   assert all(L(p)['plan_sha256']==H(U/'mistral_prereview_baseline_plan.json') for p in paths);continue
  if (lease/'yield.request').exists():sys.exit(75)
  out=gen(group,cap,True)
  for r,z,p in zip(group,out,paths):
   assert z['injection_count']==1 and z['rho_runtime']==0
   value=dict(id=r['id'],prompt_sha256=r['prompt_sha256'],in_fixed388=r.get('in_fixed388'),result=z,
       plan_sha256=H(U/'mistral_prereview_baseline_plan.json'))
   if p.exists():assert L(p)==value
   else:save(p,value)
  pulse(split,completed=min(i+B,len(data[split])),total=len(data[split]),cap=cap)
save(D/'complete.json',dict(utc=utc(),n_legal400=400,n_legal388=388,n_val70=70,
    plan_sha256=H(U/'mistral_prereview_baseline_plan.json'),no_refusal_review_collected=True,
    not_unified700_calibration=True,training_allowed=False,seconds=time.monotonic()-start))
