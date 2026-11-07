"""Resumable paired-control grid/full generation; each condition uses identical evaluation code."""
from pathlib import Path
import argparse,os,sys,json,time,hashlib,datetime,socket,ast
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--card',type=int,required=True);p.add_argument('--phase',choices=['grid','full'],required=True);a=p.parse_args();B=Path(a.root);T=B/'results/plain_arm';O=B/'results/audit/handoff_round11';O.mkdir(exist_ok=True);D=T/f'eval_s{a.seed}';D.mkdir(exist_ok=True);assert os.environ.get('CUDA_VISIBLE_DEVICES')==str(a.card)
sys.path.insert(0,str(B/'src'));from gen.common import generate_with_injection
assert a.seed in range(3,8)
def check_deadline():
 assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc),'11/10 00:00 JST hard stop'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def pulse(phase,**kw):
 if 'seconds_per_item'in kw and 'n'in kw and 'total'in kw:
  kw['estimated_remaining_seconds_current_file']=max(0,kw['total']-kw['n'])*kw['seconds_per_item'];kw['speed_sample_at_least25']=kw['n']>=25
 atomic(O/f'generate_{a.phase}_s{a.seed}_live.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),host=socket.gethostname(),physical_gpu=a.card,phase=phase,**kw))
add=B/'docs/252_ADDENDUM3_PLAIN_ARM_INTERPOLATION.md';assert sha(add)=='e92456d65278081f8b1c6b6acd1b165c8219b4c9a62af0bcbb2e6e58ad852195'
assert sha(B/'docs/252_ADDENDUM4_FIVE_PLAIN_SEEDS_NOISE_REFERENCE.md')=='95b9605403552e2c7503d5a74f9222c4c2fadf08fa186643fbf18dc5e137f64f'
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
  if n-initial==25:
   speed=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),seconds_per_item=spi,n_newly_completed=25,signature=signature);atomic(D/f'speed25_{a.phase}_{signature["condition"]}_a{signature["alpha"]:g}_{label}.json',speed);print('SPEED25',label,signature['condition'],spi,flush=True)
 atomic(path,d);assert len(d['items'])==len(rows)
 return d
conditions=[('plain',z,f'plain_s{a.seed}')for z in([.25,.5,.75,1.,1.25,1.5]if a.phase=='grid'else json.loads((T/'alpha_plan_frozen.json').read_text())['rows'][str(a.seed)]['endpoint_alphas'])]
if a.phase=='full':
 matches=json.loads((T/'alpha_plan_frozen.json').read_text());assert matches['all_comparable']and matches['addendum3_sha256']==sha(add);harm=json.loads((B/'configs/stage0_data/wjb300.json').read_text());pairs=json.loads((B/'configs/stage0_data/wjb_benign246_pairs300.json').read_text());assert len(harm)==300 and len(pairs)==300
for condition,alpha,runid in conditions:
 vp=T/runid/'v.npy';v=np.load(vp).astype('float32');v=v/np.linalg.norm(v)*(5.21*alpha);tag=f'{condition}_a{alpha:g}';signature=dict(seed=a.seed,condition=condition,alpha=alpha,vector_sha256=sha(vp),worker_sha256=sha(Path(__file__)),common_sha256=sha(B/'src/gen/common.py'),addendum3_sha256=sha(add),model_snapshot='0e9e39f249a16976918f6564b8830bc894c89659',refusal_fn_sha256=sha(B/'src/judge/refusal.py'),val_prompts_sha256=sha(B/'results/audit/handoff_round9/val70_generation_prompts.json'),legal_manifest_sha256=sha(B/'data/legal_val_items.json'),host=socket.gethostname(),physical_card=a.card)
 if a.phase=='grid':
  # seed3's predetermined repeatA already has validated generation; recompute if another host/card to keep cache attestation simple.
  single(D/(tag+'_val70.json'),[dict(id=k,prompt=p)for k,p in val.items()],v,dict(**signature,max_new_tokens=2400,baseline_file=f'results/style_retrained/eval_s{a.seed}/control_a1_val70.json'),2400,'val70')
  lp=D/(tag+'_legal400.json');d=open_cache(lp,dict(**signature,max_new_tokens=120,batch_size=8,baseline_file='results/audit/LEGALVALB_none.json'));tok.padding_side='left';tok.pad_token=tok.eos_token;scope['vec']=v;begin=time.monotonic();initial=len(d['items'])
  for offset in range(0,400,8):
   check_deadline()
   batch=legal[offset:offset+8];keys=[r['key']for r in batch];present=[k in d['items']for k in keys];assert all(present)or not any(present),'partial batch cache cannot change batch composition'
   if all(present):continue
   prepared=[(offset+i,r['group'],r['prompt'])for i,r in enumerate(batch)];texts=scope['run_batch'](prepared)
   for r,t in zip(batch,texts):d['items'][r['key']]=dict(text=t,alpha=alpha)
   atomic(lp,d);pulse('legal400',n=len(d['items']),total=400,condition=condition,alpha=alpha,seconds_per_item=(time.monotonic()-begin)/max(1,len(d['items'])-initial))
  assert len(d['items'])==400;tok.padding_side='right'
 else:
  single(D/(tag+'_wjb300.json'),[dict(id=r['id'],prompt=r['adversarial'])for r in harm],v,dict(**signature,manifest_sha256=sha(B/'configs/stage0_data/wjb300.json'),max_new_tokens=2400,baseline_file=f'results/style_retrained/eval_s{a.seed}/control_a1_wjb300.json'),2400,'wjb300')
  rows=[dict(id=r['id']+'|'+side,prompt=r[side])for r in pairs for side in ['vanilla','adversarial']]
  single(D/(tag+'_pairs600.json'),rows,v,dict(**signature,manifest_sha256=sha(B/'configs/stage0_data/wjb_benign246_pairs300.json'),max_new_tokens=120,baseline_file='results/audit/WJB_BENIGN246_alpha0.json'),120,'pairs600')
pulse('complete',phase_completed=a.phase);print('GENERATION_COMPLETE',a.phase,a.seed,flush=True)
