"""Aggregate the two fixed same-alpha endpoints only after the original unified read."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import numpy as np
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round12';R=B/'results/style_retrained';N='/home/dell/Def/results/audit/handoff_round12/'
sys.path.insert(0,str(B/'src'));from judge.refusal import new_rule
def now():return datetime.datetime.now(datetime.timezone.utc)
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');q.replace(p)
def pulse(phase,**kw):save(O/'same_alpha_analysis_live.json',dict(utc=now().isoformat(),pid=os.getpid(),phase=phase,**kw))
primary=B/'results/audit/handoff_round9/intervention_complete_results.json'
try:
 while True:
  assert now()<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc),'deadline'
  statuses={}
  for s in (3,5):
   cp=subprocess.run(['ssh','-o','ConnectTimeout=8','node01','cat',N+f'same_alpha_s{s}_launcher_live.json'],capture_output=True,text=True,timeout=12)
   statuses[str(s)]=json.loads(cp.stdout) if cp.returncode==0 else {'phase':'unavailable'}
  assert all(x['phase']!='failed' for x in statuses.values()),'a supplementary worker failed'
  ready=primary.exists()
  if ready and all(x['phase']=='complete' for x in statuses.values()):break
  pulse('waiting_both600_and_original_read',node01=statuses,original_unified_read_complete=ready);time.sleep(30)
 add=B/'docs/252_ADDENDUM5_SAME_ALPHA_PAIRS.md';m=load(R/'alpha_matches_frozen.json')
 pairs=B/'configs/stage0_data/wjb_benign246_pairs300.json';base_file=B/'results/audit/WJB_BENIGN246_alpha0.json';base=load(base_file)['items']
 ids=[x['id'] for x in load(pairs) if not any(new_rule(base[x['id']+'|'+s]['text']) for s in ('vanilla','adversarial'))];assert len(ids)==292
 subs={}
 for s in (3,5):
  n=f'same_alpha_s{s}_pairs600.private.json';local=O/n
  subprocess.run(['rsync','-a','node01:'+N+n,str(local)],check=True,timeout=60);subs[s]=local
 with (B/'docs/PREREG_LOG.txt').open('a') as f:f.write(now().isoformat()+' DOC252_SAME_ALPHA_ACTUAL_READ both fixed s3/s5 complete after original unified read; no primary decision changes.\\n'.replace('\\n','\n'))
 indices=np.random.default_rng(202611070405).integers(0,len(ids),(5000,len(ids)));report=[]
 for seed in (3,5):
  D=R/f'eval_s{seed}';entries=[];vec=[]
  for label,alpha,file in [('control',1.,D/'control_a1_pairs600.json'),('wrapped_same_alpha',1.,subs[seed]),('wrapped_ASR_matched',1.5,D/'treatment_a1.5_pairs600.json')]:
   d=load(file);z=d['items'];assert len(z)==600 and d['metadata']['alpha']==alpha
   if label=='wrapped_same_alpha':assert d['metadata']['addendum5_sha256']==sha(add) and d['metadata']['manifest_sha256']==sha(pairs)
   v,a=[np.array([new_rule(z[i+'|'+side]['text']) for i in ids],int) for side in ('vanilla','adversarial')]
   asr=m['rows'][str(seed)]['control_asr_pct'] if label=='control' else next(g['asr_pct'] for g in m['grid'] if g['seed']==seed and g['alpha']==alpha)
   entries.append(dict(condition=label,alpha=alpha,norm=alpha*5.21,val70_asr_pct=asr,vanilla=int(v.sum()),adversarial=int(a.sum()),DD_pp=float((a-v).mean()*100),file=str(file.relative_to(B)),sha256=sha(file)));vec.append(a-v)
  def interval(x):return dict(mean_pp=float(x.mean()*100),paired_vanilla_bootstrap95_pp=(np.quantile(x[indices].mean(1),[.025,.975])*100).tolist())
  report.append(dict(seed=seed,conditions=entries,same_alpha_improvement=interval(vec[0]-vec[1]),matched_alpha_improvement=interval(vec[0]-vec[2]),within_treatment_alpha1p5_minus_alpha1=interval(vec[2]-vec[1])))
 save(O/'same_alpha_sensitivity.json',dict(utc=now().isoformat(),n_pairs=292,rows=report,addendum_sha256=sha(add),baseline_file=str(base_file.relative_to(B)),baseline_sha256=sha(base_file),refusal_fn_sha256=sha(B/'src/judge/refusal.py'),original_match_sha256=sha(R/'alpha_matches_frozen.json'),scope='fixed two-seed strength sensitivity; no change to original matching or main criterion'))
 pulse('complete')
except BaseException as e:pulse('failed',error=str(e));raise
