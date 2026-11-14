"""Sealed search88 alpha0 replay; label-free, matched B8/B4 2400 path."""
from pathlib import Path
import json,hashlib,datetime,os,sys,time
import numpy as np,torch
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T));from batched_injection300 import generate_batch_with_injection
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def L(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
group_name=sys.argv[1];P=L(U/'followup38/replay_execution_v3.json');entry=next(z for z in P['groups'] if z['group']==group_name);method=entry['method'];key=entry['model'];D=U/'followup38/replays'/group_name;assert H(__file__)==P['worker_sha256'];assert H(T/'batched_injection300.py')==P['batch_core_sha256']
M=L(D/'inputs_manifest.json');assert H(D/'inputs.private.json')==M['inputs_sha256'];rows=L(D/'inputs.private.json');N=M['N'];assert len(rows)==N and N in [78,88,220]
base=L(U/'ready_generation_plan.json');spec=base['models'][key];B=spec['batch_size'];assert B=={'llama':8,'qwen':4}[key];mp=Path(spec['model_paths']['innet'])
for n,h in spec['asset_interface_sha256'].items():assert H(mp/n)==h
lease=Path(os.environ['DEF_LEASE_DIR']);tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32);checks=[];start=time.monotonic()
for begin in range(0,N,B):
 group=rows[begin:begin+B];paths=[D/'generation.private'/f"{r['id']:04d}.json" for r in group]
 if not all(p.exists() for p in paths):
  ids=[r['input_ids'] for r in group];refs=None
  if begin<20:
   enc=tok.pad({'input_ids':ids},padding=True,return_tensors='pt').to('cuda:0');width=enc.input_ids.shape[1]
   with torch.inference_mode():raw=model.generate(**enc,max_new_tokens=2400,do_sample=False,pad_token_id=tok.pad_token_id)
   eos=model.generation_config.eos_token_id;eos={eos} if isinstance(eos,int) else set(eos or []);refs=[]
   for tail in raw[:,width:].tolist():
    cut=next((j+1 for j,t in enumerate(tail) if t in eos),len(tail));refs.append(tok.decode(tail[:cut],skip_special_tokens=True))
  torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();tick=time.monotonic();out=generate_batch_with_injection(model,tok,ids,zero,layer=spec['layer'],max_new_tokens=2400,alpha=0)
  torch.cuda.synchronize();free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();head=total-outside-torch.cuda.max_memory_reserved();assert head>=3*1024**3
  for j,(r,z,p) in enumerate(zip(group,out,paths)):
   assert z['injection_count']==1 and z['rho_runtime']==0
   if refs is not None:assert refs[j]==z['text'];checks.append(dict(id=r['id'],byte_equal=True))
   value=dict(id=r['id'],prompt_sha256=r['prompt_sha256'],behavior_sha256=r['behavior_sha256'],full_response_sha256=hashlib.sha256(z['text'].encode()).hexdigest(),result=z,plan_sha256=H(U/'followup38/replay_execution_v3.json'),search_source_sha256=r['search_source_sha256'])
   if p.exists():assert L(p)==value,'Partial batch changed; preserve and stop'
   else:save(p,value)
  save(D/'metrics'/f'{begin:04d}.json',dict(rows=len(group),seconds=time.monotonic()-tick,headroom_GiB=head/1024**3))
 save(lease/'live.json',dict(utc=utc(),method=method,model=key,N=min(begin+B,N),total=N,phase='alpha0_only_replay'))
 if begin<20:save(D/'zero20.json',dict(utc=utc(),passed=True,N_compared=len(checks),scope='first20 plus full fixed batches',checks=checks))
pack=[]
for r in rows:
 gp=D/'generation.private'/f"{r['id']:04d}.json";g=L(gp);pack.append(dict(id=r['id'],model=key,family=group_name,condition='alpha0',prompt=r['prompt'],behavior=r['behavior'],response=g['result']['text'],prompt_sha256=r['prompt_sha256'],behavior_sha256=r['behavior_sha256'],response_sha256=g['full_response_sha256'],generation_sha256=H(gp),preprocessing_sha256=None,primary_preprocessing_INVALID=r['missing_selected_prompt_fallback']))
W=U/'score_waves'/('order38_'+group_name);save(W/'inputs.private.json',pack);save(W/'manifest.json',dict(utc=utc(),N=N,judges=['SORRY'],inputs_sha256=H(W/'inputs.private.json'),scope='frozen alpha0 exploratory diagnostic only; no main gate change'))
save(D/'complete.json',dict(utc=utc(),N=N,generation_SHA={str(r['id']):H(D/'generation.private'/f"{r['id']:04d}.json") for r in rows},wave=W.name,elapsed_seconds=time.monotonic()-start,nonzero_generated=False))
