from pathlib import Path
import json,hashlib,datetime,shutil,subprocess,fcntl
from transformers import AutoTokenizer
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';G=R/'prereg_repo';D=R/'results/audit/sorry296/downloads.private/sorry-bench-202503'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()
def rows(p):return [json.loads(x)for x in p.read_text().splitlines()]
families=['base','deepinception','refusal_suppression','logical_appeal','authority_endorsement','misrepresentation','evidence-based_persuasion','expert_endorsement','prefix_P1','prefix_P2'];base=rows(D/'question.jsonl');byid={r['question_id']:r for r in base};fixed=load(U/'fixed_texts.private.json');old=load(U/'static_render_manifest.json');S=load(U/'S1a_manifest.json');private={};models={};sources={'base':D/'question.jsonl'}
for family in families:
 if family not in ['base','deepinception','refusal_suppression','prefix_P1','prefix_P2']:sources[family]=D/f'question_{family}.jsonl'
for family,p in sources.items():assert sha(p)==old['source_sha256'][family]
for model,card in [('llama',2),('qwen',3)]:
 spec=S['models'][model];tok=AutoTokenizer.from_pretrained(spec['model_path'],local_files_only=True);private[model]={};plans={};B=spec['long_generation_batch_size'];assert B==(8 if model=='llama' else 4)
 for family in families:
  source=rows(sources[family]) if family in sources else base;record=[];expected={r['id']:r for r in old['models'][model]['families'][family]['rows']}
  for row in source:
   k=row['question_id'];behavior=byid[k]['turns'][0];prompt=row['turns'][0];prefill=''
   if family=='deepinception':prompt=fixed['deep_template'].format(instruction=behavior)
   elif family=='refusal_suppression':prompt=fixed['refusal_suppression']+'\n\n'+behavior
   native=tok.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True)
   if family.startswith('prefix_'):
    prefill=fixed['prefill'];render=tok.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True,tokenize=False);ids=tok(render+prefill,add_special_tokens=False).input_ids;assert ids[:len(native)]==native;position=len(ids)-1 if family=='prefix_P1' else len(native)-1
   else:ids=native;position=len(ids)-1
   assert digest(ids)==expected[k]['input_ids_sha256']
   if 'injection_position_zero_based' in expected[k]:assert position==expected[k]['injection_position_zero_based']
   record.append(dict(id=k,prompt=prompt,behavior=behavior,prefill=prefill,input_ids=ids,input_ids_sha256=digest(ids),position=position,native_prompt_len=len(native),prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),behavior_sha256=hashlib.sha256(behavior.encode()).hexdigest()))
  ordered=sorted(record,key=lambda r:(len(r['input_ids']),hashlib.sha256(('20261240:'+str(r['id'])).encode()).hexdigest()));IDs=[str(r['id'])for r in ordered];private[model][family]=record;plans[family]=dict(N=440,ordered_IDs=IDs,batches=[IDs[i:i+B]for i in range(0,440,B)],gate_selected20_IDs=IDs[:20],prefix_position_gate_required=family.startswith('prefix_'),input_ids_map_sha256=hashlib.sha256(json.dumps({str(r['id']):r['input_ids_sha256']for r in record},sort_keys=True).encode()).hexdigest())
 models[model]=dict(model_path=spec['model_path'],physical_gpu=card,layer=spec['layer'],batch_size=B,asset_interface_sha256=spec['asset_interface_sha256'],position_check_vector_path=spec['learned_vectors']['s3']['path'],position_check_vector_sha256=spec['learned_vectors']['s3']['file_sha256'],families=plans)
