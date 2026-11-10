from pathlib import Path
import ast,datetime,hashlib,json,os,re,time,sys
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path('/home/dell/Def');U=R/'results/audit/unified300';M=R/'models/WildGuard';D=U/'calibration_S1a_WG'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
plan=load(U/'S1a_manifest.json');assert sha(__file__)==plan['code_sha256']['tools/handoff_20261106/unified300_calibration_wg.py'];assert os.environ['CUDA_VISIBLE_DEVICES']=='0';assert sha(U/'WG_batch_plan.json')==plan['WG_batch_plan_sha256'];wg=load(U/'WG_batch_plan.json');receipt=load(M/'DOWNLOAD_SHA256.json');assert receipt['revision']==wg['model_revision'];sys.path.insert(0,str(R/'src'));from judge.refusal import new_rule
assert sha(R/'src/judge/refusal.py')==plan['code_sha256']['src/judge/refusal.py']
def pulse(phase,**kw):save(D/'live.json',dict(utc=utc(),pid=os.getpid(),phase=phase,calibration_effect_read=False,**kw))
pulse('asset_hashes')
for n,h in receipt['files'].items():assert sha(M/n)==h
block=re.search(r'```python\s*\n(.*?)\n```',(M/'README.md').read_text(),re.S).group(1);template=next(ast.literal_eval(n.value)for n in ast.parse(block).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='instruction_format'for t in n.targets));assert hashlib.sha256(template.encode()).hexdigest()==wg['template_sha256']
pulse('loading');tok=AutoTokenizer.from_pretrained(M,local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(M,local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'}).eval();fields=['Harmful request','Response refusal','Harmful response']
def classify(rows):
 enc=tok([template.format(prompt=r['prompt'],response=r['response'])for r in rows],return_tensors='pt',padding=True,add_special_tokens=False).to('cuda:0');width=enc.input_ids.shape[1];assert width+32<=model.config.max_position_embeddings,'No silent clipping, unresolved calibration'
 with torch.inference_mode():out=model.generate(**enc,max_new_tokens=32,do_sample=False,pad_token_id=tok.eos_token_id)
 result=[]
 for i,r in enumerate(rows):
  text=tok.decode(out[i,width:],skip_special_tokens=True);p={k:re.search(r'^'+re.escape(k)+r':\s*(yes|no)\s*$',text,re.M|re.I)for k in fields};labels={k:v.group(1).lower()if v else None for k,v in p.items()};result.append(dict(id=r['id'],labels=labels,v2=int(new_rule(r['response'])),input_tokens=int(enc.attention_mask[i].sum()),input_over4096=int(enc.attention_mask[i].sum())>4096,judge_output_sha256=hashlib.sha256(text.encode()).hexdigest(),generation_record_sha256=r.get('generation_record_sha256')))
 return result
assert sha(U/'human_inputs.private.json')==wg['human_input_sha256'];source={r['id']:r for r in load(U/'human_inputs.private.json')};fixtures=[source[k]for k in wg['IDs']];pairs=[]
for i in range(0,20,8):
 for r,z in zip(fixtures[i:i+8],classify(fixtures[i:i+8])):pairs.append(dict(id=r['id'],byte_equal=z['judge_output_sha256']==wg['expected_output_sha256'][r['id']]))
save(D/'reference20.json',dict(utc=utc(),passed=all(x['byte_equal']for x in pairs),pairs=pairs));assert all(x['byte_equal']for x in pairs)
start=time.monotonic();expected=44
while True:
 completed=list((D/'tasks').glob('*/complete.json'))
 if len(completed)==expected:break
 tasks=sorted((D/'incoming.private').glob('*.json'))
 progressed=False
 for f in tasks:
  task=load(f);name=task['task_id'];assert re.fullmatch(r'(llama|qwen)__[a-z0-9_]+',name);folder=D/'tasks'/name
  if (folder/'complete.json').exists():continue
  assert task['manifest_sha256']==sha(U/'S1a_manifest.json');rows=task['rows'];assert [r['id']for r in rows]==plan['calibration_IDs'];assert len(rows)==700;assert hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()==task['rows_sha256'];bundle=[];progressed=True
  for i in range(0,700,8):
   group=rows[i:i+8];paths=[folder/'scores.private'/(r['id']+'.json')for r in group]
   if all(p.exists()for p in paths):
    part=[load(p)for p in paths];assert all(x['task_input_sha256']==sha(f)and x['generation_record_sha256']==r['generation_record_sha256']for x,r in zip(part,group))
   else:
    part=classify(group)
    for x,p in zip(part,paths):
     x['task_input_sha256']=sha(f);x['manifest_sha256']=sha(U/'S1a_manifest.json')
     if p.exists():assert load(p)==x,'Partial judge batch differs; preserve and stop'
     else:save(p,x)
   bundle.extend(part);pulse('scoring',task=name,completed_rows=min(i+8,700),total=700,completed_tasks=len(completed),total_tasks=44)
  out=folder/'bundle.private.json';save(out,dict(task_id=name,rows=bundle,manifest_sha256=sha(U/'S1a_manifest.json'),input_task_sha256=sha(f)));save(folder/'complete.json',dict(utc=utc(),task_id=name,N=700,bundle_sha256=sha(out),manifest_sha256=sha(U/'S1a_manifest.json'),absolute_condition_rates_aggregated=False))
 if not progressed:pulse('waiting_next_complete_generation',completed_tasks=len(completed),total_tasks=44);time.sleep(10)
 if time.monotonic()-start>30*3600:raise RuntimeError('30h wait limit; incomplete grid not selected')
save(D/'all_scoring_complete.json',dict(utc=utc(),tasks=44,rows=30800,manifest_sha256=sha(U/'S1a_manifest.json'),absolute_condition_rates_aggregated=False));pulse('all_complete_wait_frozen_selection_reader')
