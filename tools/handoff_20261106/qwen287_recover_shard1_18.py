from pathlib import Path
import datetime,hashlib,json,os,sys,socket,subprocess
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/home/dell/Def');C=R/'results/audit/crossmodel287';O=C/'node_recovery18';D=C/'qwen_selection';sys.path.insert(0,str(R/'src'));from gen.common import generate_with_injection
sys.path.insert(0,str(R/'tools/handoff_20261106'));from crossmodel287_assets_and_render import render,digest
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def main():
 assert os.environ['CUDA_VISIBLE_DEVICES']=='2';route=load(O/'recovery_plan.json');assert sha(Path(__file__))==route['recovery_worker_sha256'];assert sha(D/'plan.json')==route['original_plan_sha256'];plan=load(D/'plan.json');assert sha(R/'src/gen/common.py')==plan['core_sha256'];assert sha(R/'tools/handoff_20261106/crossmodel287_assets_and_render.py')==plan['renderer_sha256']
 for name in['alpha0','s3_a1']:
  g=load(O/(name+'_gate20.json'));assert g['passed']and g['plan_sha256']==route['generation_gate_plan_sha256']
 claim=load(O/'adoption_manifest.json');assert claim['producer_failed']and claim['route_sha256']==sha(O/'recovery_plan.json');assert sha(C/'native_selection_inputs.private.json')==plan['inputs_sha256'];inputs=load(C/'native_selection_inputs.private.json')
 tok=AutoTokenizer.from_pretrained(route['target'],local_files_only=True);tok.padding_side='left';mdl=AutoModelForCausalLM.from_pretrained(route['target'],local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'}).eval();mdl.config.use_cache=True
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
 uuid=subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader','-i','2'],text=True).strip()
 def cached(p,row,sig):
  x=load(p);rel=str(p.relative_to(R));assert x['prompt_sha256']==row['prompt_sha256']
  if rel in claim['files']:assert sha(p)==claim['files'][rel]
  else:assert x['signature']==sig
  return x
 for seed in[3,4,5]:
  vp=C/f'qwen_vec_s{seed}/v.npy';assert sha(vp)==plan['vector_sha256'][str(seed)];v=np.load(vp)
  for alpha in plan['alpha_grid']:
   name=f's{seed}_a{alpha:g}';folder=D/'generation.private'/name;sig={'plan_sha256':sha(D/'plan.json'),'vector_file_sha256':sha(vp),'alpha':alpha,'host':socket.gethostname(),'device_uuid':uuid,'recovery_route_sha256':sha(O/'recovery_plan.json')};vec=v*alpha;allpaths=[]
   for i in range(0,400,8):
    if(i//8)%2!=1:continue
    group=inputs['legal400'][i:i+8];paths=[folder/'legal400'/(r['id']+'.json')for r in group];allpaths+=paths
    if all(p.exists()for p in paths):
     for row,p in zip(group,paths):cached(p,row,sig)
     continue
    for row,z,p in zip(group,batch(group,vec),paths):
     if p.exists():assert cached(p,row,sig)['result']['text']==z['text'],'Partial originalbatch replay differs; stop without overwriting'
     else:save(p,{'id':row['id'],'prompt_sha256':row['prompt_sha256'],'signature':sig,'result':z})
     save(O/'recovery_worker_live.json',{'utc':utc(),'pid':os.getpid(),'condition':name,'last_id':row['id'],'no_effects_read':True})
   for i,row in enumerate(inputs['val70']):
    if i%2!=1:continue
    p=folder/'val70'/(row['id']+'.json');allpaths.append(p)
    if p.exists():cached(p,row,sig);continue
    save(p,{'id':row['id'],'prompt_sha256':row['prompt_sha256'],'signature':sig,'result':single(row,vec,alpha)});save(O/'recovery_worker_live.json',{'utc':utc(),'pid':os.getpid(),'condition':name,'last_id':row['id'],'no_effects_read':True})
   assert len(allpaths)==235;files={str(p.relative_to(R)):sha(p)for p in allpaths};save(O/'recovered_conditions'/(name+'.json'),{'utc':utc(),'condition':name,'plan_sha256':sha(D/'plan.json'),'route_sha256':sha(O/'recovery_plan.json'),'files':files,'n_legal':200,'n_val':35})
 save(O/'recovery_worker_complete.json',{'utc':utc(),'pid':os.getpid(),'shard':1,'no_effects_read':True})
if __name__=='__main__':main()
