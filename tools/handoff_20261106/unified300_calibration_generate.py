from pathlib import Path
import json,datetime,hashlib,os,sys,time,socket
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';sys.path.insert(0,str(R/'tools/handoff_20261106'))
from batched_injection300 import generate_batch_with_injection

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
key,physical=sys.argv[1],int(sys.argv[2]);plan=load(U/'S1a_manifest.json');active=load(U/'active_protocol.json');assert active['S1a_frozen']and active['S1a_manifest_sha256']==sha(U/'S1a_manifest.json');assert sha(__file__)==plan['code_sha256']['tools/handoff_20261106/unified300_calibration_generate.py'];assert os.environ['CUDA_VISIBLE_DEVICES']==str(physical)
for rel in ['tools/handoff_20261106/batched_injection300.py','src/gen/common.py']:assert sha(R/rel)==plan['code_sha256'][rel]
assert sha(U/'calibration700.private.json')==plan['calibration_sha256'];rows={r['id']:r for r in load(U/'calibration700.private.json')};spec=plan['models'][key];dest=U/'calibration_S1a'/key

def pulse(phase,**kw):save(dest/'live.json',dict(utc=utc(),pid=os.getpid(),physical_gpu=physical,phase=phase,calibration_effect_read=False,**kw))
pulse('loading');tok=AutoTokenizer.from_pretrained(spec['model_path'],local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(spec['model_path'],local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval();ids={k:tok.apply_chat_template([{'role':'user','content':rows[k]['prompt']}],add_generation_prompt=True)for k in spec['ordered_IDs']}
assert hashlib.sha256(json.dumps({k:ids[k]for k in spec['ordered_IDs']},sort_keys=True,separators=(',',':')).encode()).hexdigest()==spec['calibration_input_ids_map_sha256']
vectors={}
for seed,v in spec['learned_vectors'].items():assert sha(v['path'])==v['file_sha256'];vectors[seed]=np.load(v['path'])
zero=np.zeros_like(vectors['s3']);batches=spec['calibration_batches'];assert sum(map(len,batches))==700
for condition in plan['calibration_conditions']:
 name=condition['id'];alpha=float(condition['alpha']);seed=condition['seed'];src=None if seed is None else spec['learned_vectors'][seed]['file_sha256'];delta=zero if seed is None else(vectors[seed]*np.float32(alpha));folder=dest/name
 if (folder/'generation_complete.json').exists():assert load(folder/'generation_complete.json')['manifest_sha256']==sha(U/'S1a_manifest.json');continue
 for i,members in enumerate(batches):
  paths=[folder/'generation.private'/(k+'.json')for k in members]
  if all(p.exists()for p in paths):assert all(load(p)['signature']['manifest_sha256']==sha(U/'S1a_manifest.json')for p in paths);continue
  pulse('generating',condition=name,batch_index=i,batches=len(batches),condition_rows=sum(len(x)for x in batches[:i]),total700=700);torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();tick=time.monotonic()
  result=generate_batch_with_injection(model,tok,[ids[k]for k in members],delta,layer=spec['layer'],max_new_tokens=120,source_vector_sha256=src,alpha=alpha)
  assert all(r['injection_count']==1 and r['new_tokens']<=120 for r in result)
  if seed is None:assert all(r['rho_runtime']==0 for r in result)
  for k,value,p in zip(members,result,paths):
   record=dict(id=k,prompt_sha256=rows[k]['prompt_sha256'],result=value,signature=dict(manifest_sha256=sha(U/'S1a_manifest.json'),worker_sha256=sha(__file__),model=key,condition=name,alpha=alpha,seed=seed,batch_ids=members,cap=120,physical_gpu=physical,source_vector_sha256=src))
   if p.exists():assert load(p)==record,'Partial batch changed; preserve and stop'
   else:save(p,record)
  torch.cuda.synchronize();free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();headroom=total-outside-torch.cuda.max_memory_reserved();save(folder/'metrics'/f'{i:04d}.json',dict(utc=utc(),rows=len(result),seconds=time.monotonic()-tick,peak_reserved_bytes=torch.cuda.max_memory_reserved(),headroom_bytes=headroom))
  if headroom<3*1024**3:save(dest/'execution_failed.json',dict(utc=utc(),reason='memory headroom below frozen3GiB',condition=name,batch_index=i,headroom=headroom,action='Preserve entire grid; no automatic path change or partial alpha selection'));raise RuntimeError('Memory admission failed; no partial alpha selection')
 files={k:sha(folder/'generation.private'/(k+'.json'))for k in plan['calibration_IDs']};assert len(files)==700;save(folder/'generation_complete.json',dict(utc=utc(),model=key,condition=name,N=700,manifest_sha256=sha(U/'S1a_manifest.json'),record_sha256=files))
save(dest/'all_generation_complete.json',dict(utc=utc(),conditions=22,rows=15400,manifest_sha256=sha(U/'S1a_manifest.json'),calibration_effect_read=False));pulse('all_generation_complete_wait_scores')
