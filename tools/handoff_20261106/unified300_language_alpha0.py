"""S3a alpha0-only fixed-family generation; gates and caches, no judge/effect reads."""
from pathlib import Path
import json,hashlib,datetime,os,sys,time,inspect,threading
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';sys.path.insert(0,str(R/'tools/handoff_20261106'))
from batched_injection300 import generate_batch_with_injection,ids_sha

def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
key,physical=sys.argv[1],int(sys.argv[2]);plan=load(U/'language_alpha0_execution_plan.json');active=load(U/'active_protocol.json');assert active['S1a_frozen']and active['language_alpha0_execution_plan_sha256']==sha(U/'language_alpha0_execution_plan.json');assert active['allowed_main_conditions']==['alpha0'];assert sha(__file__)==plan['worker_sha256'];assert os.environ['CUDA_VISIBLE_DEVICES']==str(physical);assert sha(R/'tools/handoff_20261106/batched_injection300.py')==plan['batch_core_sha256'];assert sha(U/'language_alpha0_inputs.private.json')==plan['private_input_sha256']
spec=plan['models'][key];assert all(f in active['allowed_main_families']for f in plan['family_order']);assert spec['physical_gpu']==physical
for name,h in spec['asset_interface_sha256'].items():assert sha(Path(spec['model_path'])/name)==h
data=load(U/'language_alpha0_inputs.private.json')[key];dest=U/'language_alpha0'/key

live_lock=threading.Lock();live_state={}
def pulse(phase,**kw):
 with live_lock:
  live_state.clear();live_state.update(dict(utc=utc(),progress_utc=utc(),pid=os.getpid(),physical_gpu=physical,phase=phase,main_labels_or_effects_read=False,**kw));save(dest/'live.json',live_state)
def heartbeat():
 while True:
  time.sleep(10)
  with live_lock:
   if live_state:live_state['utc']=utc();save(dest/'live.json',live_state)
