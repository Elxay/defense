"""Generate frozen old-recipe targets and audited hard-negative targets; no gradients."""
from pathlib import Path
import os,sys,json,hashlib,datetime,time,re,unicodedata
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round8';T=B/'results/style_intervention';T.mkdir(exist_ok=True);sys.path.insert(0,str(B/'src'))
from judge.refusal import new_rule
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='3'and os.environ.get('DEVICE')=='cuda:0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def norm(t):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',t).casefold()).strip()
def atomic(p,x):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def pulse(phase,**kw):atomic(O/'style_targets_live.json',dict(utc=now(),pid=os.getpid(),phase=phase,physical_gpu=3,**kw))
audit=json.loads((O/'style_data_audit.json').read_text());pool=json.loads((O/'style_audited_candidate_pool.json').read_text());assert audit['n_audited_pool']==len(pool)==120 and audit['max_reference_cosine']<.85 and audit['max_other_selected_cosine']<.85 and sha(O/'style_audited_candidate_pool.json')==audit['manifest_sha256']
source=B/'stage136/keep60_seed.py';assert sha(source)=='e7dc6b09cd6f2d6b2f5702a0393c0fc812e7762acba0fde5b884fce36ef56106';text=source.read_text();prefix=text[:text.index('ref_targets=[gen(')]
prefix=prefix.replace('map_location="cpu")','map_location="cpu",weights_only=False)')
# Only path resolution changes; target generation uses the exact old gen function, cache=False and200 cap.
prefix=prefix.replace('"meta-llama/Llama-3.1-8B-Instruct", revision=REV','"/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659", local_files_only=True')
sys.argv=[str(source),'3'];pulse('loading_old_recipe_model');ns={};exec(compile(prefix,str(source),'exec'),ns)
keep=ns['keep'];fit=ns['train_rows'];assert len(keep)==60 and len(fit)==12;cfg=json.loads((B/'configs/keep60_ids.json').read_text())['keep60'];assert {norm(r['text'])for r in keep}=={norm(r['text'])for r in cfg},'old keep recipe differs from frozen keep60'
start=time.monotonic();old=dict(keep=keep,fit=fit,keep_targets=[],ref_targets=[],old_recipe_sha256=sha(source),old_prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),max_new_tokens=200,use_cache=False,model_snapshot='0e9e39f249a16976918f6564b8830bc894c89659',initials={})
for i,r in enumerate(fit):
 old['ref_targets'].append(ns['gen'](r['text'],donor=ns['donor_state']));atomic(T/'old_recipe_targets.partial.json',old);pulse('old_ref_targets',n=i+1,total=12,elapsed_seconds=time.monotonic()-start)
for i,r in enumerate(keep):
 old['keep_targets'].append(ns['gen'](r['text']));atomic(T/'old_recipe_targets.partial.json',old);pulse('old_keep_targets',n=i+1,total=60,elapsed_seconds=time.monotonic()-start)
# Freeze exact CUDA float32 theta initialization for each paired training seed.
for seed in range(3,8):
 ns['torch'].manual_seed(seed);theta=ns['torch'].randn(4096,device='cuda:0');theta=theta/theta.norm()*5.21;arr=theta.detach().cpu().numpy();p=T/f'init_theta_s{seed}.npy';assert not p.exists();ns['np'].save(p,arr);p.chmod(0o444);old['initials'][str(seed)]=dict(file=str(p.relative_to(B)),npy_sha256=sha(p),array_sha256=hashlib.sha256(arr.tobytes()).hexdigest(),rng='CUDA torch.manual_seed(seed), float32 torch.randn4096 -> normalize to5.21')
atomic(T/'old_recipe_targets.json',old)
selected=[];records=[];gen_n=0;newstart=time.monotonic()
for r in pool:
 targets={}
 for side in ['vanilla','adversarial']:
  targets[side]=ns['gen'](r[side]);gen_n+=1;pulse('audited_style_baselines',groups_examined=len(records),groups_selected=len(selected),n_outputs=gen_n,seconds_per_output=(time.monotonic()-newstart)/gen_n)
 bad=any(new_rule(t)for t in targets.values());records.append(dict(id=r['id'],accepted=not bad,baseline_v2={side:new_rule(t)for side,t in targets.items()},target_sha256={side:hashlib.sha256(t.encode()).hexdigest()for side,t in targets.items()}))
 if not bad:selected.append(dict(**r,targets=targets))
 atomic(T/'style_targets.partial.json',dict(items=selected,records=records))
 if len(selected)==60:break
assert len(selected)==60,'insufficient audited nonrefusing groups; no replacement outside audited pool'
final=dict(created_utc=now(),n_groups=60,n_inputs=120,items=selected,records=records,old_targets_file='results/style_intervention/old_recipe_targets.json',old_targets_sha256=sha(T/'old_recipe_targets.json'),audit_file='results/audit/handoff_round8/style_data_audit.json',audit_sha256=sha(O/'style_data_audit.json'),pool_sha256=sha(O/'style_audited_candidate_pool.json'),addendum1_sha256=sha(B/'docs/252_ADDENDUM1_MEAN_CRITERION.md'),v2_sha256=sha(B/'src/judge/refusal.py'),script_sha256=sha(Path(__file__)))
atomic(T/'style_training_targets.json',final)
with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(now()+' STYLE_TRAINING_INPUTS_FROZEN oldtargets/init hashes + audited60groups120targets; before any intervention optimization; finalSHA='+sha(T/'style_training_targets.json')+' oldtargetsSHA='+sha(T/'old_recipe_targets.json')+'\n')
pulse('complete',groups_selected=60,n_outputs=gen_n,training_targets_sha256=sha(T/'style_training_targets.json'));print('TARGETS_COMPLETE',flush=True)
