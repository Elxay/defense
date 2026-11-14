import glob, json, collections, hashlib, datetime, random
R='/data/HZX/Def/results/audit/unified300'
def load(which):
    d={}
    for f in glob.glob(R+f'/main_scores/{which}/records.private/*.json'):
        try: x=json.load(open(f))
        except: continue
        k=(x.get('model'),x.get('family'),x.get('condition'),int(x.get('id')))
        if which=='HB': lab=x.get('label')
        else: lab=x.get('label')
        d[k]=lab
    return d
HB=load('HB'); SO=load('SORRY')
print("HB",len(HB),"SORRY",len(SO))
RAND={'rand0','rand1','rand2','rand3','61000','61001'}
LEARN={'s3','s4','s5'}
def unit_map(D):
    u=collections.defaultdict(dict)
    for (m,f,c,i),lab in D.items(): u[(m,f,c)][i]=lab
    return u
out=[]
for name,D in (('HB',HB),('SORRY',SO)):
    U=unit_map(D)
    fam=collections.defaultdict(dict)
    for (m,f,c),v in U.items(): fam[(m,f)][c]=v
    rng=random.Random(20261212)
    for (m,f),conds in sorted(fam.items()):
        Lc=[c for c in LEARN if c in conds]; Rc=[c for c in RAND if c in conds]
        if not Lc or not Rc: continue
        ids=sorted(set(conds[Lc[0]]))
        diffs={}
        for i in ids:
            lv=[conds[c].get(i) for c in Lc]; rv=[conds[c].get(i) for c in Rc]
            lv=[x for x in lv if x is not None]; rv=[x for x in rv if x is not None]
            if not lv or not rv: continue
            diffs[i]=(sum(lv)/len(lv))-(sum(rv)/len(rv))
        if not diffs: continue
        vals=list(diffs.values()); point=sum(vals)/len(vals)
        boots=[]
        for _ in range(2000):
            s=[vals[rng.randrange(len(vals))] for _ in range(len(vals))]
            boots.append(sum(s)/len(s))
        boots.sort()
        lo=boots[int(0.025*len(boots))]; hi=boots[int(0.975*len(boots))]
        out.append(dict(judge=name,model=m,family=f,n=len(vals),point=point,lo=lo,hi=hi,
                        verdict='negative' if hi<0 else ('positive' if lo>0 else 'uncertain'),
                        seeds={c:sum(conds[c].get(i) or 0 for i in ids)/len(ids) for c in Lc}))
print("rows",len(out))
for e in out:
    if e['judge']=='HB': print("%-5s %-26s n %d point %+.3f CI [%+.3f,%+.3f] %s"%(e['model'],e['family'],e['n'],e['point'],e['lo'],e['hi'],e['verdict']))
json.dump(out,open(R+'/R1_intervals_20261112.json','w'),indent=1)
print("SHA",hashlib.sha256(open(R+'/R1_intervals_20261112.json','rb').read()).hexdigest())