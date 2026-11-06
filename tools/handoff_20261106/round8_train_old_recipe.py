"""Old-trainer fidelity or single frozen style-data intervention; exact shared initialization."""
from pathlib import Path
import argparse,os,sys,json,hashlib,datetime,time
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round8';T=B/'results/style_intervention'
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['fidelity','intervention'],required=True);p.add_argument('--seed',type=int,choices=range(3,8),required=True);p.add_argument('--physical-card',type=int,choices=[2,3],required=True);a=p.parse_args();assert os.environ.get('CUDA_VISIBLE_DEVICES')==str(a.physical_card)and os.environ.get('DEVICE')=='cuda:0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(p,d):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');q.replace(p)
D=T/(('fidelity'if a.mode=='fidelity'else'treatment')+f'_s{a.seed}');D.mkdir(exist_ok=True);live=O/f'train_{a.mode}_s{a.seed}_live.json'
def pulse(phase,**kw):atomic(live,dict(utc=now(),pid=os.getpid(),seed=a.seed,mode=a.mode,physical_gpu=a.physical_card,phase=phase,**kw))
old=json.loads((T/'old_recipe_targets.json').read_text());init=old['initials'][str(a.seed)];assert sha(B/init['file'])==init['npy_sha256'];source=B/'stage136/keep60_seed.py';assert sha(source)==old['old_recipe_sha256']
if a.mode=='intervention':
 gate=json.loads((T/'fidelity_gate.json').read_text());assert gate['passed'],'no intervention before fidelity gate'
 data=json.loads((T/'style_training_targets.json').read_text());assert data['n_groups']==60 and data['audit_sha256']==sha(O/'style_data_audit.json')and data['addendum1_sha256']==sha(B/'docs/252_ADDENDUM1_MEAN_CRITERION.md')
 assert json.loads((O/'style_audit_window_validation.json').read_text())['no_embedding_input_truncated']
text=source.read_text();prefix=text[:text.index('ref_targets=[gen(')].replace('map_location="cpu")','map_location="cpu",weights_only=False)').replace('"meta-llama/Llama-3.1-8B-Instruct", revision=REV','"/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659", local_files_only=True')
assert hashlib.sha256(prefix.encode()).hexdigest()==old['old_prefix_sha256'];sys.argv=[str(source),str(a.seed)];pulse('loading_model');ns={};exec(compile(prefix,str(source),'exec'),ns)
import ast
render_fn=next(z for z in ast.parse(text).body if isinstance(z,ast.FunctionDef)and z.name=='render')
exec(compile(ast.Module(body=[render_fn],type_ignores=[]),str(source)+'#original_render','exec'),ns)
assert[(r['id'],r['text'])for r in ns['keep']]==[(r['id'],r['text'])for r in old['keep']];assert[(r['id'],r['text'])for r in ns['train_rows']]==[(r['id'],r['text'])for r in old['fit']]
ns['ref_targets']=old['ref_targets'];ns['keep_targets']=old['keep_targets'];ns['keep_weights']=[.075]*60
if a.mode=='intervention':
 ns['keep_weights']=[.0375]*60
 for r in data['items']:
  for side in['vanilla','adversarial']:ns['keep'].append(dict(id=r['id']+'|'+side,text=r[side]));ns['keep_targets'].append(r['targets'][side]);ns['keep_weights'].append(.01875)
assert abs(sum(ns['keep_weights'])-4.5)<1e-10
signature=dict(mode=a.mode,seed=a.seed,old_targets_sha256=sha(T/'old_recipe_targets.json'),style_targets_sha256=sha(T/'style_training_targets.json')if a.mode=='intervention'else None,init_sha256=init['npy_sha256'],old_trainer_sha256=sha(source),worker_sha256=sha(Path(__file__)),addendum1_sha256=sha(B/'docs/252_ADDENDUM1_MEAN_CRITERION.md'))
(D/'input_signature.json').write_text(json.dumps(signature,indent=2)+'\n')
block=text[text.index('torch.manual_seed(SEED)'):text.index('\nv=(NORM*theta.detach()')]
initial='theta=torch.randn(4096,device=os.environ.get("DEVICE","cuda:3")); theta=(theta/theta.norm()*NORM).requires_grad_(True)';assert initial in block
block=block.replace(initial,"theta=torch.tensor(np.load(INIT_FILE),device=os.environ.get('DEVICE','cuda:0'),dtype=torch.float32).requires_grad_(True)")
block=block.replace('for k,tgt in zip(keep,keep_targets):','for k,tgt,wpt in zip(keep,keep_targets,keep_weights):').replace('(WPT*l2).backward()','(wpt*l2).backward()')
# Resume changes neither data nor RNG-dependent operations; checkpoint signature must match exactly.
needle='for step in range(STEPS):\n    opt.zero_grad()';replacement="""START_STEP=0
if CHECKPOINT.exists():
    saved=torch.load(CHECKPOINT,map_location=os.environ.get('DEVICE','cuda:0'),weights_only=False)
    assert saved['signature']==SIGNATURE
    with torch.no_grad():theta.copy_(saved['theta'])
    opt.load_state_dict(saved['optimizer']);START_STEP=saved['next_step']
for step in range(STEPS):
    if step<START_STEP:continue
    opt.zero_grad()""";assert needle in block;block=block.replace(needle,replacement)
