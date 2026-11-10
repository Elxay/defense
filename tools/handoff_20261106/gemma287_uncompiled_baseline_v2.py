"""Gemma alpha-zero selection outputs only, resumable at a row/original-batch boundary."""
from pathlib import Path
import datetime,hashlib,json,os,socket,subprocess,sys,time
import numpy as np
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
from crossmodel287_assets_and_render import model_path,render,digest
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287';sys.path.insert(0,str(R/'src'))
from gen.common import generate_with_injection
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(p.read_text())
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def main():
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='0'and os.environ.get('DEVICE')=='cuda:0'
 assert(R/'results/audit/pair500/lease_priority/PAIR_GPU_complete.json').exists()
 protocol=O/'takeover_20261110/effective_execution.json';cfg=load(protocol);assert cfg['target_source_branch']['decision']=='U1'
 implementation=load(O/'gemma_uncompiled_implementation.json');assert implementation['protocol_sha256']==sha(protocol)
 for filename,value in implementation['code_sha256'].items():assert sha(R/filename)==value,filename
 manifest=O/'transfer_and_native_selection_inputs_manifest.json';data=O/'native_selection_inputs.private.json';assert sha(data)==load(manifest)['native_selection_inputs_private_sha256']
 assert load(O/'gemma_asset_render_receipt.json')['phase']=='verified'and sha(O/'gemma_asset_render_receipt.json')==implementation['Gemma_asset_receipt_sha256'];inputs=load(data);folder=O/'native_selection_eager_uncompiled/gemma';folder.mkdir(parents=True,exist_ok=True);start=time.monotonic()
 def pulse(phase,**kw):save(O/'gemma_uncompiled_selection_live.json',{'utc':utc(),'pid':os.getpid(),'phase':phase,'physical_gpu':0,'host':socket.gethostname(),'training_started':False,**kw})
 def stop():
  return time.monotonic()-start>1800 or datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(implementation['lease_expiry_utc'])or(R/'results/audit/pair500/lease_priority/request_gpu0.json').exists()
 if stop():pulse('yield_before_load');return
 signature={'protocol_sha256':sha(protocol),'inputs_sha256':sha(data),'worker_sha256':sha(Path(__file__)),'renderer_sha256':sha(R/'tools/handoff_20261106/crossmodel287_assets_and_render.py'),'core_sha256':sha(R/'src/gen/common.py'),'model_revision':cfg['models']['gemma']['revision'],'alpha':0,'layer':12,'attention':'eager','disable_compile':True,'device_uuid':subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader','-i','0'],text=True).strip()}
 save(folder/('execution_'+str(os.getpid())+'.json'),{'utc':utc(),'signature':signature})
 tok=AutoTokenizer.from_pretrained(str(model_path('gemma')),local_files_only=True);tok.padding_side='left'
 if tok.pad_token_id is None:tok.pad_token_id=tok.eos_token_id
 mdl=AutoModelForCausalLM.from_pretrained(str(model_path('gemma')),local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='eager').eval();mdl.config.use_cache=True
 vector=np.zeros(cfg['models']['gemma']['hidden_size'],dtype=np.float32)
 assert mdl.config._attn_implementation=='eager'
 mdl.generation_config.disable_compile=True
 assert mdl.generation_config.disable_compile is True
 def forbid_auto_compile(*args,**kwargs):raise RuntimeError('Automatic compilation is forbidden in the explicit uncompiled path')
 mdl.get_compiled_call=forbid_auto_compile
 assert not hasattr(mdl.forward,'_torchdynamo_orig_callable')
 original_generate=mdl.generate;last_generated={}
 def tracked_generate(*args,**kw):
  result=original_generate(*args,**kw);last_generated['id']=int(result[0,-1]);return result
 mdl.generate=tracked_generate
 teacher=load(R/'results/style_intervention/old_recipe_targets.json');norm_path=O/'gemma_eager_norm.json'
 if not norm_path.exists():
  values=[]
  for row in teacher['keep']:
   seen=[]
   def capture(module,args,out):seen.append(out[0][0,-1].detach().float().cpu())
   handle=mdl.model.layers[12].register_forward_hook(capture)
   try:
    with torch.inference_mode():mdl(input_ids=torch.tensor([render(tok,'gemma',row['text'])],device='cuda:0'),use_cache=False)
   finally:handle.remove()
   assert len(seen)==1;values.append({'id':row['id'],'norm_l2_float32':float(seen[0].norm())})
  m=float(np.median([v['norm_l2_float32']for v in values]));save(norm_path,{'utc':utc(),'attention':'eager','block':12,'n':60,'median':m,'rho':0.9*m,'rows':values,'signature':signature})

 for i in range(0,len(inputs['legal400']),8):
  group=inputs['legal400'][i:i+8];paths=[folder/'legal400'/(r['id']+'.json')for r in group]
  if all(p.exists()for p in paths):
   assert all(load(p)['signature']==signature and load(p)['prompt_sha256']==r['prompt_sha256']for r,p in zip(group,paths));continue
  if stop():pulse('yield_at_batch_boundary');return
  rendered=[render(tok,'gemma',r['prompt'])for r in group];encoding=tok.pad({'input_ids':rendered},padding=True,return_tensors='pt').to('cuda:0');width=encoding.input_ids.shape[1];state={'count':0,'delta_norms':None}
  def hook(module,args,output):
   if state['count']:return output
   h=output[0].clone();before=h[:,-1].clone();h[:,-1]+=torch.zeros_like(before);state['delta_norms']=(h[:,-1]-before).float().norm(dim=-1).tolist();state['count']+=1;return(h,)+output[1:]
  handle=mdl.model.layers[12].register_forward_hook(hook)
  try:
   with torch.inference_mode():out=mdl.generate(**encoding,max_new_tokens=120,do_sample=False,pad_token_id=tok.pad_token_id)
  finally:handle.remove()
  assert state['count']==1 and all(v==0 for v in state['delta_norms'])
  eos=mdl.generation_config.eos_token_id;eos={eos}if isinstance(eos,int)else set(eos)
  for index,(row,p)in enumerate(zip(group,paths)):
   ids=out[index,width:].tolist();cut=next((j+1 for j,v in enumerate(ids)if v in eos),len(ids));ids=ids[:cut];text=tok.decode(ids,skip_special_tokens=True)
   result={'text':text,'new_tokens':len(ids),'eos':bool(ids and ids[-1]in eos),'injection_count':1,'injection_positions':[width-1],'rho_runtime':0.0,'alpha':0.0,'input_ids_sha256':digest(rendered[index]),'batch_ids':[r['id']for r in group],'batch_width':width}
   record={'id':row['id'],'signature':signature,'prompt_sha256':row['prompt_sha256'],'in_fixed388':row['in_fixed388'],'result':result,'utc':utc()}
   if p.exists():assert load(p)['signature']==signature and load(p)['result']['text']==text,'Partial-batch replay mismatch; preserve old rows'
   else:save(p,record)
  pulse('legal400_generation',completed=len(list((folder/'legal400').glob('*.json'))),total=400)
 for row in inputs['val70']:
  p=folder/'val70'/(row['id']+'.json')
  if p.exists():assert load(p)['signature']==signature and load(p)['prompt_sha256']==row['prompt_sha256'];continue
  if stop():pulse('yield_at_saved_row');return
  ids=torch.tensor([render(tok,'gemma',row['prompt'])],device='cuda:0');z=generate_with_injection(mdl,tok,ids,vector,layer=12,max_new_tokens=2400,device='cuda:0',alpha=0);assert z['injection_count']==1 and z['delta_norm_runtime']==0
  z['eos']=last_generated['id']in({mdl.generation_config.eos_token_id}if isinstance(mdl.generation_config.eos_token_id,int)else set(mdl.generation_config.eos_token_id));z['last_token_id']=last_generated['id'];save(p,{'id':row['id'],'signature':signature,'prompt_sha256':row['prompt_sha256'],'result':z,'utc':utc()});pulse('val70_generation',completed=len(list((folder/'val70').glob('*.json'))),total=70)
 save(O/'gemma_uncompiled_selection_complete.json',{'utc':utc(),'n_legal400':400,'n_legal_mask':388,'n_val70':70,'signature':signature,'no_refusal_audit_yet':True});pulse('complete_waiting_refusal_audit')
if __name__=='__main__':main()
