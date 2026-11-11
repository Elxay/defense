"""Shared Qwen3 benign role-backend prototype; not an admitted search controller."""
from pathlib import Path
import json,hashlib,os,datetime,time,sys
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(o,indent=2)+'\n');q.replace(p)
P=json.loads((U/'role_backend_benign_plan.json').read_text());assert H(__file__)==P['worker_sha256'];assert os.environ['CUDA_VISIBLE_DEVICES']=='0';O=U/'role_backend_benign';save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='loading'))
assets=json.loads((U/'translator_Qwen3_asset_manifest.json').read_text());mp=Path(assets['path'])
for f,h in assets['files_sha256'].items():assert H(mp/f)==h,f
tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval()
class Backend:
 def __init__(self):self.ledger=[];self.counts={}
 def call_many(self,requests,role):
  assert role in ['attacker','scorer'];ids=[];metadata=[]
  for r in requests:
   k=(r['behavior_id'],role);n=self.counts.get(k,0);assert r['call_index']==n;self.counts[k]=n+1
   encoded=tok.apply_chat_template(r['messages'],add_generation_prompt=True,enable_thinking=False);ids.append(encoded);metadata.append(dict(behavior_id=r['behavior_id'],role=role,call_index=n,history_roles=[x['role']for x in r['messages']],history_message_sha256=[hashlib.sha256(x['content'].encode()).hexdigest()for x in r['messages']],input_ids_sha256=hashlib.sha256(json.dumps(encoded).encode()).hexdigest()))
  enc=tok.pad({'input_ids':ids},padding=True,return_tensors='pt').to('cuda:0');seed=P['seed'];torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
  with torch.inference_mode():out=model.generate(**enc,max_new_tokens=16,do_sample=True,temperature=.7,top_p=.9,pad_token_id=tok.pad_token_id)
  width=enc.input_ids.shape[1];replies=[tok.decode(x[width:],skip_special_tokens=True)for x in out];self.ledger+=metadata
  return replies
runs=[]
for run,order in enumerate([list(range(8)),list(reversed(range(8)))]):
 backend=Backend();history={i:[{'role':'user','content':f'Benign session {i}: name a common fruit using one short sentence.'}]for i in range(8)}
 for round_index in range(2):
  req=[dict(behavior_id=i,call_index=round_index,messages=history[i])for i in order];reply=backend.call_many(req,'attacker')
  for r,ans in zip(req,reply):history[r['behavior_id']]+=[{'role':'assistant','content':ans},{'role':'user','content':f'Benign session {r["behavior_id"]}: name a different common fruit.'}]
  score=[dict(behavior_id=i,call_index=round_index,messages=[{'role':'user','content':f'Benign session {i}: reply with the single digit 1.'}])for i in order];backend.call_many(score,'scorer')
 expected={(i,role):2 for i in range(8)for role in ['attacker','scorer']};assert backend.counts==expected;assert len(backend.ledger)==32
 for row in backend.ledger:
  expected_roles=['user']if row['role']=='scorer'or row['call_index']==0 else['user','assistant','user'];assert row['history_roles']==expected_roles
 save(O/f'run{run}_structure.json',dict(utc=utc(),ledger=backend.ledger,call_counts=[dict(behavior_id=i,role=role,count=backend.counts[(i,role)])for i,role in sorted(expected)]));runs.append(backend.ledger)
structure=lambda run:sorted([(r['behavior_id'],r['role'],r['call_index'],r['history_roles'])for r in run],key=lambda x:(x[0],x[1],x[2]));assert structure(runs[0])==structure(runs[1])
save(O/'prototype_complete.json',dict(utc=utc(),passed_benign_backend_structure=True,behavior_count=8,orders=2,model_calls_per_order=4,request_rows_per_order=32,shared_one_weight_instance=True,thinking=False,seed=P['seed'],no_text_byte_equivalence_claim=True,actual_source_search_controller_integrated=False,formal_S1b_role_gate_admitted=False,formal_search_outputs=0,remaining='wire this counted transport into unchanged PAIR/TAP/AutoDAN role parsers and test real controller isolation before S1b',worker_sha256=H(__file__)));save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='benign_prototype_complete_controller_gate_pending'))