threading.Thread(target=heartbeat,daemon=True).start()
pulse('loading');tick=time.monotonic();tok=AutoTokenizer.from_pretrained(spec['model_path'],local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(spec['model_path'],local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval();save(dest/'load_receipt.json',dict(utc=utc(),seconds=time.monotonic()-tick,device_uuid=str(torch.cuda.get_device_properties(0).uuid)));dim=model.config.hidden_size;zero=np.zeros(dim,dtype=np.float32)
assert sha(spec['position_check_vector_path'])==spec['position_check_vector_sha256'];position_vector=np.load(spec['position_check_vector_path']);assert len(position_vector)==dim

def raw_batch(rows):
 enc=tok.pad({'input_ids':[r['input_ids']for r in rows]},padding=True,return_tensors='pt').to('cuda:0');width=enc.input_ids.shape[1]
 with torch.inference_mode():z=model.generate(**enc,max_new_tokens=2400,do_sample=False,pad_token_id=tok.pad_token_id)
 eos=model.generation_config.eos_token_id;eos={eos}if isinstance(eos,int)else set(eos or[]);out=[]
 for i in range(len(rows)):
  tail=z[i,width:].tolist();cut=next((j+1 for j,t in enumerate(tail)if t in eos),len(tail));out.append(tok.decode(tail[:cut],skip_special_tokens=True))
 return out

def position_check(rows):
 enc=tok.pad({'input_ids':[r['input_ids']for r in rows]},padding=True,return_tensors='pt').to('cuda:0');width=enc.input_ids.shape[1];positions=[width-len(r['input_ids'])+r['position']for r in rows];observed={}
 def hook(mod,args,output):
  h=output[0]if isinstance(output,tuple)else output;z=h.clone();rr=torch.arange(len(rows),device=h.device);pp=torch.tensor(positions,device=h.device);z[rr,pp]=z[rr,pp]+torch.as_tensor(position_vector,dtype=h.dtype,device=h.device);changed=(z!=h).any(-1);observed['changed_positions']=[torch.where(changed[i])[0].tolist()for i in range(len(rows))];observed['rho']=(z[rr,pp]-h[rr,pp]).float().norm(dim=-1).tolist();observed['count']=observed.get('count',0)+1;return(z,)+output[1:]if isinstance(output,tuple)else z
 hd=model.model.layers[spec['layer']].register_forward_hook(hook);kwargs=dict(**enc,position_ids=enc.attention_mask.long().cumsum(-1).sub(1).masked_fill(enc.attention_mask==0,1),use_cache=True)
 if 'logits_to_keep'in inspect.signature(model.forward).parameters:kwargs['logits_to_keep']=1
 elif 'num_logits_to_keep'in inspect.signature(model.forward).parameters:kwargs['num_logits_to_keep']=1
 try:
  with torch.inference_mode():model(**kwargs)
 finally:hd.remove()
 assert observed['count']==1 and all(x==[p]for x,p in zip(observed['changed_positions'],positions));assert all(x>0 for x in observed['rho'])
 return[dict(id=r['id'],position=r['position'],padded_position=p,changed_only_expected_position=x==[p],rho_runtime=n,injection_count=1)for r,p,x,n in zip(rows,positions,observed['changed_positions'],observed['rho'])]

def candidate(rows):
 torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();tick=time.monotonic();records=generate_batch_with_injection(model,tok,[r['input_ids']for r in rows],zero,layer=spec['layer'],max_new_tokens=2400,positions=[r['position']for r in rows],source_vector_sha256=None,alpha=0);torch.cuda.synchronize();elapsed=time.monotonic()-tick;free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();headroom=total-outside-torch.cuda.max_memory_reserved();assert all(r['injection_count']==1 and r['rho_runtime']==0 for r in records)
 return records,dict(utc=utc(),rows=len(rows),elapsed_seconds=elapsed,peak_reserved_bytes=torch.cuda.max_memory_reserved(),headroom_bytes=headroom)

for family in plan['family_order']:
 folder=dest/family;cfg=spec['families'][family];rows={str(r['id']):r for r in data[family]};batches=cfg['batches'];ordered=cfg['ordered_IDs'];assert len(rows)==440 and [k for b in batches for k in b]==ordered
 for k,r in rows.items():assert ids_sha(r['input_ids'])==r['input_ids_sha256'];assert r['position']<len(r['input_ids']);assert r['id']==int(k)
 if (folder/'generation_complete.json').exists():assert load(folder/'generation_complete.json')['execution_plan_sha256']==sha(U/'language_alpha0_execution_plan.json');continue
 tick_family=time.monotonic()
 try:
  if not (folder/'zero20_gate.json').exists():
   selected=set(ordered[:20]);comparisons=[];position_rows=[]
   for index,members in enumerate(batches):
    if not selected.intersection(members):continue
    group=[rows[k]for k in members];pulse('zero20_gate',family=family,covered_rows=len(comparisons),selected20=20)
    if family.startswith('prefix_'):position_rows+=position_check(group)
    reference=raw_batch(group);records,metric=candidate(group);assert metric['headroom_bytes']>=3*1024**3,'Gate memory below3GiB'
    for r,text,z in zip(group,reference,records):
     comparisons.append(dict(id=r['id'],selected=r['id']in{int(x)for x in selected},byte_equal=text==z['text'],reference_sha256=hashlib.sha256(text.encode()).hexdigest(),patched_sha256=hashlib.sha256(z['text'].encode()).hexdigest()));save(folder/'gate.private'/f'{r["id"]:04d}.json',dict(reference_text=text,patched_record=z))
    save(folder/'gate_metrics'/f'{index:04d}.json',metric)
   if position_rows:save(folder/'position20_gate.json',dict(utc=utc(),passed=all(r['changed_only_expected_position']for r in position_rows),selected20_passed=sum(r['id']in{int(x)for x in selected}for r in position_rows),rows=position_rows,only_prefill_metadata_no_decoded_nonzero_reply=True))
   passed=all(x['byte_equal']for x in comparisons)and sum(x['selected']for x in comparisons)==20;save(folder/'zero20_gate.json',dict(utc=utc(),passed=passed,selected20_exact=sum(x['selected']and x['byte_equal']for x in comparisons),covered=len(comparisons),batch_size=spec['batch_size'],same_batch_membership=True,pairs=comparisons,execution_plan_sha256=sha(U/'language_alpha0_execution_plan.json')))
   if not passed:raise RuntimeError('Zero20 byte gate failed; no full family admission')
  gate=load(folder/'zero20_gate.json');assert gate['passed']and gate['execution_plan_sha256']==sha(U/'language_alpha0_execution_plan.json')
  if family.startswith('prefix_'):assert load(folder/'position20_gate.json')['passed']
  for index,members in enumerate(batches):
   group=[rows[k]for k in members];paths=[folder/'generation.private'/f'{r["id"]:04d}.json'for r in group]
   if all(p.exists()for p in paths):assert all(load(p)['signature']['execution_plan_sha256']==sha(U/'language_alpha0_execution_plan.json')for p in paths);continue
   pulse('generating_alpha0',family=family,rows_completed=sum(map(len,batches[:index])),total=440,gate_exact20=20)
   if all((folder/'gate.private'/f'{r["id"]:04d}.json').exists()for r in group):
    records=[load(folder/'gate.private'/f'{r["id"]:04d}.json')['patched_record']for r in group];metric=load(folder/'gate_metrics'/f'{index:04d}.json');origin='observed_gate_candidate_reused'
   else:records,metric=candidate(group);origin='post_gate_generation'
   for r,z,p in zip(group,records,paths):
    value=dict(id=r['id'],prompt_sha256=r['prompt_sha256'],behavior_sha256=r['behavior_sha256'],full_response_sha256=hashlib.sha256((r['prefill']+z['text']).encode()).hexdigest(),result=z,signature=dict(execution_plan_sha256=sha(U/'language_alpha0_execution_plan.json'),worker_sha256=sha(__file__),model=key,family=family,condition='alpha0',alpha=0,batch_ids=[int(x)for x in members],cap=2400,physical_gpu=physical,origin=origin),v2_input_component='continuation'if family.startswith('prefix_')else'full_response')
    if p.exists():assert load(p)==value,'Partial batch replay changed; preserve and stop'
    else:save(p,value)
   save(folder/'metrics'/f'{index:04d}.json',metric);assert metric['headroom_bytes']>=3*1024**3,'Family memory below3GiB'
  files={k:sha(folder/'generation.private'/f'{int(k):04d}.json')for k in ordered};metrics=[load(p)for p in(folder/'metrics').glob('*.json')];seconds=sum(x['elapsed_seconds']for x in metrics);assert sum(x['rows']for x in metrics)==440;save(folder/'generation_complete.json',dict(utc=utc(),N=440,model=key,family=family,condition='alpha0',execution_plan_sha256=sha(U/'language_alpha0_execution_plan.json'),record_sha256=files,generation_seconds_including_reused_candidates=seconds,effective_rows_per_hour=440*3600/seconds,family_wall_seconds_including_gate_overhead=time.monotonic()-tick_family,main_labels_or_effects_read=False));pulse('family_generation_complete_cache_only',family=family,N=440)
 except (RuntimeError,torch.cuda.OutOfMemoryError)as error:
  save(folder/'execution_blocked.json',dict(utc=utc(),model=key,family=family,error_type=type(error).__name__,reason=str(error)[:400],execution_plan_sha256=sha(U/'language_alpha0_execution_plan.json'),action='Preserve family; no smaller path or output reading without versioned gate'));torch.cuda.empty_cache();pulse('family_blocked_continue_independent_families',family=family,error_type=type(error).__name__)
save(dest/'queue_complete.json',dict(utc=utc(),complete_families=len(list(dest.glob('*/generation_complete.json'))),blocked_families=len(list(dest.glob('*/execution_blocked.json'))),planned=len(plan['family_order']),main_labels_or_effects_read=False));pulse('alpha0_queue_complete_cache_only')
