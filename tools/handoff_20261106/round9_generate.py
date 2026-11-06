"""Resumable paired-control grid/full generation; each condition uses identical evaluation code."""
from pathlib import Path
import argparse,os,sys,json,time,hashlib,datetime,socket,ast
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--card',type=int,required=True);p.add_argument('--phase',choices=['grid','full'],required=True);a=p.parse_args();B=Path(a.root);T=B/'results/style_retrained';O=B/'results/audit/handoff_round9';O.mkdir(exist_ok=True);D=T/f'eval_s{a.seed}';D.mkdir(exist_ok=True);assert os.environ.get('CUDA_VISIBLE_DEVICES')==str(a.card)
sys.path.insert(0,str(B/'src'));from gen.common import generate_with_injection
assert a.seed in range(3,8)
def check_deadline():
 assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc),'11/10 00:00 JST hard stop'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def pulse(phase,**kw):atomic(O/f'generate_{a.phase}_s{a.seed}_live.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),host=socket.gethostname(),physical_gpu=a.card,phase=phase,**kw))
add=B/'docs/252_ADDENDUM2_RETRAINED_CONTROLS.md';assert sha(add)=='493094393b6f2294498c3cf01a449f2b7557f23784530f9e8e002066f56e1896'
snapshot=('/data/ray/hub'if B==Path('/home/dell/Def')else'/data/huggingface/hub')+'/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659'
pulse('loading_model');tok=AutoTokenizer.from_pretrained(snapshot,local_files_only=True);mdl=AutoModelForCausalLM.from_pretrained(snapshot,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval();mdl.config.use_cache=True
val=json.loads((B/'results/audit/handoff_round9/val70_generation_prompts.json').read_text());legal=json.loads((B/'data/legal_val_items.json').read_text());assert len(val)==70 and len(legal)==400
# The original batch8 hook/function and all400 rows preserve baseline batch composition.
source=B/'src/eval/legal_val_batch.py';fn=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='run_batch');scope=dict(torch=torch,tok=tok,mdl=mdl,DEV='cuda:0',LAYER=9);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),scope)
def open_cache(path,signature):
 d=json.loads(path.read_text())if path.exists()else dict(metadata=signature,items={});assert d['metadata']==signature,'cache signature mismatch, never overwrite';return d
def single(path,rows,vector,signature,maxnew,label):
 d=open_cache(path,signature);assert set(d['items'])<={r['id']for r in rows};start=time.monotonic();initial=len(d['items']);completed_start=time.monotonic()
 for r in rows:
  check_deadline()
  if r['id']in d['items']:continue
  ids=tok.apply_chat_template([{'role':'user','content':r['prompt']}],add_generation_prompt=True,return_tensors='pt').to('cuda:0');out=generate_with_injection(mdl,tok,ids,vector,layer=9,max_new_tokens=maxnew,device='cuda:0');d['items'][r['id']]=out;n=len(d['items']);spi=(time.monotonic()-start)/(n-initial);pulse(label,n=n,total=len(rows),seconds_per_item=spi,condition=signature['condition'],alpha=signature['alpha'])
  if n%10==0:atomic(path,d)
  if n-initial==25:print('SPEED25',label,signature['condition'],spi,flush=True)
 atomic(path,d);assert len(d['items'])==len(rows)
 return d
control_run='repeatA_s3'if a.seed==3 else f'control_s{a.seed}';conditions=[('control',1.,control_run),*([('treatment',z,f'treatment_s{a.seed}')for z in[.25,.5,.75,1.,1.25,1.5]]if a.phase=='grid'else[('treatment',json.loads((T/'alpha_matches_frozen.json').read_text())['rows'][str(a.seed)]['selected_alpha'],f'treatment_s{a.seed}')])]
if a.phase=='full':
 matches=json.loads((T/'alpha_matches_frozen.json').read_text());assert matches['all_comparable']and matches['addendum2_sha256']==sha(add);harm=json.loads((B/'configs/stage0_data/wjb300.json').read_text());pairs=json.loads((B/'configs/stage0_data/wjb_benign246_pairs300.json').read_text());assert len(harm)==300 and len(pairs)==300
for condition,alpha,runid in conditions:
 vp=T/runid/'v.npy';v=np.load(vp).astype('float32');v=v/np.linalg.norm(v)*(5.21*alpha);tag=f'{condition}_a{alpha:g}';signature=dict(seed=a.seed,condition=condition,alpha=alpha,vector_sha256=sha(vp),worker_sha256=sha(Path(__file__)),common_sha256=sha(B/'src/gen/common.py'),addendum2_sha256=sha(add),model_snapshot='0e9e39f249a16976918f6564b8830bc894c89659',val_prompts_sha256=sha(B/'results/audit/handoff_round9/val70_generation_prompts.json'),legal_manifest_sha256=sha(B/'data/legal_val_items.json'),host=socket.gethostname(),physical_card=a.card)
 if a.phase=='grid':
  # seed3's predetermined repeatA already has validated generation; recompute if another host/card to keep cache attestation simple.
  single(D/(tag+'_val70.json'),[dict(id=k,prompt=p)for k,p in val.items()],v,dict(**signature,max_new_tokens=2400),2400,'val70')
  lp=D/(tag+'_legal400.json');d=open_cache(lp,dict(**signature,max_new_tokens=120,batch_size=8));tok.padding_side='left';tok.pad_token=tok.eos_token;scope['vec']=v;begin=time.monotonic();initial=len(d['items'])
  for offset in range(0,400,8):
   check_deadline()
   batch=legal[offset:offset+8];keys=[r['key']for r in batch];present=[k in d['items']for k in keys];assert all(present)or not any(present),'partial batch cache cannot change batch composition'
   if all(present):continue
   prepared=[(offset+i,r['group'],r['prompt'])for i,r in enumerate(batch)];texts=scope['run_batch'](prepared)
   for r,t in zip(batch,texts):d['items'][r['key']]=dict(text=t,alpha=alpha)
   atomic(lp,d);pulse('legal400',n=len(d['items']),total=400,condition=condition,alpha=alpha,seconds_per_item=(time.monotonic()-begin)/max(1,len(d['items'])-initial))
  assert len(d['items'])==400;tok.padding_side='right'
 else:
  single(D/(tag+'_wjb300.json'),[dict(id=r['id'],prompt=r['adversarial'])for r in harm],v,dict(**signature,manifest_sha256=sha(B/'configs/stage0_data/wjb300.json'),max_new_tokens=2400),2400,'wjb300')
  rows=[dict(id=r['id']+'|'+side,prompt=r[side])for r in pairs for side in ['vanilla','adversarial']]
  single(D/(tag+'_pairs600.json'),rows,v,dict(**signature,manifest_sha256=sha(B/'configs/stage0_data/wjb_benign246_pairs300.json'),max_new_tokens=120),120,'pairs600')
pulse('complete',phase_completed=a.phase);print('GENERATION_COMPLETE',a.phase,a.seed,flush=True)
