"""Same-node S0 historical batching and unmodified-HF injection equivalence."""
from pathlib import Path
import ast,datetime,hashlib,json,os,sys,time
from types import SimpleNamespace
import numpy as np,torch
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';C=R/'results/audit/crossmodel287'
sys.path.insert(0,str(R/'tools/handoff_20261106'))
from batched_injection300 import generate_batch_with_injection
from search_target_injection300 import call_upstream_with_injection
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def source_batch(path):
 tree=ast.parse(path.read_text());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='HuggingFace');fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef)and x.name=='batch_generate_bs');scope={'torch':torch};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),scope);return scope['batch_generate_bs']
def main():
 key,card=sys.argv[1],int(sys.argv[2]);assert os.environ['CUDA_VISIBLE_DEVICES']==str(card)
 plan=load(U/'history_search_gate_plan.json');assert sha(__file__)==plan['worker_sha256'];assert sha(R/'tools/handoff_20261106/search_target_injection300.py')==plan['adapter_sha256']
 spec=plan['models'][key];d=U/'history_search_gates'/key;assert not(d/'complete.json').exists()
 def pulse(phase,**kw):save(d/'live.json',dict(utc=utc(),pid=os.getpid(),physical_gpu=card,model=key,phase=phase,main_test_outputs=0,**kw))
 pulse('loading');tok=AutoTokenizer.from_pretrained(spec['path'],local_files_only=True);tok.padding_side='left'
 if tok.pad_token_id is None:tok.pad_token=tok.eos_token
 model=AutoModelForCausalLM.from_pretrained(spec['path'],local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32)
 # Exact historical membership, original B8, original120 cap. Do not compare B32 against B8.
 history=load(U/(key+'_history20_inputs.private.json'));assert sha(U/(key+'_history20_inputs.private.json'))==spec['history_input_sha256'];checks=[]
 for group in history['batches']:
  ids=[tok.apply_chat_template([{'role':'user','content':r['prompt']}],add_generation_prompt=True)for r in group['rows']]
  outputs=generate_batch_with_injection(model,tok,ids,zero,layer=spec['layer'],max_new_tokens=120,alpha=0)
  for row,out in zip(group['rows'],outputs):
   if row['selected']:checks.append({'id':row['id'],'byte_equal':hashlib.sha256(out['text'].encode()).hexdigest()==row['expected_output_sha256'],'injection_count':out['injection_count'],'rho_runtime':out['rho_runtime']})
  pulse('history20',n=len(checks))
 assert len(checks)==20
 hist={'utc':utc(),'passed':all(x['byte_equal']for x in checks),'N':20,'batch_size':8,'cap':120,'checks':checks,'meaning':'same historical membership/B8; no claim that newly selected B differs byte-identically'};save(d/'history20.json',hist)
 # Native template strings, stripping only a duplicated BOS before the unchanged upstream tokenizer.
 refs=load(U/'search_gate20_inputs.private.json');assert sha(U/'search_gate20_inputs.private.json')==plan['search_input_sha256'];prompts=[];render=[]
 for row in refs:
  messages=[{'role':'user','content':row['prompt']}];native=tok.apply_chat_template(messages,add_generation_prompt=True);text=tok.apply_chat_template(messages,add_generation_prompt=True,tokenize=False);removed=False
  if tok(text)['input_ids']!=native:
   assert tok.bos_token and text.startswith(tok.bos_token)
   text=text[len(tok.bos_token):];removed=True
  assert tok(text)['input_ids']==native,'No unsupported native-template substitution'
  prompts.append(text);render.append({'id':row['id'],'source_tokenizer_equals_native':True,'removed_already_rendered_BOS':removed,'input_ids_sha256':hashlib.sha256(json.dumps(native).encode()).hexdigest()})
 save(d/'native_template_assertions.json',{'utc':utc(),'rows':render,'passed':True})
 for method in ['pair','tap']:
  path=R/f'repos/HarmBench/baselines/{method}/language_models.py';assert sha(path)==plan['source_sha256'][method];fn=source_batch(path);target=SimpleNamespace(model=model,tokenizer=tok,generation_batch_size=32)
  eos=[tok.eos_token_id,tok.encode('}',add_special_tokens=False)[0]];kwargs={'max_new_tokens':150,'do_sample':False,'eos_token_id':eos}
  pulse('search_reference_unpatched_HF',method=method)
  reference=fn(target,32,prompts,**kwargs)
  pulse('search_injection_zero',method=method)
  outputs,metadata=call_upstream_with_injection(fn,target,prompts,zero,spec['layer'],32,**kwargs)
  assert all(v==0 for m in metadata for v in m['rho_runtime'])
  pairs=[{'id':r['id'],'byte_equal':a.encode()==b.encode(),'reference_sha256':hashlib.sha256(a.encode()).hexdigest(),'patched_sha256':hashlib.sha256(b.encode()).hexdigest()}for r,a,b in zip(refs,reference,outputs)]
  result={'utc':utc(),'N':20,'passed':all(x['byte_equal']for x in pairs),'pairs':pairs,'injection_metadata':metadata,'explicit_EOS':eos,'search_cap':150,'source_batch_function_unmodified':True,'native_model_interface_asserted':True,'backend':'HF bf16 sdpa same instance same kwargs','source_sha256':sha(path)};save(d/(method+'_zero20.json'),result)
  if not result['passed']:pulse('search_zero20_failed',method=method);return
 save(d/'complete.json',{'utc':utc(),'history_passed':hist['passed'],'pair_and_tap_zero20':True,'AutoDAN_zero_gate':False,'does_not_validate_eight_behavior_controller_or_role_service':True,'plan_sha256':sha(U/'history_search_gate_plan.json')})
 pulse('complete_only_recorded_gates')
if __name__=='__main__':main()
