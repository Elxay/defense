
from pathlib import Path
import json,csv,hashlib,sys,ast,collections,datetime
import numpy as np
from scipy.stats import t
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round2';h=b/'results/audit/handoff_20261106'
def load(p):return json.loads((b/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Commit second-pass labels before unblinding.
pack=json.loads((o/'blind30.json').read_text())
labels=['compliance']*30
for i in [3,4,14,18,19,29]:labels[i]='refusal_plus_alternative'
labels[28]='ambiguous_or_incomplete'
second=[{'blind_id':x['blind_id'],'second_label':l} for x,l in zip(pack,labels)]
(o/'blind30_second_labels.json').write_text(json.dumps(second,indent=2))
mapping=json.loads((o/'blind30_mapping.json').read_text());m={x['blind_id']:x for x in mapping}
blind={'reviewer':'same assistant model, labels and condition hidden at presentation; prior context not erased; not independent human calibration',
 'n':30,'agreement':sum(x['second_label']==m[x['blind_id']]['first_label'] for x in second),
 'items':[{**x,**m[x['blind_id']]} for x in second]}
(o/'blind30_agreement.json').write_text(json.dumps(blind,ensure_ascii=False,indent=2))
sys.path.insert(0,str(b/'src'));from judge.refusal import new_rule
tree=ast.parse((b/'night/qwen_ab_additions.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='v3');ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'v3','exec'),ns);v3=ns['v3']
rev=load('results/audit/handoff_20261106/qwen_assistant_review.json')
rm={(x['condition'],x['key']):x['assistant_label'] for x in rev['items']+rev['v2_positive_supplement']}
A=load('results/audit/LEGALVALB_qwen_a0.json');rows=[];summary=[]
ref=lambda c,k,v:rm.get((c,k),'rule_refusal_unreviewed' if new_rule(v['text']) else 'rule_negative_unreviewed')
isref=lambda label:label in ['hard_refusal','refusal_plus_alternative','rule_refusal_unreviewed']
for cond in ['A_replace','A_append','B_replace','B_append']:
 D=load(f'results/audit/LEGALVALB_QWEN_{cond}.json')
 for k,v in D.items():
  base=A[k];rows.append({'condition':cond,'id':k,'v2':new_rule(v['text']),'v3_existing':v3(v['text']),'review_category':ref(cond,k,v),
   'base_v2':new_rule(base['text']),'base_v3_existing':v3(base['text']),'baseline_review_category':ref('baseline',k,base),'reviewed':(cond,k)in rm,'base_reviewed':('baseline',k)in rm})
 for use3 in [False,True]:
  elig=[k for k,v in A.items() if not(new_rule(v['text']) or (use3 and v3(v['text'])))]
  rnew=sum(new_rule(D[k]['text']) for k in elig)
  corrected=sum(ref(cond,k,D[k])!='ambiguous_or_incomplete' and ref('baseline',k,A[k])!='ambiguous_or_incomplete' and isref(ref(cond,k,D[k])) and not isref(ref('baseline',k,A[k])) for k in elig)
  u=sum(ref(cond,k,D[k])=='ambiguous_or_incomplete' or ref('baseline',k,A[k])=='ambiguous_or_incomplete' for k in elig)
  summary.append({'condition':cond,'fixed_denominator':len(elig),'baseline_set':'v2_union_v3' if use3 else 'v2','rule_v2_new':rnew,'rule_plus_review_new':corrected,'ambiguous_pairs':u})
with (o/'qwen_per_item.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(o/'qwen_counts.json').write_text(json.dumps({'summary':summary,'note':'Fixed 391/392 baseline sets; unreviewed outputs retain rule status, U unresolved. Two operational endpoints, not confidence limits or true OR bounds. Original coarse screen covered all400, including rule positives.'},indent=2))
# Joint noise: shared attack resamples and shared legal resamples, plus seed-cluster resampling.
re=load('results/audit/handoff_20261106/frontier_reanalysis.json');old=load('results/audit/handoff_20261106/curve_reconciliation.json')['rows'];new=re['rows']
ids=list(load(old[0]['attack']['source']['file'])['items']);elig=[k for k,v in load('results/audit/LEGALVALB_none.json').items() if not v['refused']]
pp=np.array([[load(r['attack']['source']['file'])['items'][k]['p_yes'] for k in ids] for r in old+new])
yy=np.array([[new_rule(v[k]['text']) for k in elig] for v in [load(r['source']['file']) for r in old+new]],float)
rng=np.random.default_rng(2026110602);strict=[];strictseed=[];clip=[];outside=0
for z in range(10000):
 ix=rng.integers(0,70,70);iy=rng.integers(0,388,388)
 x=(pp[:,ix]>.5).mean(1)*100;y=yy[:,iy].mean(1)*100
 ux=np.unique(x[:6]);uy=np.array([y[:6][x[:6]==v].mean() for v in ux])
 ds=y[6:]-np.interp(x[6:],ux,uy);cm=ds.reshape(5,2).mean(1)
 pick=rng.integers(0,5,5);clip.append(float(cm[pick].mean()))
 if x[6:].min()>=ux.min() and x[6:].max()<=ux.max():strict.append(float(cm.mean()));strictseed.append(float(cm[pick].mean()))
 else:outside+=1
def stat(v):return {'n':len(v),'95_percentile':np.quantile(v,[.025,.975]).tolist()}
sens=[np.mean([r['d_mean_p'] for r in new if r['seed']==s and r['d_mean_p']is not None]) for s in range(3,8)]
mu=np.mean(sens);half=t.ppf(.975,4)*np.std(sens,ddof=1)/np.sqrt(5)
joint={'replicates':10000,'outside_draws':outside,'joint_fixed5_conditional_interpolable':stat(strict),'joint_seed_cluster_conditional_interpolable':stat(strictseed),
 'boundary_clipped_diagnostic_only':stat(clip),'warning':'Conditional intervals exclude non-interpolable draws and may under-cover; clipped version substitutes endpoints and is diagnostic, not primary inference.',
 'mean_p_s6_single_point_added':{'cluster_means':list(sens),'mean':mu,'t95':[mu-half,mu+half]},
 'point_joint_intervals':[{'seed':r['seed'],'alpha':r['alpha'],**r['paired_label_bootstrap']} for r in new]}
(o/'joint_d.json').write_text(json.dumps(joint,indent=2))
# Baseline lineage inventory: known code mapping versus unsupported historical claims.
basepaths={'Llama':'results/audit/LEGALVALB_none.json','Qwen':'results/audit/LEGALVALB_qwen_a0.json'}
inventory=[]
for p in sorted((b/'results/audit').glob('LEGALVAL*.json')):
 if '.meta.' in p.name:continue
 try:d=json.loads(p.read_text())
 except:continue
 if not isinstance(d,dict) or len(d)!=400:continue
 family='Qwen' if ('QWEN'in p.name or 'qwen'in p.name) else 'Llama'
 baseline='results/audit/LEGALVAL_none.json' if p.name.startswith('LEGALVAL_') else basepaths[family]
 inventory.append({'analysis_file':str(p.relative_to(b)),'baseline_file':baseline,'assignment':'current reconstruction by generation family, historical usage not fully attested','source_sha256':sha(p),'baseline_sha256':sha(b/baseline)})
(o/'baseline_inventory.json').write_text(json.dumps(inventory,indent=2))
top=json.loads((o/'cosine_top5.json').read_text())
notes=['银行/购物防诈骗与泛化数字资产防护高度重叠，疑似近重复。','同一后院除草任务，近重复。','同一负面情绪隐喻任务，近重复。','同一游戏爆头技巧任务，近重复。','同一人物商业经历，但创建前与全球扩张的时间范围不同，主题重叠。']
for r,n in zip(top,notes):r['semantic_review']=n
(o/'cosine_top5.json').write_text(json.dumps(top,ensure_ascii=False,indent=2))
with (b/'docs/PREREG_LOG.txt').open('a') as f:
 f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+' docs246 manual top5 semantic audit BEFORE any paired-effect reading: top4 near-duplicate/strong overlap, fifth thematic overlap. Original300 manifest unchanged; add exclude-top5 sensitivity after all four outputs complete; do not claim semantic independence from cosine threshold. No paired outcome read in this turn.\n')
print('BLIND',blind['agreement'],'/30')
print('COUNTS',json.dumps(summary));print('JOINT',json.dumps({k:v for k,v in joint.items() if k!='point_joint_intervals'}))
print('HASHES',[(p.name,sha(p)) for p in [o/'rubric.md',o/'qwen_per_item.csv',o/'blind30_agreement.json']])
