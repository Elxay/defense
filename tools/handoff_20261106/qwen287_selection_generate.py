"""Frozen seven-alpha grid, two row/batch shards, no outcome aggregation."""
from pathlib import Path
import datetime,hashlib,json,os,sys,time
import numpy as np,torch
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';D=C/'qwen_selection';sys.path.insert(0,str(R/'src'));from gen.common import generate_with_injection
sys.path.insert(0,str(R/'tools/handoff_20261106'));from crossmodel287_assets_and_render import model_path,render,digest
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 shard=int(sys.argv[1]);card=int(sys.argv[2]);assert shard in[0,1]and os.environ['CUDA_VISIBLE_DEVICES']==str(card)
 plan=load(D/'plan.json');assert sha(Path(__file__))==plan['worker_sha256'];assert sha(R/'src/gen/common.py')==plan['core_sha256'];assert sha(R/'tools/handoff_20261106/crossmodel287_assets_and_render.py')==plan['renderer_sha256'];inputs=load(C/'native_selection_inputs.private.json');assert sha(C/'native_selection_inputs.private.json')==plan['inputs_sha256']
 def pulse(phase,**kw):save(D/f'live_{shard}.json',{'utc':utc(),'pid':os.getpid(),'physical_gpu':card,'shard':shard,'phase':phase,'labels_read':False,**kw})
 pulse('loading');tok=AutoTokenizer.from_pretrained(str(model_path('qwen')),local_files_only=True);tok.padding_side='left';mdl=AutoModelForCausalLM.from_pretrained(str(model_path('qwen')),local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'}).eval();mdl.config.use_cache=True
 def batch(group,vec):
  rendered=[render(tok,'qwen',r['prompt'])for r in group];enc=tok.pad({'input_ids':rendered},padding=True,return_tensors='pt').to('cuda:0');width=enc.input_ids.shape[1];box={'count':0}
  def hook(module,args,out):
   if box['count']:return out
   h=out[0].clone();before=h[:,-1].clone();h[:,-1]+=torch.tensor(vec,dtype=h.dtype,device=h.device);box['norms']=(h[:,-1]-before).float().norm(dim=-1).tolist();box['count']+=1;return(h,)+out[1:]
  hd=mdl.model.layers[8].register_forward_hook(hook)
  try:
   with torch.inference_mode():out=mdl.generate(**enc,max_new_tokens=120,do_sample=False,pad_token_id=tok.pad_token_id)
  finally:hd.remove()
  assert box['count']==1;eos=mdl.generation_config.eos_token_id;eos={eos}if isinstance(eos,int)else set(eos);result=[]
  for i,row in enumerate(group):
   ids=out[i,width:].tolist();cut=next((j+1 for j,v in enumerate(ids)if v in eos),len(ids));ids=ids[:cut];result.append({'text':tok.decode(ids,skip_special_tokens=True),'new_tokens':len(ids),'eos':bool(ids and ids[-1]in eos),'injection_count':1,'rho_runtime':box['norms'][i],'batch_ids':[r['id']for r in group],'batch_width':width,'input_ids_sha256':digest(rendered[i])})
  return result
 def single(row,vec,alpha):
  ids=torch.tensor([render(tok,'qwen',row['prompt'])],device='cuda:0');capture={};original=mdl.generate
  def tracked(*args,**kw):
   out=original(*args,**kw);capture['last_id']=int(out[0,-1]);return out
  mdl.generate=tracked
  try:z=generate_with_injection(mdl,tok,ids,vec,layer=8,max_new_tokens=2400,device='cuda:0',alpha=alpha)
  finally:mdl.generate=original
  eos=mdl.generation_config.eos_token_id;eos={eos}if isinstance(eos,int)else set(eos);z['eos']=capture['last_id']in eos;z['last_token_id']=capture['last_id'];return z
 zero=np.zeros(3584,dtype=np.float32);gate=[]
 for i in [0,8]:
  group=inputs['legal400'][i:i+8]
  for row,z in zip(group,batch(group,zero)):gate.append({'id':row['id'],'equal':z['text']==load(C/'native_selection_private/qwen/legal400'/(row['id']+'.json'))['result']['text']})
  pulse('zero20_gate',completed=len(gate),total=20)
 for row in inputs['val70'][:4]:gate.append({'id':row['id'],'equal':single(row,zero,0)['text']==load(C/'native_selection_private/qwen/val70'/(row['id']+'.json'))['result']['text']});pulse('zero20_gate',completed=len(gate),total=20)
 save(D/f'zero20_gpu{card}.json',{'utc':utc(),'pairs':gate,'passed':all(x['equal']for x in gate),'plan_sha256':sha(D/'plan.json')});assert all(x['equal']for x in gate),'Zero20 failed; stop without changing baseline or gate'
 started=time.monotonic();done=0
 for seed in [3,4,5]:
  vector_file=C/f'qwen_vec_s{seed}/v.npy';assert sha(vector_file)==plan['vector_sha256'][str(seed)];v=np.load(vector_file)
  for alpha in plan['alpha_grid']:
   name=f's{seed}_a{alpha:g}';folder=D/'generation.private'/name;sig={'plan_sha256':sha(D/'plan.json'),'vector_file_sha256':sha(vector_file),'alpha':alpha,'host':os.uname().nodename,'device_uuid':subprocess_uuid(card)};vec=v*alpha
   for i in range(0,400,8):
    if(i//8)%2!=shard:continue
    group=inputs['legal400'][i:i+8];paths=[folder/'legal400'/(r['id']+'.json')for r in group]
    if all(p.exists()for p in paths):assert all(load(p)['signature']==sig for p in paths);continue
    for row,z,p in zip(group,batch(group,vec),paths):
     if p.exists():assert load(p)['signature']==sig and load(p)['result']['text']==z['text']
     else:save(p,{'id':row['id'],'prompt_sha256':row['prompt_sha256'],'signature':sig,'result':z})
     done+=1
    pulse('generating',condition=name,new_rows=done,seconds_per_new_row=(time.monotonic()-started)/max(1,done))
   for i,row in enumerate(inputs['val70']):
    if i%2!=shard:continue
    p=folder/'val70'/(row['id']+'.json')
    if p.exists():assert load(p)['signature']==sig;continue
    save(p,{'id':row['id'],'prompt_sha256':row['prompt_sha256'],'signature':sig,'result':single(row,vec,alpha)});done+=1;pulse('generating',condition=name,new_rows=done,seconds_per_new_row=(time.monotonic()-started)/max(1,done))
   save(D/'condition_done'/f'{name}_shard{shard}.json',{'utc':utc(),'plan_sha256':sha(D/'plan.json'),'n_legal':200,'n_val':35})
 pulse('all_grid_shard_complete',new_rows=done)
def subprocess_uuid(card):
 import subprocess
 return subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader','-i',str(card)],text=True).strip()
if __name__=='__main__':main()
