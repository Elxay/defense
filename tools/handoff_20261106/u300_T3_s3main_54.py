import json, glob, random, hashlib

R = '/data/HZX/Def/results/audit/unified300'

def load_set(model, cond, s):
    for f in glob.glob(f'{R}/cost_WG/{model}/{cond}/{s}.json'):
        return json.load(open(f))['items']
    return {}

def ref(item):
    lab = item.get('labels') or {}
    return 1 if lab.get('Response refusal') == 'yes' else 0

SETS = ['or_bench_hard','xstest_safe','xstest_unsafe','wjb_benign_210','pairs300_adversarial','pairs300_vanilla']
EXCLUDE = {
  'or_bench_hard': set(f'or_hard:{i}' for i in list(range(120,128))+list(range(130,140))),
  'xstest_safe': set(f'xstest_safe:{i}' for i in list(range(221,226))+list(range(251,258))),
}
POOL = ['or_bench_hard','xstest_safe','wjb_benign_210','pairs300_adversarial','pairs300_vanilla']

def ci_boot(il, sets, a0, ra, nboot=2000, seed=20261214):
    rng = random.Random(seed); n=len(il)
    bn=[]; br=[]
    for _ in range(nboot):
        idx=[il[rng.randrange(n)] for _ in range(n)]
        dn=[sum(ref(d[i]) for d in sets)/len(sets)-ref(a0[i]) for i in idx]
        dr=[sum(ref(d[i]) for d in sets)/len(sets)-ref(ra[i]) for i in idx]
        bn.append(sum(dn)/n); br.append(sum(dr)/n)
    def c(v): v=sorted(v); return [v[int(.025*len(v))],v[int(.975*len(v))]]
    return c(bn), c(br)

def main():
    out = {}
    for model, rc in [('llama','rand0'),('qwen','61000')]:
        res = {}
        for s in SETS:
            a0=load_set(model,'alpha0',s); ra=load_set(model,rc,s)
            conds = ['s3','s4','s5']
            ds = {c: load_set(model,c,s) for c in conds}
            ids = set(a0)&set(ra)
            for c in conds: ids &= set(ds[c])
            ids = sorted(ids)
            exc = EXCLUDE.get(s,set())
            old=ids; new=[i for i in ids if i not in exc]
            entry={}
            for label, il in [('old',old),('new',new)]:
                for c in conds:
                    dn=[ref(ds[c][i])-ref(a0[i]) for i in il]
                    dr=[ref(ds[c][i])-ref(ra[i]) for i in il]
                    bn,br = ci_boot(il, [ds[c]], a0, ra)
                    entry[(label,c)]=dict(n=len(il), L_none=sum(dn)/len(dn), L_none_ci=bn, L_rand=sum(dr)/len(dr), L_rand_ci=br)
            res[s]=entry
        # pooled s3 main
        for label in ('old','new'):
            for c in conds:
                dn=[]; dr=[]
                allil=[]
                for s in POOL:
                    a0=load_set(model,'alpha0',s); ra=load_set(model,rc,s); d=load_set(model,c,s)
                    ids=set(a0)&set(ra)&set(d)
                    il=sorted(i for i in ids if (label=='old' or i not in EXCLUDE.get(s,set())))
                    for i in il:
                        dn.append(ref(d[i])-ref(a0[i])); dr.append(ref(d[i])-ref(ra[i]))
                res.setdefault('POOL5',{})[(label,c)]=dict(n=len(dn), L_none=sum(dn)/len(dn), L_rand=sum(dr)/len(dr))
        out[model]=res
    # random reference on or_bench_hard (random - none)
    refr={}
    for model, rands in [('llama',['rand0','rand1']),('qwen',['61000','61001'])]:
        a0=load_set(model,'alpha0','or_bench_hard')
        row={}
        for rc in rands:
            ra=load_set(model,rc,'or_bench_hard')
            ids=sorted(set(a0)&set(ra))
            row[rc]=sum(ref(ra[i])-ref(a0[i]) for i in ids)/len(ids)
        refr[model]=row
    return out, refr

if __name__=='__main__':
    out, refr = main()
    json.dump(dict(t3=out, random_ref=refr), open(R+'/T3_s3main_54.json','w'), indent=1)
    print('saved T3_s3main_54.json')
    print('sha:', hashlib.sha256(open(R+'/T3_s3main_54.json','rb').read()).hexdigest())
    for model in out:
        print(f'=== {model} (s3 main) ===')
        for s in SETS:
            e=out[model][s]
            for label in ('old','new'):
                x=e[(label,'s3')]
                print(f'{s:22s} {label:3s} n={x["n"]:4d} L-none={x["L_none"]:+.4f}[{x["L_none_ci"][0]:+.3f},{x["L_none_ci"][1]:+.3f}] L-rand={x["L_rand"]:+.4f}[{x["L_rand_ci"][0]:+.3f},{x["L_rand_ci"][1]:+.3f}]')
        print('POOL5:', {k:v for k,v in out[model].get('POOL5',{}).items()})
    print('random_ref:', refr)
