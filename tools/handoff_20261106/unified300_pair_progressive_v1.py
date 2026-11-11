"""Method-specific HarmBench PAIR adapter: source parsers/controller, local shared roles, private logs."""
from pathlib import Path
from types import SimpleNamespace,MethodType
from typing import List
from concurrent.futures import ThreadPoolExecutor,as_completed,wait,FIRST_COMPLETED
import ast,copy,datetime,hashlib,json,os,re,sys,threading,time,contextlib
import numpy as np,torch
from transformers import AutoModelForCausalLM,AutoTokenizer
from accelerate.utils import find_executable_batch_size
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T))
from search_target_injection300 import generate_with_injection
P=json.loads((U/'S1b_PAIR_progressive_v1.json').read_text());mode=sys.argv[1];key=sys.argv[2]if len(sys.argv)>2 else'llama';assert mode in ['gate','bulk'];assert os.environ['CUDA_VISIBLE_DEVICES']=='0,1'
D=U/(('PAIR_progressive_gate_v1/'+key)if mode=='gate'else('PAIR_progressive/'+key+'/tier'+str(int(sys.argv[3]))));lease=Path(os.environ['DEF_LEASE_DIR']);CTX=threading.local();ledger=[];histories=[];ledger_lock=threading.Lock();live_lock=threading.Lock();live={}
def H(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for x in iter(lambda:f.read(16*1024*1024),b''):h.update(x)
 return h.hexdigest()
def L(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(o,indent=2)+'\n');q.replace(p)
def pulse(phase,**x):
 with live_lock:live.clear();live.update(dict(utc=utc(),pid=os.getpid(),mode=mode,target=key,phase=phase,main_judge_effects_read=False,**x));save(D/'live.json',live);save(lease/'live.json',live)
def beat():
 while True:
  time.sleep(10)
  with live_lock:
   if live:live['heartbeat_utc']=utc();save(D/'live.json',live);save(lease/'live.json',live)
assert H(__file__)==P['worker_sha256'];threading.Thread(target=beat,daemon=True).start();cold_start=time.monotonic();pulse('verifying_assets')
for rel,h in P['source_sha256'].items():assert H(R/rel)==h,rel
for kind,path in [('role',P['role_model_path']),('target',P['target_models'][key]['path'])]:
 for name,h in P['assets_sha256'][kind if kind=='role'else key].items():assert H(Path(path)/name)==h,name
role_tok=AutoTokenizer.from_pretrained(P['role_model_path'],local_files_only=True);role_tok.padding_side='left';role_tok.pad_token=role_tok.eos_token
role_model=AutoModelForCausalLM.from_pretrained(P['role_model_path'],local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval()
target_tok=AutoTokenizer.from_pretrained(P['target_models'][key]['path'],local_files_only=True);target_tok.padding_side='left'
if target_tok.pad_token_id is None:target_tok.pad_token=target_tok.eos_token
target_model=AutoModelForCausalLM.from_pretrained(P['target_models'][key]['path'],local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:1'}).eval();zero=np.zeros(target_model.config.hidden_size,dtype=np.float32)
class NativeConversation:
 roles=('user','assistant')
 def __init__(self,tok):self.tok=tok;self.messages=[];self.system_message='';self.sep2=tok.eos_token;self.owner=None
 def __deepcopy__(self,memo):
  z=NativeConversation(self.tok);z.messages=copy.deepcopy(self.messages);z.system_message=self.system_message;z.owner=self.owner;return z
 def set_system_message(self,text):self.system_message=text
 def append_message(self,role,text):self.messages.append([role,text])
 def update_last_message(self,text):self.messages[-1][1]=text
 def get_prompt(self):
  bid=CTX.bid
  if self.owner is None:self.owner=bid
  assert self.owner==bid,'conversation owner mismatch'
  msgs=([{'role':'system','content':self.system_message}]if self.system_message else[])+[{'role':r,'content':t}for r,t in self.messages]
  is_assistant=bool(msgs and msgs[-1]['role']=='assistant');tail=msgs[-1]['content']if is_assistant else None
  native=self.tok.apply_chat_template(msgs[:-1]if is_assistant else msgs,add_generation_prompt=True,tokenize=False,enable_thinking=False)
  with ledger_lock:histories.append(dict(bid=bid,roles=[r for r,t in self.messages],owner_ok=True,messages=len(self.messages)))
  return native if not is_assistant or tail is None else native+tail+self.sep2

def source_function(file,name,cls=None):
 tree=ast.parse((R/file).read_text());body=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==cls).body if cls else tree.body;node=next(n for n in body if isinstance(n,ast.FunctionDef)and n.name==name);env=dict(shared);exec(compile(ast.Module(body=[node],type_ignores=[]),str(R/file),'exec'),env);return env[name]
shared=dict(ast=ast,os=os,logging=__import__('logging'),torch=torch,copy=copy,re=re,json=json,List=List,find_executable_batch_size=find_executable_batch_size)
for fname in ['common.py','system_prompts.py']:
 path=R/'repos/HarmBench/baselines/pair'/fname;nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),shared)
