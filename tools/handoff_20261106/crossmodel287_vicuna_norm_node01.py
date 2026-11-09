"""Native Vicuna norm only on two gated node01 cards; no targets or training."""
from pathlib import Path
import datetime,hashlib,json,os,socket,subprocess,time
import numpy as np
import torch,transformers
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/home/dell/Def');D=R/'results/audit/crossmodel287/vicuna_norm_node01'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def main():
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='1,2'and os.environ.get('DEVICE')=='cuda:0'
 plan=json.loads((D/'plan.json').read_text());assert sha(Path(__file__))==plan['worker_sha256'];inputs=D/'keep60.private.json';assert sha(inputs)==plan['private_inputs_sha256'];rows=json.loads(inputs.read_text());assert len(rows)==60
 if(D/'complete.json').exists():return
 model=R/plan['model_relative_path'];checked={}
 for n,expected in plan['model_files_sha256'].items():assert sha(model/n)==expected,n;checked[n]=expected
 def pulse(phase,**kw):save(D/'live.json',{'utc':utc(),'pid':os.getpid(),'phase':phase,'physical_gpus':[1,2],'training_started':False,**kw})
 def expired():return datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(plan['allocation_deadline_utc'])
 if expired():pulse('paused_allocation_deadline_before_load');return
 tok=AutoTokenizer.from_pretrained(str(model),local_files_only=True);c=plan['fastchat_template'];rendered={}
 for row in rows:
  ids=tok(c['system_message']+c['sep']+c['roles'][0]+': '+row['text']+c['sep']+c['roles'][1]+':',add_special_tokens=True)['input_ids'];assert digest(ids)==row['input_ids_sha256'];assert len(ids)<=4096;rendered[row['id']]=ids
 execution={'utc':utc(),'plan_sha256':sha(D/'plan.json'),'worker_sha256':sha(Path(__file__)),'model_files_verified':checked,'render_checks':60,'torch':torch.__version__,'transformers':transformers.__version__,'cuda':torch.version.cuda,'dtype':'bfloat16','host':socket.gethostname(),'physical_gpus':[1,2],'device_uuids':subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader','-i','1,2'],text=True).splitlines(),'native_injection_block_output':12,'hidden_states_array_not_used':True,'no_training_or_generation':True}
 save(D/'execution.json',execution);pulse('loading_native_bf16_model')
 mdl=AutoModelForCausalLM.from_pretrained(str(model),local_files_only=True,torch_dtype=torch.bfloat16,device_map='auto',max_memory={0:'21GiB',1:'21GiB'}).eval()
 for p in mdl.parameters():p.requires_grad_(False)
 assert not any(str(v)in ['cpu','disk']for v in mdl.hf_device_map.values());assert len(mdl.model.layers)==40 and mdl.config.hidden_size==5120
 mdl.config.use_cache=False;folder=D/'rows';folder.mkdir(exist_ok=True);start=time.monotonic()
 for row in rows:
  p=folder/(row['id']+'.json')
  if p.exists():assert json.loads(p.read_text())['plan_sha256']==sha(D/'plan.json');continue
  if expired():pulse('paused_allocation_deadline',completed=len(list(folder.glob('*.json'))));return
  values=[]
  def hook(module,args,output):
   assert module is mdl.model.layers[12];h=output[0]if isinstance(output,tuple)else output;values.append(h[0,-1].detach().float().cpu())
  handle=mdl.model.layers[12].register_forward_hook(hook)
  try:
   ids=torch.tensor([rendered[row['id']]],device=mdl.get_input_embeddings().weight.device)
   with torch.inference_mode():mdl(input_ids=ids,use_cache=False)
  finally:handle.remove()
  assert len(values)==1 and values[0].numel()==5120;save(p,{'id':row['id'],'plan_sha256':sha(D/'plan.json'),'norm_l2_float32':float(values[0].norm()),'input_ids_sha256':row['input_ids_sha256'],'hook_block':12,'prefill_captures':1,'utc':utc()});pulse('measuring_norm',completed=len(list(folder.glob('*.json'))),total=60,elapsed_seconds=time.monotonic()-start)
 values=[json.loads((folder/(r['id']+'.json')).read_text())['norm_l2_float32']for r in rows];median=float(np.median(values))
 result={'utc':utc(),'n':60,'injection_block_zero_based':12,'keep60_median':median,'rho':0.9*median,'rho_multiplier':0.9,'plan_sha256':sha(D/'plan.json'),'execution_sha256':sha(D/'execution.json'),'rows_sha256':{p.name:sha(p)for p in folder.glob('*.json')},'backend':'vicuna_node01_native_bf16_norm','host':socket.gethostname(),'GPU_physical':[1,2],'software_and_node_are_explicit_not_crossnode_equivalence_claim':True,'no_targets_no_training_no_test_effects':True};save(D/'complete.json',result);pulse('complete',completed=60,total=60,keep60_median=median,rho=0.9*median);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
