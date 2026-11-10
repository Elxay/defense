"""Sharded S0 WG human-reference scoring, original single path and reference20."""
from pathlib import Path
import ast,datetime,hashlib,json,os,re,socket,sys,time
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/home/dell/Def');U=R/'results/audit/unified300';M=R/'models/WildGuard'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(16*1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def main():
 shard=int(sys.argv[1]);card=int(sys.argv[2]);assert shard in[0,1,2]and os.environ['CUDA_VISIBLE_DEVICES']==str(card)
 plan=load(U/'human_reference_plan.json');assert sha(Path(__file__))==plan['workers']['WG'];assert sha(U/'human_inputs.private.json')==plan['input_sha256']
 def pulse(phase,**kw):save(U/f'WG_live_{shard}.json',dict(utc=utc(),pid=os.getpid(),host=socket.gethostname(),physical_gpu=card,backend='hf_node01_single',phase=phase,aggregate_read=False,**kw))
 manifest=load(M/'DOWNLOAD_SHA256.json');assert manifest['revision']=='cbba4823f3e8020e5a74a5e29bf85072def6f2ff'
 for name,value in manifest['files'].items():assert sha(M/name)==value;pulse('verifying_assets',last_verified=name)
 block=re.search(r'```python\s*\n(.*?)\n```',(M/'README.md').read_text(),re.S).group(1);template=next(ast.literal_eval(n.value)for n in ast.parse(block).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='instruction_format'for t in n.targets))
 assert hashlib.sha256(template.encode()).hexdigest()==plan['WG_template_sha256']
 tok=AutoTokenizer.from_pretrained(M,local_files_only=True);model=AutoModelForCausalLM.from_pretrained(M,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval();config=load(M/'config.json');keys=['Harmful request','Response refusal','Harmful response']
 def classify(row):
  tokens=tok([template.format(prompt=row['prompt'],response=row['response'])],return_tensors='pt',add_special_tokens=False);n=tokens.input_ids.shape[1]
  if n+32>config['max_position_embeddings']:return '',{k:None for k in keys},'over_context_limit',n
  with torch.inference_mode():z=model.generate(**tokens.to('cuda:0'),max_new_tokens=32,do_sample=False,pad_token_id=tok.eos_token_id)
  text=tok.decode(z[0,n:],skip_special_tokens=True);parsed={k:re.search(r'^'+re.escape(k)+r':\s*(yes|no)\s*$',text,re.M|re.I)for k in keys};labels={k:v.group(1).lower()if v else None for k,v in parsed.items()};return text,labels,None if all(parsed.values())else'invalid_format',n
 refpath=R/'results/audit/crossmodel287/gemma_admission18/WG_reference20.private.json';assert sha(refpath)==plan['WG_reference20_sha256'];pairs=[]
 for r in load(refpath):
  text,_,_,_=classify(r);pairs.append({'id':r['id'],'byte_equal':hashlib.sha256(text.encode()).hexdigest()==r['expected_output_sha256']});pulse('reference20',n=len(pairs),total=20)
 assert len(pairs)==20;gate=dict(utc=utc(),passed=all(x['byte_equal']for x in pairs),pairs=pairs,physical_gpu=card,backend='hf_node01_single');save(U/f'WG_gate20_{shard}.json',gate);assert gate['passed']
 rows=load(U/'human_inputs.private.json');rows=rows[shard::3];sig=dict(plan_sha256=sha(U/'human_reference_plan.json'),worker_sha256=sha(Path(__file__)),input_sha256=plan['input_sha256'],shard=shard,physical_gpu=card,backend='hf_node01_single');start=time.monotonic()
 for i,r in enumerate(rows,1):
  p=U/'WG_scores'/(r['id']+'.json')
  if p.exists():assert load(p)['signature']==sig;continue
  text,labels,reason,n=classify(r);save(p,dict(id=r['id'],labels=labels,output=text,invalid_reason=reason,input_tokens=n,input_over4096=n>4096,signature=sig))
  if i%10==0:pulse('scoring_human_test',n=i,total=len(rows),seconds_per_case=(time.monotonic()-start)/i)
 save(U/f'WG_complete_{shard}.json',dict(utc=utc(),n=len(rows),shard=shard,aggregate_read=False));pulse('complete_waiting_other_judges',n=len(rows),total=len(rows))
if __name__=='__main__':main()
