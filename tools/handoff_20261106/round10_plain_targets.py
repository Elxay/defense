from pathlib import Path
import os,sys,json,hashlib,datetime,time,re
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round10';T=B/'results/plain_arm';assert os.environ.get('CUDA_VISIBLE_DEVICES')=='3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def pulse(phase,**kw):atomic(O/'plain_targets_live.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),physical_gpu=3,phase=phase,**kw))
audit=json.loads((O/'plain_data_audit.json').read_text());pool=json.loads((O/'plain_audited_pool.json').read_text());assert len(pool)==240 and sha(O/'plain_audited_pool.json')==audit['pool_sha256'];assert sha(B/'docs/252_ADDENDUM3_PLAIN_ARM_INTERPOLATION.md')=='e92456d65278081f8b1c6b6acd1b165c8219b4c9a62af0bcbb2e6e58ad852195'
source=B/'stage136/keep60_seed.py';text=source.read_text();prefix=text[:text.index('ref_targets=[gen(')].replace('map_location="cpu")','map_location="cpu",weights_only=False)').replace('"meta-llama/Llama-3.1-8B-Instruct", revision=REV','"/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659", local_files_only=True');sys.argv=[str(source),'3'];pulse('loading_model');ns={};exec(compile(prefix,str(source),'exec'),ns);sys.path.insert(0,str(B/'src'));from judge.refusal import new_rule
rubric=(B/'tools/handoff_20261106/round9_target_completion_rubric.txt').read_text();signature=dict(worker_sha256=sha(Path(__file__)),pool_sha256=sha(O/'plain_audited_pool.json'),rubric_sha256=sha(B/'tools/handoff_20261106/round9_target_completion_rubric.txt'),addendum3_sha256=sha(B/'docs/252_ADDENDUM3_PLAIN_ARM_INTERPOLATION.md'))
progress=T/'target_progress.json';saved=json.loads(progress.read_text())if progress.exists()else dict(signature=signature,records=[],accepted=[]);assert saved['signature']==signature;done={r['id']for r in saved['records']};begin=time.monotonic();fresh=0
def label(request,response):
 prompt=rubric.replace('{request}',request).replace('{response}',response);ids=ns['tok'].apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True,return_tensors='pt').to('cuda:0');ns['mdl'].config.use_cache=True
 with ns['torch'].no_grad():out=ns['mdl'].generate(ids,max_new_tokens=128,do_sample=False,pad_token_id=ns['tok'].eos_token_id)
 ns['mdl'].config.use_cache=False;raw=ns['tok'].decode(out[0][ids.shape[1]:],skip_special_tokens=True)
 try:
  d=json.loads(re.search(r'\{.*\}',raw,re.S).group());assert d['label']in['ANSWER','NONANSWER','UNCERTAIN'];return d
 except Exception:return dict(label='UNCERTAIN',reason='parsefailure',raw=raw)
for r in pool:
 if len(saved['accepted'])>=120:break
 if r['id']in done:continue
 target=ns['gen'](r['text']);z=label(r['text'],target);accept=z['label']=='ANSWER'and not new_rule(target);cap=bool(re.search(r"cannot|can't|couldn't|unable|do not have|don't have|do not know|don't know|no (?:access|information)|not (?:available|possible)|fictional|password|passphrase|contact",target,re.I));record=dict(id=r['id'],request=r['text'],target=target,label=z,accepted=accept,capability_or_fiction_flag=cap,v2=new_rule(target));saved['records'].append(record)
 if accept:saved['accepted'].append(dict(**r,target=target))
 atomic(progress,saved);fresh+=1;spi=(time.monotonic()-begin)/fresh;pulse('generating_and_filtering',groups_examined=len(saved['records']),accepted=len(saved['accepted']),n_fresh=fresh,seconds_per_item=spi);print('PLAIN_TARGET',len(saved['records']),len(saved['accepted']),flush=True)
 if fresh==25:atomic(O/'plain_target_speed25.json',dict(seconds_per_item=spi,n=25,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
assert len(saved['accepted'])==120,'<120 qualifying plain inputs; stop'
final=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),n_inputs=120,items=saved['accepted'],records=saved['records'],signature=signature,audit_sha256=sha(O/'plain_data_audit.json'),addendum3_sha256=signature['addendum3_sha256'],review_limitation='Llama model labels on full targets; GPT followup pending, no human calibration')
atomic(T/'plain_targets_provisional.json',final);pulse('waiting_gpt_followup',accepted=120,examined=len(saved['records']))
