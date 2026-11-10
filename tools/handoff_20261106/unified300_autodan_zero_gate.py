"""AutoDAN's unchanged respond/generate methods with a zero-injection wrapper."""
from pathlib import Path
from types import SimpleNamespace,MethodType
import ast,datetime,hashlib,json,os,sys,time
import numpy as np,torch
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';A=R/'repos/AutoDAN-Turbo'
sys.path.insert(0,str(R/'tools/handoff_20261106'))
from search_target_injection300 import generate_with_injection
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def extract(p,clsname,name):
 tree=ast.parse(p.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==clsname);fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name==name);scope={};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),scope);return scope[name]
class NativeTokenizer:
 def __init__(self,tok):self.base=tok;self.last_ids=None;self.stripped=False
 def __getattr__(self,key):return getattr(self.base,key)
 def apply_chat_template(self,messages,**kwargs):
  text=self.base.apply_chat_template(messages,**kwargs);assert isinstance(text,str)
  native=self.base.apply_chat_template(messages,add_generation_prompt=kwargs.get('add_generation_prompt',False));self.stripped=False
  if self.base(text)['input_ids']!=native:
   assert self.base.bos_token and text.startswith(self.base.bos_token);text=text[len(self.base.bos_token):];self.stripped=True
  assert self.base(text)['input_ids']==native;self.last_ids=native;return text
 def __call__(self,text,**kwargs):
  result=self.base(text,**kwargs);assert result['input_ids'][0].tolist()==self.last_ids;return result
def main():
 key,card=sys.argv[1],int(sys.argv[2]);plan=load(U/'autodan_zero_gate_plan.json');assert sha(__file__)==plan['worker_sha256'];assert sha(R/'tools/handoff_20261106/search_target_injection300.py')==plan['adapter_sha256'];assert os.environ['CUDA_VISIBLE_DEVICES']==str(card)
 for path,s in plan['source_sha256'].items():assert sha(R/path)==s
 d=U/'history_search_gates'/key;assert not(d/'autodan_zero20.json').exists();spec=plan['models'][key]
 def pulse(phase,**kw):save(d/'autodan_live.json',dict(utc=utc(),pid=os.getpid(),physical_gpu=card,model=key,phase=phase,main_test_outputs=0,**kw))
 pulse('loading');tok=AutoTokenizer.from_pretrained(spec['path'],local_files_only=True);model=AutoModelForCausalLM.from_pretrained(spec['path'],local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval()
 facade=NativeTokenizer(tok);hf=SimpleNamespace(model=model,tokenizer=facade);generate=extract(A/'llm/huggingface_models.py','HuggingFaceModel','generate');hf.generate=MethodType(generate,hf);target=SimpleNamespace(model=hf);respond=extract(A/'framework/target.py','Target','respond')
 refs=load(U/'search_gate20_inputs.private.json');assert sha(U/'search_gate20_inputs.private.json')==plan['input_sha256'];zero=np.zeros(model.config.hidden_size,dtype=np.float32);torch.manual_seed(plan['seed']);torch.cuda.manual_seed_all(plan['seed']);pairs=[]
 for i,row in enumerate(refs):
  pulse('unpatched_sampled_target',completed=i,total=20);cpu=torch.get_rng_state();cuda=torch.cuda.get_rng_state_all();start=time.monotonic();reference=respond(target,row['prompt']);torch.set_rng_state(cpu);torch.cuda.set_rng_state_all(cuda)
  original=model.generate;receipts=[]
  def wrapped(*args,**kwargs):
   assert not args;encoded={k:kwargs.pop(k)for k in ['input_ids','attention_mask','token_type_ids','position_ids']if k in kwargs};out,meta=generate_with_injection(model,encoded,zero,spec['layer'],kwargs,original_generate=original);receipts.append(meta);return out
  pulse('patched_sampled_target',completed=i,total=20);model.generate=wrapped
  try:out=respond(target,row['prompt'])
  finally:model.generate=original
  assert all(v==0 for r in receipts for v in r['rho_runtime'])
  pair={'id':row['id'],'byte_equal':reference.encode()==out.encode(),'reference_sha256':hashlib.sha256(reference.encode()).hexdigest(),'patched_sha256':hashlib.sha256(out.encode()).hexdigest(),'native_BOS_interface_asserted':True,'removed_already_rendered_BOS':facade.stripped,'elapsed_seconds_both_paths':time.monotonic()-start,'injection_metadata':receipts};save(d/'autodan_rows'/f'{i:02d}.json',pair);pairs.append(pair)
  if not pair['byte_equal']:save(d/'autodan_zero20.json',{'utc':utc(),'N_completed':len(pairs),'passed':False,'pairs':pairs});pulse('failed_no_fallback');return
 result={'utc':utc(),'N':20,'passed':all(x['byte_equal']for x in pairs),'pairs':pairs,'same_RNG_state_for_each_pair':True,'source_sampling_preserved':{'do_sample':True,'temperature':.6,'top_p':.9,'max_length_total':10000},'native_model_interface':'same documented native-template/BOS adapter in unmodified-source reference and injected target','backend':'HF bf16 sdpa, no quantization','plan_sha256':sha(U/'autodan_zero_gate_plan.json'),'role_service_and_eight_behavior_controller_admitted':False};save(d/'autodan_zero20.json',result);pulse('complete_only_injection_gate')
if __name__=='__main__':main()
