"""Independent 2400-token alpha0 PAIR timing-row replay; no nonzero outputs."""
from pathlib import Path
import datetime,hashlib,json,os,sys,time
import torch,numpy as np
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106'
sys.path.insert(0,str(T))
from batched_injection300 import generate_batch_with_injection
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def L(p):return json.loads(Path(p).read_text())
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
D=U/'PAIR_alpha0_independent_replay';P=L(D/'plan.json');assert H(__file__)==P['worker_sha256']
assert H(D/'inputs.private.json')==P['inputs_sha256'];data=L(D/'inputs.private.json')
base=L(U/'ready_generation_plan.json');pack=[];lease=Path(os.environ['DEF_LEASE_DIR'])
for key in ['llama','qwen']:
 spec=base['models'][key];rows=data[key];B=spec['batch_size'];mp=Path(spec['model_paths']['innet'])
 for n,h in spec['asset_interface_sha256'].items():assert H(mp/n)==h
 tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left'
 if tok.pad_token_id is None:tok.pad_token=tok.eos_token
 model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,
          attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32)
 start=time.monotonic();checks=[]
 for begin in range(0,len(rows),B):
  group=rows[begin:begin+B];ids=[r['input_ids'] for r in group]
  paths=[D/key/'generation.private'/f"{r['id']:04d}.json" for r in group]
  if not all(p.exists() for p in paths):
   enc=tok.pad({'input_ids':ids},padding=True,return_tensors='pt').to('cuda:0');width=enc.input_ids.shape[1]
   with torch.inference_mode():raw=model.generate(**enc,max_new_tokens=2400,do_sample=False,pad_token_id=tok.pad_token_id)
   eos=model.generation_config.eos_token_id;eos={eos} if isinstance(eos,int) else set(eos or [])
   refs=[]
   for tail in raw[:,width:].tolist():
    cut=next((j+1 for j,t in enumerate(tail) if t in eos),len(tail));refs.append(tok.decode(tail[:cut],skip_special_tokens=True))
   out=generate_batch_with_injection(model,tok,ids,zero,layer=spec['layer'],max_new_tokens=2400,
          positions=[len(v)-1 for v in ids],source_vector_sha256=None,alpha=0)
   for r,z,ref,p in zip(group,out,refs,paths):
    assert z['injection_count']==1 and z['rho_runtime']==0
    checks.append(dict(id=r['id'],byte_equal=z['text']==ref))
    save(p,dict(id=r['id'],result=z,prompt_sha256=r['prompt_sha256'],full_response_sha256=digest(z['text']),
      plan_sha256=H(D/'plan.json'),reference_sha256=digest(ref),reference_byte_equal=z['text']==ref))
   assert all(c['byte_equal'] for c in checks),'Replay native/nohook vs zero-hook mismatch'
  save(lease/'live.json',dict(utc=utc(),model=key,N_completed=min(begin+B,len(rows)),N=10,phase='independent_alpha0_replay'))
 for r in rows:
  gp=D/key/'generation.private'/f"{r['id']:04d}.json";g=L(gp)
  assert g['reference_byte_equal']
  pack.append(dict(id=r['id'],model=key,family='PAIR_pilot_diagnostic',condition='alpha0',prompt=r['prompt'],
    behavior=r['behavior'],response=g['result']['text'],prompt_sha256=r['prompt_sha256'],
    behavior_sha256=r['behavior_sha256'],response_sha256=g['full_response_sha256'],generation_sha256=H(gp)))
 save(D/key/'complete.json',dict(utc=utc(),N=10,reference_equal=10,seconds=time.monotonic()-start))
 del model;torch.cuda.empty_cache()
W=U/'score_waves/PAIR_alpha0_diagnostic';save(W/'inputs.private.json',pack)
save(W/'manifest.json',dict(utc=utc(),N=20,judges=['SORRY'],inputs_sha256=H(W/'inputs.private.json'),
    schedule_sha256=H(U/'scoring_schedule_v1.json'),scope='Only authorized independent alpha0 diagnostic'))
save(D/'complete.json',dict(utc=utc(),N=20,reference_comparison_generations=20,main_replay_generations=20,
                          no_nonzero_generated_or_read=True))
