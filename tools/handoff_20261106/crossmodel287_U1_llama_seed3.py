"""Training-only Llama seed3 check with the immutable U1 target cache."""
from pathlib import Path
import ast,datetime,hashlib,json,os,sys,time
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';D=C/'U1_llama_seed3_check'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def pulse(phase,**kw):save(D/'live.json',{'utc':utc(),'pid':os.getpid(),'host':os.uname().nodename,'physical_gpu':2,'phase':phase,**kw})
def main():
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='2'and os.environ.get('DEVICE')=='cuda:0'
 plan=json.loads((D/'plan.json').read_text());assert plan['worker_sha256']==sha(Path(__file__))
 teacher=R/plan['teacher_file'];assert sha(teacher)==plan['teacher_sha256'];old=json.loads(teacher.read_text());source=R/'stage136/keep60_seed.py';assert sha(source)==old['old_recipe_sha256']==plan['old_trainer_sha256']
 init=old['initials']['3'];assert sha(R/init['file'])==init['npy_sha256']==plan['initialization_sha256'];ref=R/'results/audit/runs/block10_keep60_s3/v.npy';assert sha(ref)==plan['frozen_vector_sha256']
 assert not(D/'complete.json').exists(),'Completed check immutable'
 text=source.read_text();prefix=text[:text.index('ref_targets=[gen(')].replace('map_location="cpu")','map_location="cpu",weights_only=False)').replace('"meta-llama/Llama-3.1-8B-Instruct", revision=REV','"/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659", local_files_only=True')
 assert hashlib.sha256(prefix.encode()).hexdigest()==old['old_prefix_sha256']
 D.mkdir(exist_ok=True);pulse('loading_model',step=0,total_steps=40);sys.argv=[str(source),'3'];ns={};exec(compile(prefix,str(source),'exec'),ns)
 render_fn=next(z for z in ast.parse(text).body if isinstance(z,ast.FunctionDef)and z.name=='render');exec(compile(ast.Module(body=[render_fn],type_ignores=[]),str(source)+'#original_render','exec'),ns)
 assert [(r['id'],r['text'])for r in ns['keep']]==[(r['id'],r['text'])for r in old['keep']]
 assert [(r['id'],r['text'])for r in ns['train_rows']]==[(r['id'],r['text'])for r in old['fit']]
 ns['ref_targets']=old['ref_targets'];ns['keep_targets']=old['keep_targets']
 block=text[text.index('torch.manual_seed(SEED)'):text.index('\nv=(NORM*theta.detach()')]
 initial='theta=torch.randn(4096,device=os.environ.get("DEVICE","cuda:3")); theta=(theta/theta.norm()*NORM).requires_grad_(True)';assert initial in block
 block=block.replace(initial,"theta=torch.tensor(np.load(INIT_FILE),device=os.environ.get('DEVICE','cuda:0'),dtype=torch.float32).requires_grad_(True)")
 needle='for step in range(STEPS):\n    opt.zero_grad()';assert needle in block
 replacement='''START_STEP=0
if CHECKPOINT.exists():
    saved=torch.load(CHECKPOINT,map_location=os.environ.get('DEVICE','cuda:0'),weights_only=False)
    assert saved['plan_sha256']==PLAN_SHA
    with torch.no_grad():theta.copy_(saved['theta'])
    opt.load_state_dict(saved['optimizer']);START_STEP=saved['next_step']
    torch.set_rng_state(saved['cpu_rng'].cpu());torch.cuda.set_rng_state(saved['cuda_rng'].cpu())
for step in range(STEPS):
    if step<START_STEP:continue
    BEFORE_STEP(step)
    opt.zero_grad()'''
 block=block.replace(needle,replacement).replace('    opt.step()','    opt.step()\n    CHECKPOINT_CALLBACK(step+1,theta,opt)')
 started=time.monotonic();started_utc=utc()
 def before(step):
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(plan['allocation_deadline_utc']):
   pulse('paused_allocation_deadline',step=step,total_steps=40);raise SystemExit(0)
 def checkpoint(step,theta,opt):
  torch=ns['torch'];q=D/'optimizer.pt.tmp';torch.save({'theta':theta.detach(),'optimizer':opt.state_dict(),'next_step':step,'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state(),'plan_sha256':sha(D/'plan.json')},q);q.replace(D/'optimizer.pt');pulse('training',step=step,total_steps=40,elapsed_seconds=time.monotonic()-started,seconds_per_step=(time.monotonic()-started)/max(1,step));print('U1_LLAMA_S3_STEP',step,flush=True)
 ns.update(INIT_FILE=str(R/init['file']),CHECKPOINT=D/'optimizer.pt',PLAN_SHA=sha(D/'plan.json'),BEFORE_STEP=before,CHECKPOINT_CALLBACK=checkpoint);exec(compile(block,str(source)+'#fixed_U1_target_loop','exec'),ns)
 np=ns['np'];v=(ns['NORM']*ns['theta'].detach()/ns['theta'].detach().norm()).cpu().numpy();q=D/'v.npy.tmp'
 with q.open('wb')as f:np.save(f,v)
 q.replace(D/'v.npy');a=v.astype('float64');b=np.load(ref).astype('float64');cos=float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)));difference=float(np.linalg.norm(a-b))
 result={'utc':utc(),'training_started_utc':started_utc,'seed':3,'steps':40,'plan_sha256':sha(D/'plan.json'),'worker_sha256':sha(Path(__file__)),'teacher_sha256':sha(teacher),'vector_sha256':sha(D/'v.npy'),'frozen_vector_sha256':sha(ref),'cosine_float64':cos,'difference_l2':difference,'new_vector_norm':float(np.linalg.norm(a)),'reference_vector_norm':float(np.linalg.norm(b)),'elapsed_training_seconds':time.monotonic()-started,'suggested_0_999_closeness_cutoff_met':cos>=.999,'interpretation':'one fixed-cache retrain; closeness is not target-byte identity, statistical equivalence, or a variance decomposition','model_weights_updated':False,'val70_or_test_outputs_generated':False}
 save(D/'complete.json',result);pulse('complete',step=40,total_steps=40,cosine_float64=cos,elapsed_seconds=time.monotonic()-started)
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
