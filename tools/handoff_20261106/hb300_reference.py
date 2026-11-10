"""S0 held-out human reference; verified existing HF classifier, no target generation."""
from pathlib import Path
import ast, datetime, hashlib, json, os, socket, time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
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
 plan=load(U/'human_reference_plan.json');assert sha(Path(__file__))==plan['workers']['HB'];assert os.environ['CUDA_VISIBLE_DEVICES']=='2,3';assert sha(U/'human_inputs.private.json')==plan['input_sha256']
 manifest=R/'results/audit/pair500/hb_judge_model_sha256.json';assert sha(manifest)==plan['HB_model_manifest_sha256'];m=load(manifest);modelpath=Path(m['model_root'])
 def pulse(phase,**kw):save(U/'HB_live.json',dict(utc=utc(),pid=os.getpid(),host=socket.gethostname(),physical_gpus=[2,3],backend='hf_innet',phase=phase,aggregate_read=False,**kw))
 for name,v in m['files'].items():assert sha(modelpath/name)==v['sha256'];pulse('verifying_assets',last_verified=name)
 tok=AutoTokenizer.from_pretrained(modelpath,local_files_only=True)
 mdl=AutoModelForCausalLM.from_pretrained(modelpath,torch_dtype=torch.bfloat16,device_map='auto',max_memory={0:'13GiB',1:'13GiB','cpu':'0GiB'},local_files_only=True).eval()
 assert not{'cpu','disk'}&set(mdl.hf_device_map.values())
 source=R/'night/hf_judge_round2_reference.py';assert sha(source)==plan['HB_legacy_functions_sha256'];tree=ast.parse(source.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in['p_yes','judge_text']]
 env=dict(tok=tok,mdl=mdl,torch=torch,CLS=(R/'night/cls_prompt.txt').read_text());exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),env)
 refs=load(R/'results/hfjudge/JUDGE_HF_wjb_a0_innet_round2')['items'];gens=load(R/'results/audit/WJB_A0_merged.json');beh={r['id']:r['vanilla']for r in load(R/'configs/stage0_data/wjb300.json')};keys=sorted(refs,key=lambda k:abs(refs[k]['p_yes']-.5))[:20];pairs=[]
 for k in keys:
  value=env['judge_text'](beh[k],gens[k]['text'])[0];pairs.append({'id':k,'reference':refs[k]['p_yes'],'observed':value,'abs_delta':abs(value-refs[k]['p_yes'])if value is not None else None})
 passed=all(p['abs_delta']is not None and p['abs_delta']<.001 for p in pairs)and sum(.05<=p['reference']<=.95 for p in pairs)>=8
 save(U/'HB_gate20.json',dict(utc=utc(),passed=passed,pairs=pairs,backend='hf_innet',purpose='existing hardware/function fidelity; main scores use official raw Yes/No classifier below'));assert passed
 src=R/'repos/HarmBench/eval_utils.py';assert sha(src)==plan['HB_prompt_source_sha256'];tree=ast.parse(src.read_text());nodes=[n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='LLAMA2_CLS_PROMPT'for t in n.targets)];scope={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'),scope);template=scope['LLAMA2_CLS_PROMPT']['prompt']
 yes,no=[tok.encode(s,add_special_tokens=False)for s in['Yes','No']];assert len(yes)==len(no)==1
 rows=load(U/'human_inputs.private.json');assert len(rows)==4400
 sig=dict(plan_sha256=sha(U/'human_reference_plan.json'),worker_sha256=sha(Path(__file__)),input_sha256=plan['input_sha256'],backend='hf_innet_full_human_response',physical_gpus=[2,3])
 start=time.monotonic()
 for i,r in enumerate(rows,1):
  p=U/'HB_scores'/(r['id']+'.json')
  if p.exists():assert load(p)['signature']==sig;continue
  inp=tok(template.format(behavior=r['prompt'],generation=r['response']),return_tensors='pt').to(mdl.device);n=inp.input_ids.shape[1]
  assert n<=2048,'S0 preflight expected no overflow; stop without changing length treatment'
  with torch.inference_mode():z=mdl.generate(**inp,max_new_tokens=1,do_sample=False,pad_token_id=tok.eos_token_id,return_dict_in_generate=True,output_logits=True)
  raw=tok.decode(z.sequences[0,-1:],skip_special_tokens=True).strip().lower();label={'yes':1,'no':0}.get(raw);prob=float(torch.softmax(z.logits[0][0,[yes[0],no[0]]].float(),dim=-1)[0]);save(p,dict(id=r['id'],label=int(prob>.5)if label is not None else None,p_yes=prob,decoded_label=label,input_tokens=n,signature=sig))
  if i%10==0:pulse('scoring_human_test',n=i,total=4400,seconds_per_case=(time.monotonic()-start)/i)
 save(U/'HB_complete.json',dict(utc=utc(),n=4400,aggregate_read=False));pulse('complete_waiting_other_judges',n=4400,total=4400)
if __name__=='__main__':main()
