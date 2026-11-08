"""Alpha0-only paired diagnostics. Never open condition prediction files."""
import collections
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';WG=BASE/'wildguard'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    inputs=json.loads((WG/'alpha0_inputs.private.json').read_text())
    scores={x['id']:x for x in json.loads((WG/'alpha0_labels.private.json').read_text())}
    assert len(inputs)==len(scores)==2000
    hb={};manifest={}
    for row in inputs:
        p=BASE/'public255/mapped_scores/alpha0'/(row['id']+'.json');x=json.loads(p.read_text())
        hb[row['id']]=x['label'];manifest[str(p.relative_to(ROOT))]=sha(p)
    groups={'all':inputs,'high':[r for r in inputs if not r['low_confidence']], 'low':[r for r in inputs if r['low_confidence']]}
    results={}
    for name,rows in groups.items():
        matrix=collections.Counter();invalid=[]
        for row in rows:
            h=hb[row['id']];v=scores[row['id']]['labels']['Harmful response']
            if h not in (0,1) or v not in ('yes','no'):
                invalid.append({'id':row['id'],'harmbench_label':h,'wildguard_label':v});continue
            matrix[h,int(v=='yes')]+=1
        n=sum(matrix.values());po=(matrix[0,0]+matrix[1,1])/n if n else None
        pe=((matrix[0,0]+matrix[0,1])*(matrix[0,0]+matrix[1,0])+(matrix[1,0]+matrix[1,1])*(matrix[0,1]+matrix[1,1]))/n**2 if n else None
        results[name]={'n_all_rows':len(rows),'complete_pairs':n,'invalid_pairs':invalid,
            'matrix':{f'HB{a}_WG{b}':matrix[a,b] for a in (0,1) for b in (0,1)},
            'kappa':(po-pe)/(1-pe) if pe is not None and pe!=1 else None}
    missed=[r for r in inputs if not r['v2'] and scores[r['id']]['labels']['Response refusal']=='yes']
    assert len(missed)==16
    missed_rows=[{'id':r['id'],'HB_top1_harmful':hb[r['id']],
        'WG_response_harmful':scores[r['id']]['labels']['Harmful response'],
        'mapping_layer':'low' if r['low_confidence'] else 'high'} for r in missed]
    prompt_no=[r for r in inputs if scores[r['id']]['labels']['Harmful request']=='no'];assert len(prompt_no)==76
    def counts(rows,field):
        c=collections.Counter(scores[r['id']]['labels'][field] for r in rows)
        yes=c['yes'];no=c['no'];invalid=len(rows)-yes-no
        return {'n':len(rows),'yes':yes,'no':no,'invalid':invalid,'bounds':[yes/len(rows),(yes+invalid)/len(rows)]}
    result={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope':'alpha0 only; harmfulness pairs, not target-condition effects',
        'agreement':results,'v2_negative_wg_refusal_positive_rows':missed_rows,
        'v2_negative_wg_refusal_positive_hb_yes':sum(hb[r['id']]==1 for r in missed),
        'wg_prompt_harmless_response_harmful':counts(prompt_no,'Harmful response'),
        'v2_negative_response_harmful':counts([r for r in inputs if not r['v2']],'Harmful response'),
        'source_hashes':{str((WG/n).relative_to(ROOT)):sha(WG/n) for n in ['alpha0_inputs.private.json','alpha0_labels.private.json']}}
    mp=WG/'alpha0_harmbench_source_hashes.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');result['harmbench_source_manifest_sha256']=sha(mp)
    out=WG/'alpha0_crossjudge.json';out.write_text(json.dumps(result,indent=2)+'\n')
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{result["created_utc"]} WILDGUARD_ALPHA0_CROSSJUDGE_READ SHA={sha(out)} after addendum20 freeze; no condition predictions inspected.\n')
    print(json.dumps(result));print('SHA',sha(out))


if __name__=='__main__':main()
