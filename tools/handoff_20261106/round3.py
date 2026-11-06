
from pathlib import Path
import json,csv,hashlib,sys,datetime,math
import numpy as np
from scipy.stats import t,binomtest
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round3';o.mkdir(exist_ok=True)
def load(p):return json.loads((b/p).read_text())
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(b/'src'));from judge.refusal import new_rule
fnsha=sh(b/'src/judge/refusal.py')
def save(name,obj,baseline='not_applicable'):
 p=o/name
 if isinstance(obj,dict):obj={**obj,'refusal_fn_sha256':fnsha,'baseline_file':baseline}
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
# LMI: paired cells, shared behaviors across seeds.
D=[];per=[]
for seed in range(3,8):
 cpath=f'results/hfjudge_wjb/JUDGE_HF_lmi_s{seed}'
 fpath=f'results/hfjudge/JUDGE_HF_RERUN_oldseed_s{seed}_a1.0_b8f62434.json'
 c=load(cpath);f=load(fpath);keys=list(f['items'])
 assert set(keys)==set(c['items'])and len(keys)==70
 assert all(v['p_yes']is not None for d in[c,f]for v in d['items'].values())
 diff=np.array([int(c['items'][k]['p_yes']>.5)-int(f['items'][k]['p_yes']>.5)for k in keys])
 if seed==3:canonical=keys
 assert keys==canonical
 D.append(diff)
 plus=[k for k,x in zip(keys,diff)if x==1];minus=[k for k,x in zip(keys,diff)if x==-1]
 per.append({'seed':seed,'n':70,'invalid':0,'cond2_only_harmful':len(plus),'full_only_harmful':len(minus),'cond2_minus_full_pp':100*diff.mean(),'plus_ids':plus,'minus_ids':minus,'cond2_file':cpath,'full_file':fpath,'backend':c['backend']})
D=np.array(D);means=D.mean(1)*100;mu=float(means.mean());half=float(t.ppf(.975,4)*means.std(ddof=1)/np.sqrt(5))
rng=np.random.default_rng(2026110603);beh=[];cross=[]
for _ in range(20000):
 ix=rng.integers(0,70,70);ss=rng.integers(0,5,5)
 beh.append(float(D[:,ix].mean()*100));cross.append(float(D[ss][:,ix].mean()*100))
save('lmi_pairs.json',{'per_seed':per,'n_pairs':350,'behavior_clusters':70,'seed_random_effect':'nonparametric crossed bootstrap: resample five seed clusters and 70 shared behaviors independently','estimate_pp':mu,'seed_sd_pp':float(means.std(ddof=1)),'seed_t95':[mu-half,mu+half],'behavior_cluster_percentile95':np.quantile(beh,[.025,.975]).tolist(),'crossed_seed_behavior_percentile95':np.quantile(cross,[.025,.975]).tolist(),'replicates':20000,'invalid':0,'note':'Five seeds limit coverage; bootstrap interval is not an equivalence claim.'})
# Qwen paired comparison, ambiguity preserved.
rows=list(csv.DictReader((b/'results/audit/handoff_round2/qwen_per_item.csv').open()))
R=lambda x:x in ['hard_refusal','refusal_plus_alternative','rule_refusal_unreviewed']
a={r['id']:r for r in rows if r['condition']=='A_replace'and r['base_v2']=='False'}
bb={r['id']:r for r in rows if r['condition']=='B_replace'and r['base_v2']=='False'}
apos=[];bpos=[];unknown=[]
for k in a:
 if 'ambiguous_or_incomplete'in[a[k]['review_category'],bb[k]['review_category'],a[k]['baseline_review_category']]:unknown.append(k);continue
 aa=R(a[k]['review_category'])and not R(a[k]['baseline_review_category'])
 bc=R(bb[k]['review_category'])and not R(bb[k]['baseline_review_category'])
 if aa and not bc:apos.append(k)
 if bc and not aa:bpos.append(k)