block=block.replace('    opt.step()','    opt.step()\n    CHECKPOINT_CALLBACK(step+1,theta,opt)')
start=time.monotonic()
def checkpoint(step,theta,opt):
 q=D/'optimizer.pt.tmp';ns['torch'].save(dict(theta=theta.detach(),optimizer=opt.state_dict(),next_step=step,signature=signature),q);q.replace(D/'optimizer.pt');pulse('training',step=step,total_steps=40,elapsed_seconds=time.monotonic()-start,seconds_per_step=(time.monotonic()-start)/step);print(a.mode,a.seed,'STEP',step,'/40',flush=True)
ns.update(INIT_FILE=str(B/init['file']),CHECKPOINT=D/'optimizer.pt',SIGNATURE=signature,CHECKPOINT_CALLBACK=checkpoint);exec(compile(block,str(source)+'#frozen-weighted-loop','exec'),ns)
v=(ns['NORM']*ns['theta'].detach()/ns['theta'].detach().norm()).cpu().numpy();tmp=D/'v.npy.tmp'
with tmp.open('wb')as f:ns['np'].save(f,v)
tmp.replace(D/'v.npy');meta=dict(**signature,steps=40,vector_sha256=sha(D/'v.npy'),vector_norm=float(ns['np'].linalg.norm(v)),keep_weight_sum=sum(ns['keep_weights']),n_keep=len(ns['keep']),completed_utc=now())
if a.mode=='fidelity':
 ref=ns['np'].load(B/f'results/audit/runs/block10_keep60_s{a.seed}/v.npy');meta['cosine_to_frozen_old']=float(v@ref/(ns['np'].linalg.norm(v)*ns['np'].linalg.norm(ref)));assert meta['cosine_to_frozen_old']>.999,'old trainer reconstruction failed; stop before intervention'
atomic(D/'metadata.json',meta);pulse('vector_complete',step=40,vector_sha256=meta['vector_sha256'],seconds_per_step=(time.monotonic()-start)/40)
if a.mode=='fidelity':
 # Match the existing val70 generation path: enable KV cache after the old training loop.
 ns['mdl'].config.use_cache=True;sys.path.insert(0,str(B/'src'));from gen.common import generate_with_injection
 val={}
 for name in ['STAGE0_VAL_PAIR.json','STAGE0_VAL_HB_PAIR.json','STAGE0_VAL_HB_PAIR2.json','STAGE0_VAL_HB_PAIR3.json']:
  for r in json.loads((B/'results/audit'/name).read_text()):
   if r['result'].get('success'):val[r['behavior_id']]=r['result']['best_prompt']
 keys=json.loads((B/'configs/stage0_data/val70_ids.json').read_text())['ids'];out={};vv=v/ns['np'].linalg.norm(v)*5.21;begin=time.monotonic()
 for k in keys:
  ids=ns['tok'].apply_chat_template([{'role':'user','content':val[k]}],add_generation_prompt=True,return_tensors='pt').to('cuda:0');z=generate_with_injection(ns['mdl'],ns['tok'],ids,vv,layer=9,max_new_tokens=2400,device='cuda:0');out[k]=z;atomic(D/'val70.json',out);pulse('fidelity_val70_generation',n=len(out),total=70,seconds_per_item=(time.monotonic()-begin)/len(out))
 pulse('complete_waiting_judge',n=70,vector_cosine=meta['cosine_to_frozen_old'])
else:pulse('complete',step=40,vector_sha256=meta['vector_sha256'])
print('TRAINING_COMPLETE',a.mode,a.seed,flush=True)
