"""Benign deterministic translation interface gate and instruction backtranslation diagnostic only."""
from pathlib import Path
import json,hashlib,datetime,time,os,sys
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
from language300_local_translation import detect_reply_language
R=Path('/home/dell/Def');U=R/'results/audit/unified300'
def L(p):return json.loads(p.read_text())
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');q.replace(p)
P=L(U/'translation_execution_20261111_plan.json');plan=L(U/'language_preprocessing_plan.json');O=U/'translation_execution_20261111';assert H(__file__)==P['worker_sha256'];assert H(U/'language_preprocessing_plan.json')==P['language_plan_sha256'];assert os.environ['CUDA_VISIBLE_DEVICES']=='2'
assets=L(U/'translator_Qwen3_asset_manifest.json');modelpath=Path(plan['runtime_model_path']);save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='verifying_assets'))
for n,h in assets['files_sha256'].items():assert H(modelpath/n)==h,n
tok=AutoTokenizer.from_pretrained(modelpath,local_files_only=True);model=AutoModelForCausalLM.from_pretrained(modelpath,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval()
rows=L(U/'translation_diagnostic_inputs.private.json');assert H(U/'translation_diagnostic_inputs.private.json')==P['inputs_sha256'];fixtures=L(U/'translation_benign20.json');assert H(U/'translation_benign20.json')==P['fixtures_sha256']
def translate(text):
 torch.manual_seed(plan['translation_seed']);msgs=[{'role':'system','content':plan['system_text']},{'role':'user','content':text}];ids=tok.apply_chat_template(msgs,add_generation_prompt=True,return_tensors='pt',enable_thinking=False).to('cuda:0');n=ids.shape[1];assert n+plan['max_new_tokens']<=model.config.max_position_embeddings
 start=time.monotonic()
 with torch.inference_mode():out=model.generate(input_ids=ids,attention_mask=torch.ones_like(ids),max_new_tokens=plan['max_new_tokens'],do_sample=False,pad_token_id=tok.eos_token_id)
 tail=out[0,n:];textout=tok.decode(tail,skip_special_tokens=True);eos=model.generation_config.eos_token_id;eos={eos}if isinstance(eos,int)else set(eos or[]);finished=bool(len(tail)and int(tail[-1])in eos)
 return dict(text=textout,text_sha256=hashlib.sha256(textout.encode()).hexdigest(),input_ids_sha256=hashlib.sha256(json.dumps(ids[0].tolist()).encode()).hexdigest(),new_tokens=len(tail),eos=finished,truncated=len(tail)>=plan['max_new_tokens']and not finished,seconds=time.monotonic()-start,output_language=detect_reply_language(textout,plan['language_seed']))
checks=[]
for i,r in enumerate(fixtures):
 save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='benign20_repeatability_gate',completed=i,total=20));a=translate(r['text']);b=translate(r['text']);save(O/'gate.private'/f'{i:02d}.json',dict(id=r['id'],first=a,second=b));checks.append(dict(id=r['id'],byte_equal=a['text']==b['text'],nonempty=bool(a['text'].strip()),not_truncated=not a['truncated'],language=a['output_language']['language'],input_ids_sha256=a['input_ids_sha256']))
passed=all(x['byte_equal']and x['nonempty']and x['not_truncated']for x in checks);save(O/'benign20_gate.json',dict(utc=utc(),passed=passed,N=20,exact=sum(x['byte_equal']for x in checks),checks=checks,all_asset_files_verified=True,no_fidelity_accuracy_claim=True,plan_sha256=H(U/'translation_execution_20261111_plan.json')));assert passed,'Benign replay interface failed; diagnostic not started'
start=time.monotonic();completed=0
for r in rows:
 p=O/'backtranslation.private'/r['language']/f"{r['id']:04d}.json"
 if p.exists():completed+=1;continue
 save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='instruction_backtranslation',language=r['language'],completed=completed,total=2200,rows_per_hour=completed/max(time.monotonic()-start,1)*3600))
 try:z=translate(r['text']);value=dict(id=r['id'],language=r['language'],source_sha256=r['source_sha256'],base_sha256=r['base_sha256'],translation=z,error=None)
 except Exception as e:value=dict(id=r['id'],language=r['language'],source_sha256=r['source_sha256'],base_sha256=r['base_sha256'],translation=None,error=type(e).__name__)
 save(p,value);completed+=1
save(O/'all_generation_complete.json',dict(utc=utc(),N=completed,seconds=time.monotonic()-start,plan_sha256=H(U/'translation_execution_20261111_plan.json'),primary_model_outputs_read=False,interpretation='instruction translation diagnostic; no reply fidelity claim; no threshold or scope decisions'))
save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='translation_complete_embedding_summary_pending',completed=completed,total=2200))
