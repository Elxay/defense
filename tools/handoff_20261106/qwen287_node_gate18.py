from pathlib import Path
import ast,datetime,hashlib,json,os,sys,socket
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/home/dell/Def');C=R/'results/audit/crossmodel287';O=C/'node_recovery18';sys.path.insert(0,str(R/'src'));from gen.common import generate_with_injection
sys.path.insert(0,str(R/'tools/handoff_20261106'));from crossmodel287_assets_and_render import render,digest
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def main():
 assert os.environ['CUDA_VISIBLE_DEVICES']=='2'
 plan=load(O/'gate_plan.json');assert sha(Path(__file__))==plan['worker_sha256'];assert sha(R/'src/gen/common.py')==plan['core_sha256'];assert sha(R/'tools/handoff_20261106/crossmodel287_assets_and_render.py')==plan['renderer_sha256']
 assert load(C/'qwen_node_assets17/complete.json')['all_required_match'];assert sha(O/'inputs.private.json')==plan['inputs_sha256']
 tok=AutoTokenizer.from_pretrained(plan['target'],local_files_only=True);tok.padding_side='left';mdl=AutoModelForCausalLM.from_pretrained(plan['target'],local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'}).eval();mdl.config.use_cache=True
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
 data=load(O/'inputs.private.json');results={};save(O/'gate_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'loaded','no_labels_read':True})
 for name,alpha in [('alpha0',0),('s3_a1',1)]:
  if alpha:
   p=R/plan['vector_file'];assert sha(p)==plan['vector_sha256'];v=np.load(p)
  else:v=np.zeros(3584,dtype=np.float32)
  rows=[]
  def accept(row,z):
   rows.append({'id':row['id'],'byte_equal':hashlib.sha256(z['text'].encode()).hexdigest()==data['expected'][name][row['id']]['text_sha256'],'injection_count':z['injection_count']});save(O/'gate_live.json',{'utc':utc(),'pid':os.getpid(),'condition':name,'completed':len(rows),'total':20,'no_labels_read':True})
  for group in [data['legal16'][:8],data['legal16'][8:]]:
   for row,z in zip(group,batch(group,v)):accept(row,z)
  for row in data['val4']:accept(row,single(row,v,alpha))
  assert len(rows)==20;result={'utc':utc(),'pid':os.getpid(),'condition':name,'pairs':rows,'passed':all(x['byte_equal']for x in rows),'plan_sha256':sha(O/'gate_plan.json'),'no_labels_read':True};save(O/(name+'_gate20.json'),result);results[name]=result['passed'];assert result['passed'],'Cross-node byte gate failed: no migration or relaxed gate'
 save(O/'generation_gates_complete.json',{'utc':utc(),'pid':os.getpid(),'passed':all(results.values()),'conditions':results,'no_labels_read':True});print('QWEN_NODE_GATES_PASS',flush=True)
if __name__=='__main__':main()
