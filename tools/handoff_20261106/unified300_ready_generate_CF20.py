"""Queue worker: fixed membership HF generation, explicit gates/leases, no outcome reads."""
from pathlib import Path
import json,hashlib,datetime,os,sys,time,ast,threading,inspect
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T))
from batched_injection300 import generate_batch_with_injection,ids_sha
def L(p):return json.loads(Path(p).read_text())
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(o,indent=2)+'\n');q.replace(p)
key,family,condition,mode,physical=sys.argv[1:];physical=int(physical);site=os.environ['DEF_SITE'];lease=Path(os.environ['DEF_LEASE_DIR']);plan_path=U/'ready_generation_CF20.json';plan=L(plan_path);binding=L(U/'ready_worker_operational_binding_CF20.json');assert H(__file__)==binding['worker_sha256'] and H(plan_path) in binding['allowed_numerical_plan_sha256'];assert H(T/'batched_injection300.py')==plan['batch_core_sha256'];assert os.environ['CUDA_VISIBLE_DEVICES']==str(physical)
spec=plan['models'][key];cfg=spec['families'][family];assert cfg['home_site']==site;assert condition in plan['condition_order'][key];assert mode in ['gate','generate']
oldinput=U/cfg['input_file'];assert H(oldinput)==cfg['input_sha256'];data={str(r['id']):r for r in L(oldinput)[key][family]};batchlist=cfg['batches'];assert len(data)==440;folder=U/cfg['output_root']/key/family/condition
state={};lock=threading.Lock()
def pulse(phase,**x):
 with lock:state.clear();state.update(dict(utc=utc(),progress_utc=utc(),pid=os.getpid(),site=site,physical_gpu=physical,model=key,family=family,condition=condition,phase=phase,no_effect_reads=True,**x));save(lease/'live.json',state)
def heartbeat():
 while True:
  time.sleep(10)
  with lock:
   if state:state['utc']=utc();save(lease/'live.json',state)
threading.Thread(target=heartbeat,daemon=True).start();pulse('loading');mp=Path(spec['model_paths'][site])
for n,h in spec['asset_interface_sha256'].items():assert H(mp/n)==h,n
tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32);alpha=0.;vec=zero;src=None
if condition!='alpha0':
 v=spec['scaled_vectors'][condition];vp=R/v['path_relative'];assert H(vp)==v['file_sha256'];vec=np.load(vp);alpha=spec['selected_alpha'];src=v['source_vector_sha256'];assert abs(np.linalg.norm(vec.astype('float64'))-v['expected_norm'])<1e-4
 assert (cfg.get('SORRY_gate') in ['active','INVALID_crossing_continue']) or (cfg.get('SORRY_gate')=='external_after_alpha0' and L(R/cfg['external_SORRY_gate_relative'])['gate'] in ['active','INVALID_crossing_continue'])
# Parent raw_batch is extracted unchanged, including native generation/EOS handling.
source=T/'unified300_language_alpha0.py';assert H(source)==plan['raw_batch_source_sha256'];tree=ast.parse(source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='raw_batch');env=dict(tok=tok,model=model,torch=torch);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),env);raw_batch=env['raw_batch']
def candidate(rows,vector=vec,a=alpha,s=src):
 torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();tick=time.monotonic();out=generate_batch_with_injection(model,tok,[r['input_ids']for r in rows],vector,layer=spec['layer'],max_new_tokens=2400,positions=[r['position']for r in rows],source_vector_sha256=s,alpha=a);torch.cuda.synchronize();free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();head=total-outside-torch.cuda.max_memory_reserved();assert all(z['injection_count']==1 for z in out)
 return out,dict(utc=utc(),rows=len(rows),elapsed_seconds=time.monotonic()-tick,peak_reserved_bytes=torch.cuda.max_memory_reserved(),headroom_bytes=head,device_uuid=str(torch.cuda.get_device_properties(0).uuid))
