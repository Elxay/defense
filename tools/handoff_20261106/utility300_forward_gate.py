from pathlib import Path
import hashlib,json,datetime,sys,os,inspect
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';sys.path.insert(0,str(R/'tools/handoff_20261106'))
from utility300_injected_forward import injected_prefill_scores
from utility300_scoring import arc_choice

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
key=sys.argv[1];plan=load(U/'ARC_forward_gate_plan.json');assert sha(__file__)==plan['worker_sha256'];assert sha(R/'tools/handoff_20261106/utility300_injected_forward.py')==plan['core_sha256'];assert sha(U/'utility.private/arc200.json')==plan['ARC200_sha256'];spec=plan['models'][key];dest=U/'ARC_forward_gate'/key;dest.mkdir(parents=True,exist_ok=True)
def pulse(phase,**kw):save(dest/'live.json',dict(utc=utc(),pid=os.getpid(),phase=phase,utility_accuracy_read=False,**kw))
pulse('loading');tok=AutoTokenizer.from_pretrained(spec['path'],local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(spec['path'],local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval();rows={r['id']:r for r in load(U/'utility.private/arc200.json')};vectors={}
for c,v in spec['vectors'].items():assert sha(v['path'])==v['sha256'];vectors[c]=np.load(v['path'])
vectors={'alpha0':np.zeros_like(vectors['s3']),**vectors};records=[]
for index,k in enumerate(plan['IDs20']):
 row=rows[k];ids=tok.apply_chat_template([{'role':'user','content':row['prompt']}],add_generation_prompt=True,return_tensors='pt').to('cuda:0');mask=torch.ones_like(ids);text=tok.apply_chat_template([{'role':'user','content':row['prompt']}],add_generation_prompt=True,tokenize=False);options=[]
 for letter in row['candidate_letters']:
  joint=tok(text+letter,add_special_tokens=False).input_ids;assert joint[:ids.shape[1]]==ids[0].tolist();tail=joint[ids.shape[1]:];assert len(tail)==1;options.append(tail[0])
 assert len(set(options))==4
 kwargs=dict(input_ids=ids,attention_mask=mask,position_ids=mask.long().cumsum(-1)-1,use_cache=True)
 if 'logits_to_keep'in inspect.signature(model.forward).parameters:kwargs['logits_to_keep']=1
 elif 'num_logits_to_keep'in inspect.signature(model.forward).parameters:kwargs['num_logits_to_keep']=1
 with torch.inference_mode():raw=model(**kwargs).logits[0,-1,options].float().cpu()
 for c in ['alpha0','s3','random']:
  scores,meta=injected_prefill_scores(model,ids,mask,vectors[c],spec['layer'],options)
  if c=='alpha0':assert meta['rho_runtime']==0;zero_equal=torch.equal(raw,scores)
  state={'count':0};v=torch.as_tensor(vectors[c],dtype=torch.float32)
  def hook(mod,args,out):
   if state['count']:return out
   h=out[0]if isinstance(out,tuple)else out;assert h.shape[1]==ids.shape[1];h=h.clone();h[0,-1]=h[0,-1]+v.to(h.device,h.dtype);state['count']+=1;return (h,)+out[1:]if isinstance(out,tuple)else h
  hd=model.model.layers[spec['layer']].register_forward_hook(hook)
  try:
   with torch.inference_mode():out=model.generate(input_ids=ids,attention_mask=mask,max_new_tokens=1,do_sample=False,pad_token_id=tok.pad_token_id,return_dict_in_generate=True,output_scores=True)
  finally:hd.remove()
  assert state['count']==1;g=out.scores[0][0,options].float().cpu();records.append(dict(id=k,condition=c,metadata=meta,zero_equals_no_hook=zero_equal if c=='alpha0'else None,argmax_forward_equals_generate=arc_choice(scores.tolist())==arc_choice(g.tolist()),candidate_logit_max_abs_difference=float((scores-g).abs().max()),forward_scores_sha256=hashlib.sha256(scores.numpy().tobytes()).hexdigest(),generation_scores_sha256=hashlib.sha256(g.numpy().tobytes()).hexdigest()))
 pulse('checking',completed=index+1,total=20)
passed=all(r['argmax_forward_equals_generate']and(r['zero_equals_no_hook']is not False)for r in records);result=dict(utc=utc(),model=key,N20=20,conditions=3,passed=passed,plan_sha256=sha(U/'ARC_forward_gate_plan.json'),records=records,utility_accuracy_read=False,output_tokens_or_choices_published=False,formal_generation_admitted=False)
save(dest/'result.json',result);pulse('complete',passed=passed);print('PASSED',key,passed,'SHA',sha(dest/'result.json'))
