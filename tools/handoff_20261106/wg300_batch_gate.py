"""S0 WildGuard batching check against frozen human-reference single outputs."""
from pathlib import Path
import ast,datetime,hashlib,json,os,re,time
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/home/dell/Def');U=R/'results/audit/unified300';M=R/'models/WildGuard'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def main():
 plan=load(U/'WG_batch_plan.json');assert sha(__file__)==plan['worker_sha256']
 assert sha(U/'human_inputs.private.json')==plan['human_input_sha256']
 assert os.environ['CUDA_VISIBLE_DEVICES']=='0'
 dest=U/'WG_batch';assert not (dest/'complete.json').exists()
 def pulse(phase,**kw):save(dest/'live.json',{'utc':utc(),'pid':os.getpid(),'phase':phase,'new_test_effect_read':False,**kw})
 pulse('verifying_assets')
 receipt=load(M/'DOWNLOAD_SHA256.json');assert receipt['revision']==plan['model_revision']
 for name,value in receipt['files'].items():assert sha(M/name)==value
 block=re.search(r'```python\s*\n(.*?)\n```',(M/'README.md').read_text(),re.S).group(1)
 template=next(ast.literal_eval(n.value)for n in ast.parse(block).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='instruction_format'for t in n.targets))
 assert hashlib.sha256(template.encode()).hexdigest()==plan['template_sha256']
 pulse('loading')
 tok=AutoTokenizer.from_pretrained(M,local_files_only=True);tok.padding_side='left'
 if tok.pad_token_id is None:tok.pad_token=tok.eos_token
 model=AutoModelForCausalLM.from_pretrained(M,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval()
 source={x['id']:x for x in load(U/'human_inputs.private.json')};rows=[source[k]for k in plan['IDs']]
 keys=['Harmful request','Response refusal','Harmful response'];results=[]
 for b in plan['batch_sizes']:
  pulse('batch_gate',batch_size=b)
  torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();tick=time.monotonic();pairs=[];tokens_generated=0
  for i in range(0,len(rows),b):
   group=rows[i:i+b];texts=[template.format(prompt=x['prompt'],response=x['response'])for x in group]
   enc=tok(texts,return_tensors='pt',padding=True,add_special_tokens=False).to('cuda:0');width=enc.input_ids.shape[1]
   with torch.inference_mode():out=model.generate(**enc,max_new_tokens=32,do_sample=False,pad_token_id=tok.eos_token_id)
   for j,row in enumerate(group):
    raw=out[j,width:].tolist();eos=model.generation_config.eos_token_id;eos={eos}if isinstance(eos,int)else set(eos)
    cut=next((z+1 for z,t in enumerate(raw)if t in eos),len(raw));tokens_generated+=cut
    text=tok.decode(raw[:cut],skip_special_tokens=True)
    parsed={k:re.search(r'^'+re.escape(k)+r':\s*(yes|no)\s*$',text,re.M|re.I)for k in keys}
    labels={k:v.group(1).lower()if v else None for k,v in parsed.items()}
    old=load(U/'WG_scores'/(row['id']+'.json'));assert sha(U/'WG_scores'/(row['id']+'.json'))==plan['single_record_sha256'][row['id']]
    pairs.append({'id':row['id'],'byte_equal':hashlib.sha256(text.encode()).hexdigest()==plan['expected_output_sha256'][row['id']],
       'field_equal':{k:labels[k]==old['labels'][k]for k in keys},'output_sha256':hashlib.sha256(text.encode()).hexdigest()})
   torch.cuda.synchronize()
  seconds=time.monotonic()-tick;free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();headroom=total-outside-torch.cuda.max_memory_reserved()
  result={'utc':utc(),'batch_size':b,'N':20,'exact_bytes':sum(x['byte_equal']for x in pairs),
    'field_agreements':{k:sum(x['field_equal'][k]for x in pairs)for k in keys},'pairs':pairs,
    'seconds':seconds,'tokens_per_second':tokens_generated/seconds,'rows_per_hour':20*3600/seconds,
    'conservative_headroom_bytes':headroom,'passed_exact20':all(x['byte_equal']for x in pairs)}
  save(dest/f'B{b}.json',result);results.append(result)
  if b==1:assert result['passed_exact20'],'Original single reference changed; stop'
 eligible=[x for x in results if x['passed_exact20']and x['conservative_headroom_bytes']>=3*1024**3]
 best=max(x['tokens_per_second']for x in eligible);chosen=min(x['batch_size']for x in eligible if x['tokens_per_second']>=.8*best)
 save(dest/'complete.json',{'utc':utc(),'candidate_batch_size':chosen,'rule':'exact20 and >=3GiB; smallest >=80% maximum measured tokens/s',
    'N_fixed_prompts':20,'not_accuracy_or_steering_effect':True,'plan_sha256':sha(U/'WG_batch_plan.json')})
 pulse('complete',candidate_batch_size=chosen)
if __name__=='__main__':main()
