from pathlib import Path
from types import SimpleNamespace,MethodType
import os,sys,json,hashlib,datetime,time,ast,re
from typing import List
import torch,transformers
from transformers import AutoTokenizer,AutoModelForCausalLM
from accelerate.utils import find_executable_batch_size
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';D=U/'score_diagnostic36';lease=Path(os.environ['DEF_LEASE_DIR'])
L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'rating36_plan_v2.json');assert H(__file__)==P['worker_sha256'];assert H(D/'inputs.private.json')==P['private_input_sha256'];spec=L(U/'S1b_PAIR_progressive_v1.json');mp=Path(spec['role_model_path']);assert os.environ['CUDA_VISIBLE_DEVICES']=='0'
for n,h in spec['assets_sha256']['role'].items():assert H(mp/n)==h
base=R/'repos/HarmBench/baselines/pair';assert H(base/'judges.py')==P['judge_source_sha256'];assert H(base/'language_models.py')==spec['source_sha256']['repos/HarmBench/baselines/pair/language_models.py']
def function(path,name,cls):
 t=ast.parse(path.read_text());c=next(x for x in t.body if isinstance(x,ast.ClassDef) and x.name==cls);n=next(x for x in c.body if isinstance(x,ast.FunctionDef) and x.name==name);env=dict(torch=torch,find_executable_batch_size=find_executable_batch_size,re=re,List=List);exec(compile(ast.Module(body=[n],type_ignores=[]),str(path),'exec'),env);return env[name]
parse=function(base/'judges.py','process_output','JudgeBase');hf_batch=function(base/'language_models.py','batch_generate_bs','HuggingFace');hf_generate=function(base/'language_models.py','batched_generate','HuggingFace');save(D/'CPU_preflight36_v2.json',dict(utc=utc(),three_source_functions_compiled=True,parser10=parse(None,'Rating: [[10]]'),parser_failure_fallback=parse(None,'unparseable')));tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();core=SimpleNamespace(model=model,tokenizer=tok,eos_token_ids=[tok.eos_token_id,tok.encode('}',add_special_tokens=False)[0]],generation_batch_size=32);core.batch_generate_bs=MethodType(hf_batch,core);generate=MethodType(hf_generate,core)
inputs=L(D/'inputs.private.json');assert len(inputs['positions'])==264;start=time.monotonic();groups=inputs['groups'];positions=inputs['positions']
for gi,g in enumerate(groups):
 p=D/'groups.private'/(g['key']+'.json')
 if p.exists():continue
 assert hashlib.sha256(json.dumps(g['convs']).encode()).hexdigest()==g['original_request_sha256'];core.generation_batch_size=g['generation_batch_size'];tick=time.monotonic();t0=utc();raw=generate(g['convs'],max_n_tokens=5,temperature=0.);seconds=time.monotonic()-tick;assert len(raw)==len(g['convs']);parsed=[]
 for s in raw:
  full='Rating: [['+s;m=re.search(r'\[\[(\d+)\]\]?',full);score=parse(None,full);parsed.append(dict(continuation=s,parser_input=full,parse_success=m is not None,score=score,score_in_1_10=1<=score<=10))
 save(p,dict(utc=utc(),started_utc=t0,group=g['key'],id=g['id'],iteration=g['iteration'],N=len(raw),seconds=seconds,requested_original_B=g['generation_batch_size'],actual_B=core.generation_batch_size,request_sha256=g['request_sha256'],original_request_sha256=g['original_request_sha256'],outputs=parsed,worker_sha256=H(__file__),plan_sha256=H(U/'rating36_plan_v2.json')))
 save(lease/'live.json',dict(utc=utc(),phase='raw_score_replay',groups_completed=gi+1,total_groups=len(groups),N_requested_positions=264,covered_outputs=sum(len(x['convs']) for x in groups[:gi+1]),elapsed_seconds=time.monotonic()-start))
out=[];wave=[]
for r in positions:
 g=L(D/'groups.private'/(r['group']+'.json'));v=g['outputs'][r['batch_position']];gp=R/r['source_record_relative'];assert H(gp)==r['source_record_sha256'];source=L(gp);out.append(dict(**r,**v,source_group_sha256=H(D/'groups.private'/(r['group']+'.json')),historical_score_reproduced=v['score']==r['original_score'],batch_exact=g['actual_B']==g['requested_original_B']))
 prompt=source['prompt'];response=source['response'];behavior=source['behavior'];wave.append(dict(id=f"{r['id']}:{r['kind']}",model='qwen',family='PAIR_internal_rating_diagnostic36',condition=r['kind'],prompt=prompt,response=response,behavior=behavior,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),response_sha256=hashlib.sha256(response.encode()).hexdigest(),behavior_sha256=hashlib.sha256(behavior.encode()).hexdigest(),generation_sha256=H(gp),preprocessing_sha256=None))
save(D/'requested_raw.private.json',dict(utc=utc(),rows=out,N=264));W=U/'score_waves/PAIR_internal_rating_diagnostic36';save(W/'inputs.private.json',wave);save(W/'manifest.json',dict(utc=utc(),N=264,judges=['SORRY'],inputs_sha256=H(W/'inputs.private.json'),scope='SORRY on same saved internal alpha0 completions; no new generation or protected effects',raw_ratings_sha256=H(D/'requested_raw.private.json')))
save(D/'raw_complete.json',dict(utc=utc(),N_requested=264,N_groups=len(groups),N_covered_outputs=sum(len(g['convs']) for g in groups),all_full_original_request_SHA_matched=True,elapsed_seconds=time.monotonic()-start,raw_records_sha256=H(D/'requested_raw.private.json'),torch=torch.__version__,transformers=transformers.__version__,device_uuid=str(torch.cuda.get_device_properties(0).uuid),SORRY_wave_manifest_sha256=H(W/'manifest.json')))