p=U/'static_alpha0_inputs.private.json';assert not p.exists();p.write_text(json.dumps(private,indent=2)+'\n');plan=U/'static_alpha0_execution_plan.json';assert not plan.exists();plan.write_text(json.dumps(dict(utc_frozen=utc(),stage='S3a alpha0 only, independent of calibration choice',S1a_manifest_sha256=sha(U/'S1a_manifest.json'),addendum4_sha256=sha(R/'docs/300_ADDENDUM4_LANGUAGE_BATCH_REGRESSION_AND_SEARCH_TIERS.md'),worker_sha256=sha(T/'unified300_static_alpha0.py'),batch_core_sha256=sha(T/'batched_injection300.py'),private_input_sha256=sha(p),source_sha256={n:sha(p)for n,p in sources.items()},fixed_texts_sha256=sha(U/'fixed_texts.private.json'),static_render_manifest_sha256=sha(U/'static_render_manifest.json'),family_order=families,models=models,condition='alpha0',max_new_tokens=2400,greedy=True,gate='same full-family batch membership, no-hook vs zero-hook first20; all covered outputs equal; not batch-vs-single equivalence',read_lock='generation and judge caches only; no primary label/effect reads',encoding_language_not_admitted=True,nonzero_not_admitted=True,main_outputs_before_plan=0),indent=2)+'\n')
launchers=[]
for model,card in [('llama',2),('qwen',3)]:
 f=T/f'launch300_static_alpha0_{model}.sh';assert not f.exists();f.write_text(f'''#!/usr/bin/env bash
set -euo pipefail
source /data/HZX/Def/night/launch.sh
exec 201>/data/HZX/Def/logs/idle_gpu{card}.lock
flock -n 201 || exit 73
unset NOGPU
export DEVICE=cuda:{card}
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES={card} DEVICE=cuda:0 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True /home/kemove/anaconda3/envs/HZX_GLA/bin/python /data/HZX/Def/tools/handoff_20261106/unified300_static_alpha0.py {model} {card}
''');launchers.append(f)
master=R/'docs/300_UNIFIED_PROTOCOL.md';text=master.read_text();text+='\n追加4前置冻结SHA '+sha(R/'docs/300_ADDENDUM4_LANGUAGE_BATCH_REGRESSION_AND_SEARCH_TIERS.md')+'：语言链、主测试后路径回归与搜索440/220/88见追加4。S3a alpha0只需S1a+家族执行门，不依赖alpha选择；非零S3b仍锁。原220预测超预算分支由三档及预算不可行分支取代，10pilot保留所有档。\n';master.write_text(text)
active=load(U/'active_protocol.json');active.update(updated_utc=utc(),stage='S3a_alpha0_and_S2b_read_ready',master_candidate_sha256=sha(master),new_test_generation_allowed=True,allowed_main_conditions=['alpha0'],allowed_main_families=families,static_alpha0_execution_plan_sha256=sha(plan),main_label_or_effect_reads_allowed=False,search_outputs_allowed=False,language_encoding_execution_locked=True);(U/'active_protocol.json').write_text(json.dumps(active,indent=2)+'\n')
line=utc()+' freeze/activate S3a alpha0 before target outputs; LlamaB8/QwenB4 fixed. Same-batch nohook/zero20, prefix separate position proof; cache-only no main labels/effects. Other phases locked. planSHA='+sha(plan)+'\n';files=[plan,T/'unified300_static_alpha0.py',Path(__file__),*launchers,master,U/'active_protocol.json']
for n in ['OPS_LOG','PREREG_LOG.txt']:
 with (R/'docs'/n).open('a')as f:f.write(line)
 files.append(R/'docs'/n)
with (R/'logs/prereg_publish.lock').open('a')as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip();rels=[]
 for f in files:
  rel=f.relative_to(R);dst=G/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst);rels.append(str(rel))
 subprocess.run(['git','add','--',*rels],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Freeze alpha0 family gates and fixed-batch cache generation before baseline startup'],cwd=G,check=True);subprocess.run(['git','push','origin','HEAD'],cwd=G,check=True)
print('STATIC_PLAN_SHA',sha(plan))
for model in ['llama','qwen']:subprocess.run(['bash','-c','nohup bash /data/HZX/Def/tools/handoff_20261106/launch300_static_alpha0_'+model+'.sh > /data/HZX/Def/logs/unified300_static_alpha0_'+model+'.log 2>&1 < /dev/null &'],check=True)
