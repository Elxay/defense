import json, glob, collections, random, hashlib

R = '/data/HZX/Def/results/audit/unified300'

def load(judge):
    dirs = {
        'HB': [R+'/main_scores/HB/records.private'],
        'SORRY': [R+'/main_scores/SORRY/records.private'],
        'WG': [R+'/main_scores_uniform21_B4/WG/records.private',
               R+'/main_scores_uniform21_B4_innet/WG/records.private'],
    }[judge]
    out = []
    for d in dirs:
        for f in glob.glob(d+'/*.json'):
            try: x = json.load(open(f))
            except Exception: continue
            out.append(x)
    return out

def key(x):
    return (x.get('model'), x.get('family'), x.get('condition'), x.get('id'))

def label(judge, x):
    # ASR direction: 1 = harmful / non-refusal (ASR), 0 = safe / refusal
    if judge == 'WG':
        lab = x.get('labels') or {}
        return 0 if lab.get('Response refusal') == 'yes' else 1  # non-refusal = ASR
    return 1 if x.get('label') == 1 else 0

COND = {'llama': {'a0':'alpha0','s':'s3','r':'rand0'},
        'qwen':  {'a0':'alpha0','s':'s3','r':'61000'}}
MODELS = ['llama','qwen']
FAMS = ['base','deepinception','prefix_P1','prefix_P2','refusal_suppression',
        'logical_appeal','misrepresentation','evidence-based_persuasion','expert_endorsement','authority_endorsement']
PERSUASION = {'logical_appeal','misrepresentation','evidence-based_persuasion','expert_endorsement','authority_endorsement'}

def dedup(recs):
    out = {}
    for x in recs:
        k = key(x)
        if k not in out:
            out[k] = x
    return out

def compute():
    data = {j: dedup(load(j)) for j in ('HB','SORRY','WG')}
    rows = []
    for m in MODELS:
        for f in FAMS:
            for judge in ('HB','SORRY','WG'):
                conds = {}
                for role, cname in COND[m].items():
                    d = {}
                    for (mm, ff, cc, i), x in data[judge].items():
                        if mm == m and ff == f and cc == cname:
                            d[i] = label(judge, x)
                    conds[role] = d
                ids = sorted(set(conds['a0']) & set(conds['s']) & set(conds['r']))
                n = len(ids)
                if n == 0:
                    rows.append(dict(model=m, family=f, judge=judge, n=0, missing=True,
                                     analyzable=(f not in PERSUASION)))
                    continue
                va = [conds['a0'][i] for i in ids]
                vs = [conds['s'][i]  for i in ids]
                vr = [conds['r'][i]  for i in ids]
                ra = sum(va)/n; rs = sum(vs)/n; rr = sum(vr)/n
                dnaive = rs - ra; dnoise = rr - ra; ddir = rs - rr
                rng = random.Random(20261214)
                bn, bns, bd = [], [], []
                for _ in range(2000):
                    idx = [ids[rng.randrange(n)] for _ in range(n)]
                    a2 = sum(conds['a0'][i] for i in idx)
                    s2 = sum(conds['s'][i]  for i in idx)
                    r2 = sum(conds['r'][i]  for i in idx)
                    bn.append((s2-a2)/n); bns.append((r2-a2)/n); bd.append((s2-r2)/n)
                def ci(v):
                    v = sorted(v)
                    return [v[int(0.025*len(v))], v[int(0.975*len(v))]]
                c_n = ci(bn); c_ns = ci(bns); c_d = ci(bd)
                rows.append(dict(model=m, family=f, judge=judge, n=n,
                    rate_a0=ra, rate_s3=rs, rate_rand=rr,
                    dNaive=dnaive, dNoise=dnoise, dDir=ddir,
                    ci_dNaive=c_n, ci_dNoise=c_ns, ci_dDir=c_d,
                    analyzable=(f not in PERSUASION),
                    upgrade=(c_n[1] < 0 and c_d[1] < 0)))
    return rows

if __name__ == '__main__':
    rows = compute()
    json.dump(rows, open(R+'/T1_table48.json','w'), indent=2)
    print('rows', len(rows))
