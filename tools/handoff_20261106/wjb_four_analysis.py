"""Aggregate the fixed four-condition contrasts specified in docs255 addendum11."""
import datetime
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path('/data/HZX/Def')
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools/handoff_20261106'))
from pair500_generate import digest, load, write
from judge.refusal import new_rule

BASE = ROOT / 'results/audit/pair500'
EVAL = BASE / 'public255'
PLAN = ROOT / 'docs/255_ADDENDUM11_FOUR_CONDITION_ANALYSIS.md'
EXPECTED = '8128efd0504f62649b6e0f85471331580f45120d27bcdbc9da11f5129e93625f'
NAMES = ['old_s3', 'old_s4', 'rand0', 'rand1']
WEIGHTS = np.array([[.5,.5,-.5,-.5], [1,0,-.5,-.5], [0,1,-.5,-.5],
                    [1,0,-1,0], [1,0,0,-1], [0,1,-1,0], [0,1,0,-1]])
CONTRASTS = ['learned_mean_minus_random_mean','s3_minus_random_mean','s4_minus_random_mean',
             's3_minus_rand0','s3_minus_rand1','s4_minus_rand0','s4_minus_rand1']


def intervals(values, groups):
    n, m = values.shape
    row_rng = np.random.default_rng(20261120)
    row_draws = np.empty((3000, m))
    for b in range(3000):
        row_draws[b] = values[row_rng.integers(0, n, n)].mean(axis=0)
    unique, inverse = np.unique(groups, return_inverse=True)
    sums = np.zeros((len(unique), m))
    np.add.at(sums, inverse, values)
    counts = np.bincount(inverse)
    group_rng = np.random.default_rng(20261121)
    draws = group_rng.integers(0, len(unique), (3000, len(unique)))
    grouped = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)[:,None]
    return np.quantile(row_draws, [.025,.975],axis=0), np.quantile(grouped,[.025,.975],axis=0),len(unique)


def aggregate(values, rows):
    answer = {}
    strata = {'all': np.ones(len(rows),dtype=bool),
              'high': np.array([not(r['low_similarity'] or r['low_margin']) for r in rows]),
              'low': np.array([r['low_similarity'] or r['low_margin'] for r in rows])}
    for name, selected in strata.items():
        matrix = values[selected]
        selected_rows = [r for r,keep in zip(rows,selected) if keep]
        complete = np.isfinite(matrix).all(axis=1)
        report = {'n':len(matrix),'complete_pairs':int(complete.sum()),
                  'missing_or_invalid_pairs':int((~complete).sum()), 'conditions':{}}
        report['all_row_bounds_pp']={}
        for weight,key in zip(WEIGHTS,CONTRASTS):
            low=np.where(np.isfinite(matrix),matrix,np.where(weight>=0,0,1)) @ weight * 100
            high=np.where(np.isfinite(matrix),matrix,np.where(weight>=0,1,0)) @ weight * 100
            report['all_row_bounds_pp'][key]=[float(low.mean()),float(high.mean())]
        for i,condition in enumerate(NAMES):
            valid = np.isfinite(matrix[:,i])
            report['conditions'][condition] = {'valid':int(valid.sum()),
                'sum':float(np.nansum(matrix[:,i])),
                'mean_valid':float(matrix[valid,i].mean()) if valid.any() else None}
        if complete.any():
            diffs = matrix[complete] @ WEIGHTS.T * 100
            groups = np.array([r['group'] for r,ok in zip(selected_rows,complete) if ok])
            row_ci,group_ci,ng = intervals(diffs,groups)
            report['behavior_groups'] = ng
            report['contrasts_pp'] = {key:{'mean':float(diffs[:,i].mean()),
                'row_bootstrap95':row_ci[:,i].tolist(), 'behavior_bootstrap95':group_ci[:,i].tolist()}
                for i,key in enumerate(CONTRASTS)}
        answer[name] = report
    return answer


