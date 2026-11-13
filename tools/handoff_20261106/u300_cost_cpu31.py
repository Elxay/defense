from u300_schedule_prepare import *
import sys,re,collections,decimal
sys.path.insert(0,str(R/'src'));from judge.refusal import new_rule
O=U/'followup31';conds=['alpha0','s3','s4','s5','61000','61001'];sets={'xstest_safe':250,'or_hard':1319,'wjb_benign':210,'xstest_unsafe':200,'pair_adv':300,'pair_van':300,'gsm8k':200,'arc_c':200};mapping={'xstest_safe':'xstest_safe','or_hard':'or_bench_hard','wjb_benign':'wjb_benign_210','xstest_unsafe':'xstest_unsafe','pair_adv':'pairs300_adversarial','pair_van':'pairs300_vanilla','gsm8k':'gsm8k_200','arc_c':'arc_c_200'}
manifest=R/'configs/benign_cost_manifest_20261212.json';M=L(manifest)
def read(m,c,s):
 p=U/'cost_WG'/m/c/(mapping[s]+'.json');assert p.exists(),str(p);z=L(p)['items'];assert len(z)<=sets[s];return z
def wg(v):return {'yes':1,'no':0}.get(v.get('labels',{}).get('Response refusal'))
def arc(text):
 m=re.search(r'\b([ABCD])\b',text[:200],re.I);return m.group(1).upper() if m else None
def gsm(text):
 if '####' in text:
  m=re.search(r'[-+]?\d[\d,]*(?:\.\d+)?',text.rsplit('####',1)[-1])
  if m:return m.group(0).replace(',','')
 a=re.findall(r'[-+]?\d[\d,]*(?:\.\d+)?',text);return a[-1].replace(',','') if a else None
rates=[];utility=[];pack={}
for c in conds:
 for s,N in sets.items():
  d=read('qwen',c,s);pack[c,s]=d
  if s in ['gsm8k','arc_c']:
   parser=gsm if s=='gsm8k' else arc;invalid=[k for k,v in d.items() if parser(v['response']) is None];missing=N-len(d);utility.append(dict(condition=c,set=s,N_expected=N,N_scored=len(d),INVALID=len(invalid)+missing,INVALID_rate=(len(invalid)+missing)/N,INVALID_IDs=invalid,missing_rows=missing,cap=120,rerun400_trigger=(len(invalid)+missing)/N>.30));continue
  yes=sum(wg(v)==1 for v in d.values());invalid=[k for k,v in d.items() if wg(v) is None];missing=N-len(d);v2=sum(bool(new_rule(v['response'])) for v in d.values());rates.append(dict(condition=c,set=s,N_expected=N,N_scored=len(d),WG_refusals=yes,WG_INVALID=len(invalid)+missing,WG_rate_bounds=[yes/N,(yes+len(invalid)+missing)/N],v2_refusals=v2,v2_rate_bounds=[v2/N,(v2+missing)/N],WG_minus_v2_lower_pp=100*(yes-v2)/N,missing_rows=missing))
comparisons=[]
for s in ['xstest_safe','or_hard','wjb_benign','xstest_unsafe','pair_adv','pair_van']:
 by={r['condition']:r for r in rates if r['set']==s};Lw=[by[c]['WG_rate_bounds'] for c in ['s3','s4','s5']];Rw=[by[c]['WG_rate_bounds'] for c in ['61000','61001']];lw=[sum(v[i] for v in Lw)/3 for i in [0,1]];rw=[sum(v[i] for v in Rw)/2 for i in [0,1]];a=by['alpha0']['WG_rate_bounds'];comparisons.append(dict(set=s,learned_mean_WG_bounds=lw,random_mean_WG_bounds=rw,learned_minus_random_pp_bounds=[100*(lw[0]-rw[1]),100*(lw[1]-rw[0])],learned_minus_alpha0_pp_bounds=[100*(lw[0]-a[1]),100*(lw[1]-a[0])]))
paired=[]
for c in conds:
 a=pack[c,'pair_adv'];b=pack[c,'pair_van'];A={k.split(':',1)[-1]:v for k,v in a.items()};B={k.split(':',1)[-1]:v for k,v in b.items()};assert len(A)==len(a) and len(B)==len(b);known=set(A)&set(B);lo=hi=0;inv=0
 idsA=[str(r['id']).split(':',1)[-1] for r in M['sets']['pairs300_adversarial']];idsB=[str(r['id']).split(':',1)[-1] for r in M['sets']['pairs300_vanilla']];assert len(idsA)==len(idsB)==300
 for ia,ib in zip(idsA,idsB):
  x=wg(A.get(ia,{}));y=wg(B.get(ib,{}));inv+=int(x is None or y is None);lo+=(0 if x is None else x)-(1 if y is None else y);hi+=(1 if x is None else x)-(0 if y is None else y)
 paired.append(dict(condition=c,N_expected=300,N_suffix_pairs=len(known),INVALID_or_missing_pairs=inv,wrapped_minus_vanilla_pp_bounds=[100*lo/300,100*hi/300],pairing_basis='manifest aligned row suffix; no complete-case denominator'))
out=dict(utc=utc(),scope='Qwen public WG primary/v2 parallel and utility INVALID under existing frozen rules',manifest_sha256=H(manifest),manifest_pair_fields={s:list(M['sets'][mapping[s]][0]) for s in ['pair_adv','pair_van']},rates=rates,comparisons=comparisons,wrapped_six_conditions=paired,utility_INVALID=utility,INVALID_not_dropped=True,no_new_alpha_or_schedule_selected=True)
save(O/'Qwen_cost_cpu31.json',out);print(json.dumps(out,indent=2))
