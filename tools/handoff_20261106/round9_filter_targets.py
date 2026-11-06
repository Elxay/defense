"""Fixed-order task-completion filtering; private texts; no optimization."""
from pathlib import Path
import os,sys,json,hashlib,datetime,time,re
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round9';T=B/'results/style_retrained';CACHE=B/'results/style_intervention'
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='3'and os.environ.get('DEVICE')=='cuda:0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,x):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def pulse(phase,**kw):atomic(O/'target_filter_live.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),phase=phase,physical_gpu=3,**kw))
assert sha(B/'docs/252_ADDENDUM2_RETRAINED_CONTROLS.md')=='493094393b6f2294498c3cf01a449f2b7557f23784530f9e8e002066f56e1896'
source=B/'stage136/keep60_seed.py';text=source.read_text();prefix=text[:text.index('ref_targets=[gen(')].replace('map_location="cpu")','map_location="cpu",weights_only=False)').replace('"meta-llama/Llama-3.1-8B-Instruct", revision=REV','"/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659", local_files_only=True');sys.argv=[str(source),'3'];pulse('loading_model');ns={};exec(compile(prefix,str(source),'exec'),ns)
sys.path.insert(0,str(B/'src'));from judge.refusal import new_rule
rubric=(B/'tools/handoff_20261106/round9_target_completion_rubric.txt').read_text();signature=dict(rubric_sha256=sha(B/'tools/handoff_20261106/round9_target_completion_rubric.txt'),worker_sha256=sha(Path(__file__)),addendum2_sha256=sha(B/'docs/252_ADDENDUM2_RETRAINED_CONTROLS.md'),pool_sha256=sha(B/'results/audit/handoff_round8/style_audited_candidate_pool.json'))
old=json.loads((CACHE/'style_training_targets.json').read_text());existing={r['id']:r for r in old['items']};v2excluded={r['id']for r in old['records']if not r['accepted']};pool=json.loads((B/'results/audit/handoff_round8/style_audited_candidate_pool.json').read_text())
progress=T/'target_filter_progress.json';saved=json.loads(progress.read_text())if progress.exists()else dict(signature=signature,records=[],accepted=[]);assert saved['signature']==signature;completed={r['id']for r in saved['records']};begin=time.monotonic()
def label(request,response):
 q=rubric.replace('{request}',request).replace('{response}',response);ids=ns['tok'].apply_chat_template([{'role':'user','content':q}],add_generation_prompt=True,return_tensors='pt').to('cuda:0');ns['mdl'].config.use_cache=True
 with ns['torch'].no_grad():out=ns['mdl'].generate(ids,max_new_tokens=128,do_sample=False,pad_token_id=ns['tok'].eos_token_id)
 ns['mdl'].config.use_cache=False;raw=ns['tok'].decode(out[0][ids.shape[1]:],skip_special_tokens=True)
 try:
  d=json.loads(re.search(r'\{.*\}',raw,re.S).group());assert d['label']in ['ANSWER','NONANSWER','UNCERTAIN'];return d
 except Exception:return dict(label='UNCERTAIN',reason='unparseable structured model judgment',raw=raw)
for r in pool:
 if len(saved['accepted'])>=60:break
 if r['id']in completed:continue
 if r['id']in v2excluded:saved['records'].append(dict(id=r['id'],accepted=False,reason='historical_v2_positive_targets',labels=None));atomic(progress,saved);continue
 targets=existing[r['id']]['targets']if r['id']in existing else{side:ns['gen'](r[side])for side in ['vanilla','adversarial']}
 labels={side:label(r[side],targets[side])for side in ['vanilla','adversarial']};accepted=all(z['label']=='ANSWER'for z in labels.values())and not any(new_rule(t)for t in targets.values())
 cap=re.compile(r"cannot|can't|unable|do not have|don't have|no (?:access|information)|not (?:available|possible)|fictional|password|passphrase|contact",re.I)
 record=dict(id=r['id'],accepted=accepted,labels=labels,targets=targets,requests={side:r[side]for side in ['vanilla','adversarial']},capability_or_fiction_flag=any(cap.search(t)for t in targets.values()),v2={side:new_rule(t)for side,t in targets.items()});saved['records'].append(record)
 if accepted:saved['accepted'].append(dict(**r,targets=targets))
 atomic(progress,saved);pulse('filtering',groups_examined=len(saved['records']),groups_accepted=len(saved['accepted']),seconds_per_examined=(time.monotonic()-begin)/len(saved['records']));print('FILTER',len(saved['records']),len(saved['accepted']),r['id'],accepted,flush=True)
assert len(saved['accepted'])==60,'insufficient reviewed audited groups; stop without relaxing selection'
final=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),n_groups=60,n_inputs=120,items=saved['accepted'],records=saved['records'],audit_sha256=sha(B/'results/audit/handoff_round8/style_data_audit.json'),old_targets_sha256=sha(CACHE/'old_recipe_targets.json'),addendum2_sha256=signature['addendum2_sha256'],rubric_sha256=signature['rubric_sha256'],review_model='meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659',reviewer_limitation='model completion labels without human calibration; GPT follow-up review pending')
atomic(T/'style_targets_provisional.json',final);pulse('waiting_gpt_followup_review',groups_accepted=60,groups_examined=len(saved['records']));print('PROVISIONAL_COMPLETE',flush=True)