def main():
    assert digest(PLAN) == EXPECTED
    rows = load(BASE / 'wjb_mapping255.json')['rows']
    assert len(rows)==2000 and len({r['id'] for r in rows})==2000
    mapping_sha=digest(BASE/'wjb_mapping255.json')
    log = ROOT/'docs/PREREG_LOG.txt'
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with log.open('a') as f:
        f.write(f'{started} FOUR_CONDITION_AGGREGATION_START addendum11SHA={EXPECTED}; first conversational outcome aggregation after pushed commit86620ea. Automated prior processing acknowledged.\n')
    manifest = {}
    result = {'created_utc':started,'plan_sha256':EXPECTED, 'conditions':NAMES,
              'interpretation':'Exploratory, post-alpha0; mapping sensitivity pending is not evidence of robustness.'}
    for folder, key in [('mapped_scores','top1'),('mapped_top2_scores','top2')]:
        values = np.full((2000,4),np.nan)
        counts = {}
        for j,name in enumerate(NAMES):
            found=0
            for i,row in enumerate(rows):
                p=EVAL/folder/name/(row['id']+'.json')
                if not p.exists(): continue
                source=EVAL/'harmful.private'/name/'wildjailbreak_harmful'/(row['id']+'.json')
                record=load(p)
                assert record['signature']['mapping_sha256']==mapping_sha
                assert record['signature']['generation_sha256']==digest(source)
                assert record['behavior_id']==row['candidates'][0 if key=='top1' else 1]['behavior_id']
                manifest[str(p.relative_to(ROOT))]=digest(p)
                if record['label'] in (0,1): values[i,j]=record['label']
                found+=1
            counts[name]=found
        result[key+'_file_counts']=counts
        result[key]=aggregate(values,rows) if all(n==2000 for n in counts.values()) else {'status':'pending_complete_files'}
    refusal=np.zeros((2000,4))
    for j,name in enumerate(NAMES):
        for i,row in enumerate(rows):
            p=EVAL/'harmful.private'/name/'wildjailbreak_harmful'/(row['id']+'.json')
            record=load(p)
            refusal[i,j]=new_rule(record['items'][0]['text'])
            manifest[str(p.relative_to(ROOT))]=digest(p)
    result['v2_refusal']=aggregate(refusal,rows)
    guard_values=np.full((2000,4),np.nan)
    for j,name in enumerate(NAMES):
        for i,row in enumerate(rows):
            p=EVAL/'harmful_guard_scores'/name/(row['id']+'.json')
            if p.exists():
                record=load(p)
                source=EVAL/'harmful.private'/name/'wildjailbreak_harmful'/(row['id']+'.json')
                assert record['signature']['generation_sha256']==digest(source)
                guard_values[i,j]=record['p_unsafe'];manifest[str(p.relative_to(ROOT))]=digest(p)
    result['guard_status']='complete' if np.isfinite(guard_values).all() else 'pending exclusive judge window'
    if result['guard_status']=='complete':
        result['guard_probability']=aggregate(guard_values,rows)
        result['guard_thresholds']={}
        for threshold in [.5,.2,.1,.05,.01]:
            result['guard_thresholds'][str(threshold)]={name:{
                'block_ge':int((guard_values[:,j]>=threshold).sum()),
                'block_gt':int((guard_values[:,j]>threshold).sum()),
                'ties':int((guard_values[:,j]==threshold).sum())} for j,name in enumerate(NAMES)}
    if 'all' in result['top2']:
        signs=[result[k][s]['contrasts_pp']['learned_mean_minus_random_mean']['mean']
               for k in ['top1','top2'] for s in ['all','high','low']]
        result['negative_sign_in_both_references_and_strata']=all(x<0 for x in signs)
        result['robust_abstract_claim']='sign criterion satisfied; only two learned seeds and two directions, abstract is not automatically edited' if all(x<0 for x in signs) else 'sign criterion not satisfied; descriptive only'
    else:
        result['robust_abstract_claim']='pending top2 and strata sensitivity; abstract unchanged'
    mp=EVAL/'four_condition_source_hashes.json';write(mp,manifest)
    result['source_manifest_sha256']=digest(mp)
    path=EVAL/'four_condition_analysis.json';write(path,result)
    with log.open('a') as f:
        f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} FOUR_CONDITION_AGGREGATION_SAVED resultSHA={digest(path)} sourceManifestSHA={digest(mp)}; top2 pending if incomplete, no robust wording or scheduling change.\n')
    print(json.dumps({'sha256':digest(path),'result':result}))


if __name__=='__main__':main()