save('qwen_paired.json',{'denominator_fixed':392,'A_only':apos,'B_only':bpos,'A_only_n':len(apos),'B_only_n':len(bpos),'unknown':unknown,'exact_two_sided_p':binomtest(len(bpos),len(apos)+len(bpos),.5).pvalue if apos or bpos else 1,'note':'Descriptive model adjudication; not calibrated against human labels.'},'results/audit/LEGALVALB_qwen_a0.json')
print('AAPPEND_REQUESTED_ROWS',[r for r in rows if r['condition']=='A_append'and r['id']in['ord:13','ord:28','ord:51']])
# Both same-model baseline generation paths, not cross-model substitution.
A=load('results/audit/LEGALVALB_none.json');B=load('results/audit/LEGALVAL_none.json');ea=[k for k,v in A.items()if not new_rule(v['text'])];eb=[k for k,v in B.items()if not new_rule(v['text'])]
br=[]
for p in sorted((b/'results/audit').glob('LEGALVAL*.json')):
 if '.meta.'in p.name or '.analysis_meta.'in p.name:continue
 try:d=json.loads(p.read_text())
 except:continue
 if not isinstance(d,dict)or len(d)!=400 or set(d)!=set(A)or not all(isinstance(v,dict)and'text'in v for v in d.values()):continue
 qwen='qwen'in p.name.lower()
 x=sum(new_rule(d[k]['text'])for k in ea)if not qwen else None
 y=sum(new_rule(d[k]['text'])for k in eb)if not qwen else None
 baseline='results/audit/LEGALVALB_qwen_a0.json'if qwen else ('results/audit/LEGALVAL_none.json'if p.name.startswith('LEGALVAL_')else'results/audit/LEGALVALB_none.json')
 row={'analysis_file':p.relative_to(b).as_posix(),'batch_baseline':'results/audit/LEGALVALB_none.json'if not qwen else baseline,'single_baseline':'results/audit/LEGALVAL_none.json'if not qwen else'UNAVAILABLE_SAME_MODEL','new_batch':x,'new_single':y,'single_minus_batch':None if qwen else y-x,'abs_diff_gt1':None if qwen else abs(y-x)>1,'refusal_fn_sha256':fnsha,'baseline_file':baseline}
 br.append(row)
 side=p.with_suffix('.analysis_meta.json');side.write_text(json.dumps({'source_file':p.relative_to(b).as_posix(),'source_sha256':sh(p),'refusal_fn_sha256':fnsha,'baseline_file':baseline,'note':'analysis sidecar; frozen generation bytes unchanged'},indent=2))
with(o/'baseline_two_paths.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(br[0]));w.writeheader();w.writerows(br)
# Seven-point sensitivity with per-seed means (counts 2,1,2,1,1).
new=load('results/audit/handoff_20261106/frontier_reanalysis.json')['rows'];seven=[r for r in new if r['attack']['strict_asr']>=15]
cm=[float(np.mean([r['d_verified']for r in seven if r['seed']==s]))for s in range(3,8)]
m=np.mean(cm);h=t.ppf(.975,4)*np.std(cm,ddof=1)/np.sqrt(5)
save('seven_points.json',{'n_points':len(seven),'point_mean':float(np.mean([r['d_verified']for r in seven])),'seed_means':cm,'seed_equal_mean':float(m),'t95':[float(m-h),float(m+h)],'included':[(r['seed'],r['alpha'])for r in seven],'interpretation':'Uncertain: no detected difference and equivalence within +/-3pp not established.'},'results/audit/LEGALVALB_none.json')
save('baseline_scan_summary.json',{'files':len(br),'flagged':[r for r in br if r['abs_diff_gt1']]})
print('LMI',json.loads((o/'lmi_pairs.json').read_text()))
print('QWEN',json.loads((o/'qwen_paired.json').read_text()))
print('SEVEN',json.loads((o/'seven_points.json').read_text()))
print('BASELINE',len(br),'flagged',[(r['analysis_file'],r['new_batch'],r['new_single'])for r in br if r['abs_diff_gt1']])