shared['ray']=SimpleNamespace(get=lambda x:x);shared['get_conversation_template']=lambda name:NativeConversation(role_tok)
base='repos/HarmBench/baselines/pair/'
shared['clean_attacks_and_convs']=source_function(base+'PAIR.py','clean_attacks_and_convs')
pair_fn=source_function(base+'PAIR.py','generate_test_cases_single_behavior','PAIR');attack_fn=source_function(base+'conversers.py','get_attack','AttackLM');target_fn=source_function(base+'conversers.py','get_response','TargetLM');hf_batch=source_function(base+'language_models.py','batch_generate_bs','HuggingFace');hf_generate=source_function(base+'language_models.py','batched_generate','HuggingFace')
class Core:
 def __init__(self,model,tok,is_target):
  self.model=model;self.tokenizer=tok;self.eos_token_ids=[tok.eos_token_id,tok.encode('}',add_special_tokens=False)[0]];self.generation_batch_size=32;self.lock=threading.Lock();self.is_target=is_target;self.batch_generate_bs=MethodType(hf_batch,self)
 def invoke(self,role,prompts,**kwargs):
  bid=CTX.bid;index=CTX.counts.get(role,0);CTX.counts[role]=index+1;queued=time.monotonic();seed=int.from_bytes(hashlib.sha256(f"{P['seed']}:{bid}:{role}:{index}".encode()).digest()[:4],'little')
  if self.is_target:
   normalized=[]
   for text in prompts:
    native=self.tokenizer(text,add_special_tokens=False).input_ids
    if self.tokenizer(text).input_ids!=native:
     assert self.tokenizer.bos_token and text.startswith(self.tokenizer.bos_token);text=text[len(self.tokenizer.bos_token):]
    assert self.tokenizer(text).input_ids==native;normalized.append(text)
   prompts=normalized
  with self.lock:
   start=time.monotonic();receipts=[];old=self.model.generate
   if self.is_target and CTX.patched:
    def wrapped(*args,**kw):
     assert not args;enc={k:kw.pop(k)for k in ['input_ids','attention_mask','position_ids','token_type_ids']if k in kw};out,receipt=generate_with_injection(self.model,enc,zero,P['target_models'][key]['layer'],kw,original_generate=old);receipts.append(receipt);return out
    self.model.generate=wrapped
   try:
    rng=torch.random.fork_rng(devices=[0])if kwargs['temperature']>0 else contextlib.nullcontext()
    with rng:
     if kwargs['temperature']>0:torch.manual_seed(seed)
     out=hf_generate(self,prompts,**kwargs)
   finally:self.model.generate=old
   active=time.monotonic()-start
  event=dict(bid=bid,role=role,call_index=index,batch_rows=len(prompts),seed=seed,max_n_tokens=kwargs['max_n_tokens'],temperature=kwargs['temperature'],waiting_seconds=start-queued,active_seconds=active,generation_batch_size=self.generation_batch_size,request_sha256=hashlib.sha256(json.dumps(prompts).encode()).hexdigest(),target_injection_receipts=receipts)
  with ledger_lock:ledger.append(event)
  return out
class Port:
 def __init__(self,fn):self.fn=fn
 def __call__(self,*a,**k):return self.fn(*a,**k)
 def remote(self,*a,**k):return self.fn(*a,**k)
roles=Core(role_model,role_tok,False);target=Core(target_model,target_tok,True)
def handle(core,role):return SimpleNamespace(batched_generate=Port(lambda prompts,**kw:core.invoke(role,prompts,**kw)))
def build_object(engineering=False):
 cfg=P['engineering']if engineering else P['formal'];att=SimpleNamespace(model_name_or_path='Qwen/Qwen3-8B',temperature=cfg['attack_temp'],max_n_tokens=cfg['attack_max_n_tokens'],max_retries=cfg['max_retries'],template=NativeConversation(role_tok),model=handle(roles,'attacker'),use_ray=False);att.get_attack=MethodType(attack_fn,att)
 tar=SimpleNamespace(model_name_or_path=P['target_models'][key]['model_name'],max_n_tokens=cfg['target_max_n_tokens'],temperature=0.,template=NativeConversation(target_tok),model=handle(target,'target'),use_ray=False);tar.get_response=MethodType(target_fn,tar)
 judge=SimpleNamespace(judge_name='Qwen/Qwen3-8B',max_n_tokens=cfg['judge_max_n_tokens'],temperature=0.,init_msg='Rating: [[',judge_model=handle(roles,'scorer'))
 for name,cls in [('get_judge_prompt','JudgeBase'),('process_output','JudgeBase'),('create_conv','OpenSourceJudge'),('score','OpenSourceJudge')]:setattr(judge,name,MethodType(source_function(base+'judges.py',name,cls),judge))
 obj=SimpleNamespace(attackLM=att,targetLM=tar,judgeLM=judge,n_streams=cfg['n_streams'],steps=cfg['steps'],keep_last_n=cfg['keep_last_n'],cutoff_score=cfg['cutoff_score'],behavior_id_to_target=L(U/'targets.private.json'));return obj