try:
 gate=U/'ready_CF_family_gates20'/site/key/family/'zero20.json'
 if mode=='gate':
  assert condition=='alpha0';selected=set(cfg['ordered_IDs'][:20]);checks=[]
  for index,members in enumerate(batchlist):
   if not selected.intersection(members):continue
   rows=[data[k]for k in members];pulse('zero20_gate',covered=len(checks));ref=raw_batch(rows);out,metric=candidate(rows,zero,0,None)
   assert metric['headroom_bytes']>=3*1024**3,'gate memory below3GiB'
   for r,text,z in zip(rows,ref,out):
    checks.append(dict(id=r['id'],selected=str(r['id'])in selected,byte_equal=text==z['text']));save(gate.parent/'observed_candidates.private'/f"{r['id']:04d}.json",dict(result=z,metric=metric))
  passed=all(x['byte_equal']for x in checks);assert sum(x['selected']for x in checks)==20;save(gate,dict(utc=utc(),passed=passed,N_selected=20,selected_exact=sum(x['selected']and x['byte_equal']for x in checks),checks=checks,plan_sha256=H(plan_path)));assert passed,'byte gate failed';pulse('gate_complete');sys.exit(0)
 assert mode=='generate'
 if cfg.get('original_zero20_relative'):
  p=R/cfg['original_zero20_relative'];assert H(p)==cfg['original_zero20_sha256']and L(p)['passed']
 else:assert L(gate)['passed']and L(gate)['plan_sha256']==H(plan_path)
 for i,members in enumerate(batchlist):
  rows=[data[k]for k in members];paths=[folder/'generation.private'/f"{r['id']:04d}.json"for r in rows]
  if all(p.exists()for p in paths):assert all(L(p)['signature']['plan_sha256']==H(plan_path)for p in paths);continue
  if (lease/'yield.request').exists():save(lease/'yielded.json',dict(utc=utc(),before_batch=i,rows_completed=sum(len(b)for b in batchlist[:i])));pulse('yielded_at_batch_boundary');sys.exit(75)
  pulse('generating',rows_completed=sum(len(b)for b in batchlist[:i]),N=440)
  observed=[gate.parent/'observed_candidates.private'/f"{r['id']:04d}.json"for r in rows]
  if condition=='alpha0'and all(p.exists() and L(p)['result']['device_uuid']==str(torch.cuda.get_device_properties(0).uuid) for p in observed):
   vals=[L(p)for p in observed];out=[v['result']for v in vals];metric=vals[0]['metric'];assert all(z['device_uuid']==str(torch.cuda.get_device_properties(0).uuid)for z in out),'gate candidate device changed'
  else:out,metric=candidate(rows)
  for r,z,p in zip(rows,out,paths):
   expected_rho=float(np.linalg.norm(vec.astype('float64')));error=abs(z['rho_runtime']-expected_rho);relative_error=None if expected_rho==0 else error/expected_rho;z={**z,'rho_expected':expected_rho,'rho_relative_error':relative_error,'rho_relative_tolerance':.01,'nominal_relative_to_residual':0.9*alpha};save(lease/'norm_check_latest.json',dict(utc=utc(),id=r['id'],rho_runtime=z['rho_runtime'],rho_expected=expected_rho,relative_error=relative_error,passed=error<=1e-7 if expected_rho==0 else relative_error<=.01))
   value=dict(id=r['id'],prompt_sha256=r['prompt_sha256'],behavior_sha256=r['behavior_sha256'],full_response_sha256=hashlib.sha256((r['prefill']+z['text']).encode()).hexdigest(),result=z,signature=dict(plan_sha256=H(plan_path),model=key,family=family,condition=condition,alpha=alpha,source_vector_sha256=src,batch_ids=[int(k)for k in members],physical_gpu=physical,site=site,cap=2400,worker_sha256=H(__file__),operational_binding_sha256=H(U/'ready_worker_operational_binding_CF20.json')))
   if p.exists():assert L(p)==value,'partial batch changed; stop and preserve'
   else:save(p,value)
   assert error<=1e-7 if expected_rho==0 else relative_error<=.01,'runtime rho outside frozen tolerance; preserve record and stop'
  save(folder/'metrics'/f'{i:04d}.json',metric)
  assert metric['headroom_bytes']>=3*1024**3,'family memory below3GiB'
 files={str(r['id']):H(folder/'generation.private'/f"{r['id']:04d}.json")for r in data.values()};mets=[L(p)for p in(folder/'metrics').glob('*.json')];assert sum(x['rows']for x in mets)==440;seconds=sum(x['elapsed_seconds']for x in mets)
 save(folder/'complete.json',dict(utc=utc(),N=440,model=key,family=family,condition=condition,site=site,plan_sha256=H(plan_path),record_sha256=files,generation_seconds=seconds,rows_per_hour=440*3600/seconds));pulse('complete')
except Exception as e:
 save(lease/'failure.json',dict(utc=utc(),error_type=type(e).__name__,reason=str(e)[:500],action='retain files; no automatic batch fallback; independent queue tasks may proceed'));pulse('blocked',error_type=type(e).__name__);raise
