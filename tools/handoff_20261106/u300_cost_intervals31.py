from u300_schedule_prepare import *
import random,numpy as np
O=U/'followup31';M=L(R/'configs/benign_cost_manifest_20261212.json');conds=['alpha0','s3','s4','s5','61000','61001'];rng=random.Random(20261213)
def arr(setname):
 ids=[str(r['id']) for r in M['sets'][setname]];a=[]
 for c in conds:
  d=L(U/'cost_WG/qwen'/c/(setname+'.json'))['items'];a.append([{'yes':1.,'no':0.}.get(d.get(i,{}).get('labels',{}).get('Response refusal'),np.nan) for i in ids])
 return np.array(a)
def ci(lower,upper):
 N=len(lower);idx=np.array([[rng.randrange(N) for _ in range(N)] for b in range(2000)],dtype=np.int32);lo=lower[idx].mean(1);hi=upper[idx].mean(1);return [float(np.sort(lo)[50]),float(np.sort(hi)[1950])]
rows=[]
for s in ['xstest_safe','or_bench_hard','wjb_benign_210','xstest_unsafe']:
 x=arr(s);low=np.nan_to_num(x,nan=0.);high=np.nan_to_num(x,nan=1.);l=low[1:4].mean(0);u=high[1:4].mean(0)
 for cmp,vl,vu in [('learned_minus_random',low[4:].mean(0),high[4:].mean(0)),('learned_minus_alpha0',low[0],high[0])]:
  a=l-vu;b=u-vl;rows.append(dict(set=s,comparison=cmp,N=len(a),point_identification_pp=[float(a.mean()*100),float(b.mean()*100)],CI95_pp=[100*z for z in ci(a,b)]))
xa=arr('pairs300_adversarial');xv=arr('pairs300_vanilla');paired=[]
for j,c in enumerate(conds):
 a=np.nan_to_num(xa[j],nan=0)-np.nan_to_num(xv[j],nan=1);b=np.nan_to_num(xa[j],nan=1)-np.nan_to_num(xv[j],nan=0);paired.append(dict(condition=c,N=300,point_identification_pp=[float(a.mean()*100),float(b.mean()*100)],CI95_pp=[100*z for z in ci(a,b)]))
save(O/'Qwen_cost_intervals31.json',dict(utc=utc(),method='2000 original-prompt cluster bootstrap, fixed Python random seed20261213 from existing auxiliary reader; INVALID0/1 bounds retained',conditional_on_frozen_vectors=True,rows=rows,wrapped_pairs=paired));print(json.dumps(dict(rows=rows,wrapped_pairs=paired),indent=2))