cold_seconds=time.monotonic()-cold_start
if mode=='gate':
 refs=L(U/'search_gate20_inputs.private.json');CTX.bid='zero20';CTX.counts={};texts=[]
 for r in refs:
  conv=NativeConversation(target_tok);conv.append_message('user',r['prompt']);conv.append_message('assistant',None);texts.append(conv.get_prompt())
 CTX.patched=False;a=target.invoke('target',texts,max_n_tokens=150,temperature=0.,stop_tokens=['}']);CTX.patched=True;b=target.invoke('target',texts,max_n_tokens=150,temperature=0.,stop_tokens=['}']);pairs=[dict(id=r['id'],byte_equal=x==y)for r,x,y in zip(refs,a,b)];save(D/'target_zero20.json',dict(utc=utc(),passed=all(x['byte_equal']for x in pairs),N=20,pairs=pairs));assert all(x['byte_equal']for x in pairs)
 runs=[]
 def benign(i):
  CTX.bid=f'benign_{i}';CTX.counts={};CTX.patched=True;obj=build_object(True);obj.behavior_id_to_target={CTX.bid:P['benign_target']};pair_fn(obj,dict(Behavior=f'Name a common fruit for benign test session {i}.',ContextString='',BehaviorID=CTX.bid),verbose=False);return dict(bid=CTX.bid,counts=CTX.counts)
 for order,workers in [(list(range(12)),8),(list(reversed(range(12))),4)]:
  with ledger_lock:ledger.clear();histories.clear()
  with ThreadPoolExecutor(max_workers=workers)as pool:rs=[f.result()for f in as_completed([pool.submit(benign,i)for i in order])]
  structure=sorted([(e['bid'],e['role'],e['call_index'],e['batch_rows'])for e in ledger]);assert all(h['owner_ok']for h in histories);assert all(r['counts'].get('target')==2 and r['counts'].get('scorer')==2 for r in rs);runs.append(structure)
 assert runs[0]==runs[1],'controller call structure changed with execution order'
 save(D/'complete.json',dict(utc=utc(),passed=True,method='PAIR',target=key,zero20=20,behavior_count=12,orders=2,concurrency_orders=[8,4],source_parsers_and_controller_executed=True,role_shared_one_instance=True,thinking=False,seed=P['seed'],engineering_config=P['engineering'],formal_config_unchanged=True,structure=runs[0],plan_sha256=H(U/'S1b_PAIR_progressive_v1.json'),cold_seconds=cold_seconds));
 if key=='llama':save(U/'PAIR_progressive_gate_v1/complete.json',L(D/'complete.json'))
 pulse('gate_complete');sys.exit(0)

assert mode=='bulk'
tier=int(sys.argv[3]);assert tier in [88,220,440]
assert L(U/'PAIR_progressive_gate_v1'/key/'complete.json')['passed']
assert L(U/'PAIR_progressive_gate_v1'/key/'complete.json')['plan_sha256']==H(U/'S1b_PAIR_progressive_v1.json')
if tier>88:
 admission=L(U/'search_progressive_tier_admissions'/f'{tier}.json')
 assert admission['admitted'] and not admission['outcomes_used']
assert H(U/'PAIR_progressive_inputs.private.json')==P['progressive']['full_inputs_sha256']
assert H(U/'targets.private.json')==P['progressive']['target_mapping_sha256']
all_inputs={r['id']:r for r in L(U/'PAIR_progressive_inputs.private.json')}
ids=P['progressive']['IDs_by_tier'][str(tier)]
retained={}; inherited_cost=0.
for bid, expected in P['progressive']['retained_pilot_rows'][key].items():
 path=R/expected['path'];assert H(path)==expected['sha256'];row=L(path)
 assert row['id']==int(bid) and row['failure'] is None
 assert row['source_behavior_sha256']==all_inputs[int(bid)]['behavior_sha256']
 retained[int(bid)]={'path':str(path.relative_to(R)),'sha256':H(path),'selected_prompt_sha256':hashlib.sha256(row['selected_prompt'].encode()).hexdigest(),'from_original_pilot':True}
