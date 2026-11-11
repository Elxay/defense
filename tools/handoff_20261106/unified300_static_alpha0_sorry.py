"""Canonical SORRY alpha0 cache writer, never aggregates or unlocks reads."""
from pathlib import Path
import json,hashlib,datetime,os,sys,time,importlib.util
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';O=U/'static_alpha0_SORRY'
def H(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(16*1024*1024),b''):h.update(b)
 return h.hexdigest()
def L(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(o,indent=2)+'\n');q.replace(p)
P=L(U/'static_alpha0_SORRY_execution_plan.json');assert H(__file__)==P['worker_sha256'];assert os.environ['CUDA_VISIBLE_DEVICES']=='0';assert H(U/'static_alpha0_inputs.private.json')==P['generation_inputs_sha256'];A=L(R/'results/audit/sorry296/judge_download_complete.json');mp=Path(A['local_path'])
for n,v in A['files'].items():assert H(mp/n)==v['sha256']
parser=R/'results/audit/sorry296/official_template_parser.py';promptsfile=R/'repos/SORRY-Bench/data/sorry_bench/judge_prompts.jsonl';assert H(parser)==P['parser_sha256'];assert H(promptsfile)==P['prompt_template_sha256'];spec=importlib.util.spec_from_file_location('official_sorry_main',parser);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.json=json
save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='loading',physical_gpu=0,main_effects_aggregated=False))
from vllm import LLM,SamplingParams
model=LLM(model=str(mp),tokenizer=str(mp),dtype='bfloat16',disable_custom_all_reduce=True,tensor_parallel_size=1,enforce_eager=True,gpu_memory_utilization=.85,hf_overrides={'head_dim':128},max_model_len=16384);params=SamplingParams(temperature=0,n=1,max_tokens=1024);tok=model.get_tokenizer()
def dialogs(rows):
 return mod.apply_sorry_bench_judge_template([{'question_id':r['id'],'turns':[r['behavior']]}for r in rows],[{'choices':[{'turns':[r['response']]}]}for r in rows],'ft-mistral-7b-instruct-v0.2','base',promptsfile)
def score(ds):return [(x.outputs[0].text.strip(),len(x.prompt_token_ids),len(x.outputs[0].token_ids))for x in model.generate(ds,params,use_tqdm=False)]
human=L(U/'human_inputs.private.json')[:20];test=[dict(id=r['id'],behavior=r['prompt'],response=r['response'])for r in human];ds,tag=dialogs(test);vals=[]
for begin in range(0,20,P['batch_size']):vals+=score(ds[begin:begin+P['batch_size']])
checks=[dict(id=r['id'],byte_equal=z[0]==L(U/'SORRY_scores'/(r['id']+'.json'))['output'],actual_output_sha256=hashlib.sha256(z[0].encode()).hexdigest())for r,z in zip(human,vals)];passed=all(c['byte_equal']for c in checks);save(O/'reference20.json',dict(utc=utc(),passed=passed,N=20,exact=sum(c['byte_equal']for c in checks),checks=checks));assert passed,'Fresh canonical judge reference gate failed; no main scores written'
inputs=L(U/'static_alpha0_inputs.private.json');old=L(U/'static_alpha0_execution_plan.json');tasks=[(m,f)for m in ['llama','qwen']for f in old['family_order']];done=0
for m,f in tasks:
 folder=O/'tasks'/m/f;data={r['id']:r for r in inputs[m][f]};marker=U/'static_alpha0'/m/f/'generation_complete.json';assert L(marker)['N']==440;rows=[]
 for k in sorted(data):
  r=data[k];gpath=U/'static_alpha0'/m/f/'generation.private'/f'{k:04d}.json';g=L(gpath);assert g['signature']['condition']=='alpha0';response=r['prefill']+g['result']['text'];assert hashlib.sha256(response.encode()).hexdigest()==g['full_response_sha256'];rows.append(dict(id=k,behavior=r['behavior'],response=response,generation_sha256=H(gpath),prompt_sha256=r['prompt_sha256'],response_sha256=g['full_response_sha256'],input_ids_sha256=r['input_ids_sha256']))
 ds,tag=dialogs(rows)
 for begin in range(0,440,P['batch_size']):
  group=rows[begin:begin+P['batch_size']];texts=ds[begin:begin+P['batch_size']];paths=[folder/'scores.private'/f"{r['id']:04d}.json"for r in group]
  if all(p.exists()for p in paths):continue
  lengths=[len(tok.encode(t))for t in texts];valid=[i for i,n in enumerate(lengths)if n<=16384];z=score([texts[i]for i in valid])if valid else[];answers={i:v for i,v in zip(valid,z)}
  for i,(r,path)in enumerate(zip(group,paths)):
   raw,n,nt=answers[i]if i in answers else('',lengths[i],0);parsed=mod.extract_content(tag,raw)if i in answers else None;label=int(parsed)if parsed in [0,1]else None
   value=dict(id=r['id'],label=label,raw_parsed=parsed,output=raw,input_tokens=n,new_tokens=nt,invalid_reason='input_over_16384'if i not in answers else'parse_invalid'if label is None else None,signature=dict(plan_sha256=H(U/'static_alpha0_SORRY_execution_plan.json'),model=m,family=f,condition='alpha0',generation_sha256=r['generation_sha256'],prompt_sha256=r['prompt_sha256'],response_sha256=r['response_sha256'],input_ids_sha256=r['input_ids_sha256'],judge_backend='vllm_0.6.6_bf16_eager_innet_GPU0',question_policy='base English instruction as official mutation evaluator',batch_ids=[r['id']for r in group]))
   if path.exists():assert L(path)==value
   else:save(path,value)
  save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='cache_only_scoring',model=m,family=f,completed_rows=begin+len(group),total=440,completed_tasks=done,total_tasks=20,main_effects_aggregated=False))
 save(folder/'complete.json',dict(utc=utc(),N=440,model=m,family=f,condition='alpha0',plan_sha256=H(U/'static_alpha0_SORRY_execution_plan.json'),score_record_sha256={str(r['id']):H(folder/'scores.private'/f"{r['id']:04d}.json")for r in rows},main_effects_aggregated=False));done+=1
save(O/'all_complete.json',dict(utc=utc(),tasks=done,rows=8800,no_main_labels_or_effects_aggregated=True));save(O/'live.json',dict(utc=utc(),pid=os.getpid(),phase='complete_cache_only',tasks=done,main_effects_aggregated=False))
