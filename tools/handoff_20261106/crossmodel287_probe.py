"""Resumable native norm/donor/target preflight; no optimization or test read."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, socket, subprocess, sys, time
import numpy as np
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
from crossmodel287_assets_and_render import model_path, render, digest

R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287'
sys.path.insert(0,str(R/'src'))
from judge.refusal import new_rule
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):
 q=p.with_name(p.name+'.'+str(os.getpid())+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');os.replace(q,p)
def must_yield(started):
 if time.monotonic()-started>450:return True
 if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc):return True
 p=R/'results/audit/pair500/lease_priority/controller_live.json'
 if p.exists():
  for row in load(p).get('jobs',{}).values():
   if '0'in row.get('cards',[])and row['kind']in ['prefix','hb']:return True
 return (R/'results/audit/pair500/lease_priority/request_gpu0.json').exists()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('model',choices=['qwen','gemma']);ap.add_argument('--targets',action='store_true');a=ap.parse_args()
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='0'and os.environ.get('DEVICE')=='cuda:0'
 protocol=load(O/'protocol_effective_addendum1.json');spec=protocol['models'][a.model]
 asset=O/(a.model+'_asset_render_receipt.json');assert load(asset)['phase']=='verified'
 path=model_path(a.model);directory=O/(a.model+'_private');directory.mkdir(exist_ok=True)
 public=O/(a.model+'_preflight.json');state=load(public)if public.exists()else {'model':a.model,'norm_rows':{},'targets_completed':{},'created_utc':utc()}
 live=O/(a.model+'_preflight_live.json');start=time.monotonic()
 def pulse(phase,**kw):save(live,{'utc':utc(),'pid':os.getpid(),'host':socket.gethostname(),'physical_gpu':0,'phase':phase,'effects_read':False,**kw})
 if must_yield(start):pulse('yield_before_model_load');return
 execution={'utc':utc(),'host':socket.gethostname(),'physical_gpu':0,
            'device_uuid':subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader','-i','0'],text=True).strip(),
            'torch':torch.__version__,
            'transformers':transformers.__version__,'cuda_runtime':torch.version.cuda,'dtype':'bfloat16',
            'protocol_sha256':sha(O/'protocol_effective_addendum1.json'),'asset_receipt_sha256':sha(asset),
            'worker_sha256':sha(Path(__file__)),'render_adapter_sha256':sha(R/'tools/handoff_20261106/crossmodel287_assets_and_render.py'),
            'stage':'norm_and_donor_target_preparation_only_no_training','injection_block':spec['injection_block_zero_based'],
            'donor_block':spec['donor_block_zero_based'],'native_block_output':True}
 receipt=directory/('execution_'+str(os.getpid())+'.json');save(receipt,execution)
 with(R/'docs/PREREG_LOG.txt').open('a')as f:f.write(utc()+' CROSSMODEL287_PREFLIGHT_BEFORE_GPU model='+a.model+' manifest_SHA='+sha(receipt)+' no optimization/test effects.\n')
 pulse('loading_native_model')
 tok=AutoTokenizer.from_pretrained(str(path),local_files_only=True)
 mdl=AutoModelForCausalLM.from_pretrained(str(path),local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'}).eval()
 for p in mdl.parameters():p.requires_grad_(False)
 mdl.config.use_cache=False
 layers=mdl.model.layers;assert len(layers)==spec['layers']
 source=load(R/'results/style_intervention/old_recipe_targets.json')
 def ids(text):return torch.tensor([render(tok,a.model,text)],dtype=torch.long,device='cuda:0')
 def block_value(output):return output[0]if isinstance(output,tuple)else output
 def capture(text,layer):
  data=[]
  def hook(module,args,output):data.append(block_value(output)[0,-1].detach().float().cpu())
  h=layers[layer].register_forward_hook(hook)
  try:
   with torch.inference_mode():mdl(input_ids=ids(text),use_cache=False)
  finally:h.remove()
  assert len(data)==1
  return data[0]
 for row in source['keep']:
  key=row['id']
  if key not in state['norm_rows']:
   value=capture(row['text'],spec['injection_block_zero_based'])
   state['norm_rows'][key]={'norm_l2_float32':float(value.norm()),'input_ids_sha256':digest(render(tok,a.model,row['text']))}
   state.update(utc=utc(),phase='measuring_norm');save(public,state);pulse('measuring_norm',completed=len(state['norm_rows']),total=60)
  if must_yield(start):pulse('yield_at_saved_row',norm_rows=len(state['norm_rows']));return
 assert len(state['norm_rows'])==60
 state['rho']=float(np.median([x['norm_l2_float32']for x in state['norm_rows'].values()]))
 # Only the fixed original behavior is read from the old activation metadata.
 donor_file=directory/'native_donor.npy'
 if not donor_file.exists():
  cache=torch.load(R/'results/probes/llama31_8b_instruct/acts_attack2_h.pt',map_location='cpu',weights_only=False)
  row=next(x for x in cache['meta']if x['id'].replace('H_','')=='jbbh_0000')
  value=capture(row['text'],spec['donor_block_zero_based']);np.save(donor_file,value.numpy())
 state.update(utc=utc(),phase='norm_and_donor_complete',native_donor_sha256=sha(donor_file),
              donor_block=spec['donor_block_zero_based'],injection_block=spec['injection_block_zero_based'],
              asset_receipt_sha256=sha(asset),last_execution_manifest_sha256=sha(receipt))
 save(public,state);pulse('norm_and_donor_complete',rho=state['rho'],norm_rows=60)
 if not a.targets:return
 donor=torch.from_numpy(np.load(donor_file)).to(device='cuda:0',dtype=torch.bfloat16)
 def generate(text,replace=False,limit=200):
  inputs=ids(text);seen=[0]
  def hook(module,args,output):
   if seen[0]:return output
   seen[0]+=1
   if not replace:return output
   value=block_value(output).clone();value[0,-1]=donor
   return (value,)+output[1:]if isinstance(output,tuple)else value
  h=layers[spec['injection_block_zero_based']].register_forward_hook(hook)
  try:
   with torch.inference_mode():out=mdl.generate(inputs,max_new_tokens=limit,do_sample=False,use_cache=False,pad_token_id=tok.eos_token_id)
  finally:h.remove()
  gen=out[0,inputs.shape[1]:].tolist();text=tok.decode(gen,skip_special_tokens=True)
  return {'output':text,'new_tokens':len(gen),'eos':bool(gen and gen[-1]in ([tok.eos_token_id]if isinstance(tok.eos_token_id,int)else tok.eos_token_id)),
          'prefill_hook_count':seen[0],'donor_replacement_count':int(replace),'v2_refusal':bool(new_rule(text)),
          'input_ids_sha256':digest(inputs[0].tolist()),'output_sha256':hashlib.sha256(text.encode()).hexdigest()}
 for group,rows,replace,limit in [('fit_alpha0',source['fit'],False,512),('fit_donor',source['fit'],True,200),('keep_alpha0',source['keep'],False,200)]:
  folder=directory/group;folder.mkdir(exist_ok=True)
  for row in rows:
   if must_yield(start):pulse('yield_at_saved_row',group=group);return
   file=folder/(row['id']+'.json')
   if not file.exists():save(file,{'id':row['id'],'utc':utc(),**generate(row['text'],replace,limit)})
   state['targets_completed'][group]=len(list(folder.glob('*.json')));save(public,state);pulse('target_preparation',group=group,completed=state['targets_completed'][group],total=len(rows))
 state.update(utc=utc(),phase='targets_complete_no_training',v2_refusals={g:sum(load(p)['v2_refusal']for p in(directory/g).glob('*.json'))for g in ['fit_alpha0','fit_donor','keep_alpha0']})
 save(public,state);pulse('targets_complete_no_training')

if __name__=='__main__':main()