for smaller in [88,220]:
 if smaller>=tier:continue
 prior=U/'PAIR_progressive'/key/f'tier{smaller}'/'complete.json'
 assert prior.exists()
 for bid, receipt in L(prior)['selected_rows'].items():
  path=R/receipt['path'];assert H(path)==receipt['sha256'];retained[int(bid)]=receipt
for path in (D/'rows.private').glob('*.json'):
 row=L(path);assert row['id'] in ids
 assert row['plan_sha256']==H(U/'S1b_PAIR_progressive_v1.json')
 retained[row['id']]={'path':str(path.relative_to(R)),'sha256':H(path),'selected_prompt_sha256':None if row['selected_prompt'] is None else hashlib.sha256(row['selected_prompt'].encode()).hexdigest(),'failure_type':None if row['failure'] is None else row['failure'].split(':',1)[0]}
inputs=[all_inputs[i] for i in ids if i not in retained]
formal_start=time.monotonic();results=[];stop_new=False
def spent_search_GPUh():
 total=0.
 for path in (U/'queue_jobs').glob('*/exit.json'):
  desc=path.parent/'descriptor.json'
  if not desc.exists():continue
  a=L(desc)['argv'];is_search=any(any(tag in value for tag in ['unified300_pair_','unified300_tap_','unified300_autodan_'])for value in a)
  if is_search and any(value in ['pilot','bulk']for value in a):
   ex=L(path);total+=len(L(desc)['gpus'])*ex.get('resident_seconds',0)/3600
 return total+2*(cold_seconds+time.monotonic()-formal_start)/3600
def run_row(r):
 bid=f"sorry_{r['id']:04d}";CTX.bid=bid;CTX.counts={};CTX.patched=True;started=time.monotonic();failure=None;test_case=None;logs=[]
 try:test_case,logs=pair_fn(build_object(False),dict(Behavior=r['behavior'],ContextString='',BehaviorID=bid),verbose=False)
 except Exception as e:failure=type(e).__name__+': '+str(e)[:300]
 row=dict(utc=utc(),id=r['id'],bid=bid,seconds=time.monotonic()-started,call_counts=CTX.counts,selected_prompt=test_case,streams=logs,failure=failure,source_behavior_sha256=r['behavior_sha256'],plan_sha256=H(U/'S1b_PAIR_progressive_v1.json'))
 save(D/'rows.private'/f"{r['id']:04d}.json",row);return row
iterator=iter(inputs)
with ThreadPoolExecutor(max_workers=8)as pool:
 futures={}
 def fill():
  global stop_new
  if spent_search_GPUh()>=600:stop_new=True
  while not stop_new and len(futures)<8:
   try:row=next(iterator)
   except StopIteration:break
   futures[pool.submit(run_row,row)]=row['id']
 fill()
 while futures:
  done,_=wait(futures,return_when=FIRST_COMPLETED)
  for future in sorted(done,key=lambda f:futures[f]):
   row=future.result();futures.pop(future);results.append(row)
   path=D/'rows.private'/f"{row['id']:04d}.json"
   retained[row['id']]={'path':str(path.relative_to(R)),'sha256':H(path),'selected_prompt_sha256':None if row['selected_prompt'] is None else hashlib.sha256(row['selected_prompt'].encode()).hexdigest(),'failure_type':None if row['failure'] is None else row['failure'].split(':',1)[0]}
   if row['failure'] is not None:stop_new=True
  pulse('progressive_rows',tier=tier,N_saved=len(retained),N_pending=tier-len(retained),stop_new=stop_new)
  fill()
window=time.monotonic()-formal_start
receipt=dict(utc=utc(),method='PAIR',target=key,tier=tier,N_saved=len(retained),N_retained_pilot=10,cold_seconds=cold_seconds,formal_window_seconds=window,new_reserved_GPUh=2*(cold_seconds+window)/3600,search_actual_GPUh_including_failed_attempts=spent_search_GPUh(),selected_rows={str(i):retained[i]for i in ids if i in retained},unattempted_IDs=[i for i in ids if i not in retained],execution_failure_IDs=[i for i in ids if i in retained and retained[i].get('failure_type')],source_algorithm_changed=False,main_judge_effects_read=False,independent_alpha0_fulfillment_not_read=True)
save(D/('complete.json'if len(retained)==tier else'incomplete.json'),receipt)
save(D/'call_ledger.private.json',ledger)
if len(retained)!=tier:raise SystemExit(42)
pulse('progressive_tier_complete',tier=tier,N_saved=tier)
