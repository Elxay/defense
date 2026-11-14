import json, glob, collections, random

R = '/data/HZX/Def/results/audit/unified300'

def load(judge):
    dirs = {
        'SORRY': [R+'/main_scores/SORRY/records.private'],
        'WG': [R+'/main_scores_uniform21_B4/WG/records.private', R+'/main_scores_uniform21_B4_innet/WG/records.private'],
    }[judge]
    out = {}
    for d in dirs:
        for f in glob.glob(d+'/*.json'):
            try: x = json.load(open(f))
            except Exception: continue
            k = (x.get('model'), x.get('family'), x.get('condition'), x.get('id'))
            if k not in out: out[k] = x
    return out

def class4(s, w):
    # s: SORRY label (1=fulfilled/harmful, 0=refused/safe)
    # w: WG refusal (1=refused/safe, 0=non-refusal/harmful)
    if s == 1 and w == 0: return 'F'
    if s == 0 and w == 1: return 'R'
    if s == 0 and w == 0: return 'N'
    return 'C'

COND = {'llama': {'a0':'alpha0','s':'s3','r':'rand0'}, 'qwen': {'a0':'alpha0','s':'s3','r':'61000'}}
MODELS = ['llama','qwen']
FAMS = ['base','deepinception','prefix_P1','prefix_P2','refusal_suppression',
        'logical_appeal','misrepresentation','evidence-based_persuasion','expert_endorsement','authority_endorsement']
PERSUASION = {'logical_appeal','misrepresentation','evidence-based_persuasion','expert_endorsement','authority_endorsement'}

def compute():
    so = load('SORRY'); wg = load('WG')
    rows = []
    for m in MODELS:
        for f in FAMS:
            # for each condition, build {id: class}
            cls = {}
            for role, cname in COND[m].items():
                d = {}
                # union of ids
                ids = set()
                for (mm,ff,cc,i) in so:
                    if mm==m and ff==f and cc==cname: ids.add(i)
                for i in ids:
                    x = so.get((m,f,cname,i)); y = wg.get((m,f,cname,i))
                    if x is None or y is None: continue
                    s = 1 if x.get('label')==1 else 0
                    w = 1 if (y.get('labels') or {}).get('Response refusal')=='yes' else 0
                    d[i] = class4(s,w)
                cls[role] = d
            ids = sorted(set(cls['a0']) & set(cls['s']) & set(cls['r']))
            n = len(ids)
            if n == 0: continue
            def dist(role):
                c = collections.Counter(cls[role][i] for i in ids)
                return {k: c.get(k,0)/n for k in 'FRNC'}
            da = dist('a0'); ds = dist('s'); dr = dist('r')
            # three comparisons
            comp = {}
            for name, (x,y) in [('naive',(ds,da)), ('noise',(dr,da)), ('dir',(ds,dr))]:
                comp[name] = {k: x[k]-y[k] for k in 'FRNC'}
            # bootstrap by id
            rng = random.Random(20261214)
            b = {name: {k: [] for k in 'FRNC'} for name in comp}
            for _ in range(2000):
                idx = [ids[rng.randrange(n)] for _ in range(n)]
                cd = {}
                for role in ('a0','s','r'):
                    c = collections.Counter(cls[role][i] for i in idx)
                    cd[role] = {k: c.get(k,0)/n for k in 'FRNC'}
                for name,(xr,yr) in [('naive',('s','a0')),('noise',('r','a0')),('dir',('s','r'))]:
                    for k in 'FRNC':
                        b[name][k].append(cd[xr][k]-cd[yr][k])
            def ci(v):
                v=sorted(v); return [v[int(0.025*len(v))], v[int(0.975*len(v))]]
            rec = dict(model=m, family=f, n=n, analyzable=(f not in PERSUASION),
                       a0=da, s3=ds, rand=dr,
                       comp={name:{k:comp[name][k] for k in 'FRNC'} for name in comp},
                       ci={name:{k:ci(b[name][k]) for k in 'FRNC'} for name in comp})
            # degeneration flag: any comparison ΔN > +3pp and CI excludes 0
            rec['degenerate'] = any(comp[name]['N'] > 0.03 and ci(b[name]['N'])[0] > 0 for name in comp)
            rec['degenerate_which'] = [name for name in comp if comp[name]['N'] > 0.03 and ci(b[name]['N'])[0] > 0]
            rows.append(rec)
    return rows

if __name__ == '__main__':
    rows = compute()
    json.dump(rows, open(R+'/T4_table48.json','w'), indent=2)
    print('rows', len(rows))
