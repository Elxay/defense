"""Nine separately invoked, chained, time-gated WJB reads. No GPU scheduling."""
import argparse
import ast
import collections
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import sys

import numpy as np

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'nine_read_20261109'
NAMES=['old_s3','old_s4','old_s5','old_s6','old_s7','rand0','rand1','rand2','rand3']
FIELDS=['Harmful request','Harmful response','Response refusal']
STAGES=['status','baseline_hashes','main_contrast','sign_consistency','unit_permutation','downflip_refusal','refusal_agreement','invalid_ids','prediction']
UNLOCK=datetime.datetime(2026,11,8,23,tzinfo=datetime.timezone.utc)

def utc():return datetime.datetime.now(datetime.timezone.utc)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp')
    t.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');os.replace(t,p)
def directory_manifest(folder):return {p.name:sha(p) for p in sorted(folder.glob('*.json'))}
def fingerprint(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def score_dir(judge,name):return BASE/('public255/mapped_scores/'+name if judge=='HB_top1' else 'wildguard/'+name+'_scores')
def generation_path(name,key):
    if name=='alpha0' and load(BASE/'public255/alpha0_active_baseline.json')['lane']=='native':return BASE/'public_wjb_a0.private'/(key+'.json')
    return BASE/'public255/harmful.private'/name/'wildjailbreak_harmful'/(key+'.json')
def check_clock():
    if utc()<UNLOCK:raise SystemExit('LOCKED until 2026-11-08T23:00:00Z / 08:00 JST')
def mapping():
    rows=load(BASE/'wjb_mapping255.json')['rows'];assert len(rows)==2000
    assert len({r['id'] for r in rows})==2000
    assert sum(bool(r['low_similarity'] or r['low_margin']) for r in rows)==311
    return rows


def labels(judge,names,field='Harmful response'):
    rows=mapping();values=np.full((len(rows),len(names)),np.nan)
    for j,name in enumerate(names):
        pinned=(load(OUT/(judge+'_alpha0_file_manifest.json')) if name=='alpha0' else load(OUT/'score_file_manifest.json')[str(score_dir(judge,name).relative_to(ROOT))])
        for i,row in enumerate(rows):
            path=score_dir(judge,name)/(row['id']+'.json');raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==pinned[path.name]
            x=json.loads(raw);assert x['id']==row['id']
            if judge=='HB_top1':
                assert x['behavior_id']==row['candidates'][0]['behavior_id']
                value=x['label']
            else:value={'yes':1,'no':0}.get(x['labels'].get(field))
            if value in (0,1):values[i,j]=value
    return values


def paired_summary(matrix,groups):
    weights=np.array([.2]*5+[-.25]*4)
    complete=np.isfinite(matrix).all(axis=1);n=len(matrix)
    low=np.where(np.isfinite(matrix),matrix,np.where(weights>=0,0,1))@weights*100
    high=np.where(np.isfinite(matrix),matrix,np.where(weights>=0,1,0))@weights*100
    result={'retained_rows':n,'complete_pair_rows':int(complete.sum()),'invalid_pair_rows':int((~complete).sum()),
        'all_rows_identification_bounds_pp':[float(low.mean()),float(high.mean())],
        'conditions':{name:{'yes':int(np.nansum(matrix[:,j])),'valid':int(np.isfinite(matrix[:,j]).sum()),'invalid':int(np.isnan(matrix[:,j]).sum()),'denominator':n,
            'yes_over_all_rows_pct':100*float(np.nansum(matrix[:,j]))/n,'bounds_pct':[100*float(np.nansum(matrix[:,j]))/n,100*float(np.nansum(matrix[:,j])+np.isnan(matrix[:,j]).sum())/n]} for j,name in enumerate(NAMES)}}
    assert complete.any()
    diff=matrix[complete]@weights*100;groups=np.asarray(groups);uniq,inverse=np.unique(groups,return_inverse=True)
    all_low=np.bincount(inverse,weights=low,minlength=len(uniq));all_high=np.bincount(inverse,weights=high,minlength=len(uniq));all_n=np.bincount(inverse)
    result['all_behavior_identification_bounds_pp']=[float(np.mean(all_low/all_n)),float(np.mean(all_high/all_n))]
    sums=np.bincount(inverse[complete],weights=diff,minlength=len(uniq));counts=np.bincount(inverse[complete],minlength=len(uniq));valid_groups=counts>0
    group_means=sums[valid_groups]/counts[valid_groups]
    row_rng=np.random.default_rng(20261120);row_draws=np.empty(3000)
    for k in range(0,3000,100):row_draws[k:k+100]=diff[row_rng.integers(0,len(diff),(100,len(diff)))].mean(axis=1)
    rng=np.random.default_rng(20261121);draws=rng.integers(0,len(uniq),(3000,len(uniq)))
    denom=counts[draws].sum(axis=1);assert np.all(denom>0)
    cluster=sums[draws].sum(axis=1)/denom
    gm=np.full(len(uniq),np.nan);gm[valid_groups]=group_means
    equal=np.nanmean(gm[draws],axis=1)
    lower_draw=all_low[draws].sum(axis=1)/all_n[draws].sum(axis=1)
    upper_draw=all_high[draws].sum(axis=1)/all_n[draws].sum(axis=1)
    result.update(conditional_complete_pair_mean_pp=float(diff.mean()),row_bootstrap95_pp=np.quantile(row_draws,[.025,.975]).tolist(),
        behavior_cluster_bootstrap95_pp=np.quantile(cluster,[.025,.975]).tolist(),behavior_count=len(uniq),behaviors_with_valid_pairs=int(valid_groups.sum()),
        conditional_equal_behavior_mean_pp=float(group_means.mean()),equal_behavior_bootstrap95_pp=np.quantile(equal,[.025,.975]).tolist(),
        all_rows_behavior_bootstrap_identification_envelope95_pp=[float(np.quantile(lower_draw,.025)),float(np.quantile(upper_draw,.975))],
        interpretation='Point/ordinary intervals condition on explicitly counted complete pairs; all retained rows also have identification bounds. Intervals condition on the observed vector units, not unit populations.')
    return result


def agreement(a,b):
    valid=np.isfinite(a)&np.isfinite(b);x=a[valid].astype(int);y=b[valid].astype(int);n=len(x)
    cells={f'v2{i}_WG{j}':int(((x==i)&(y==j)).sum()) for i in [0,1] for j in [0,1]}
    if n:
        po=float((x==y).mean());pe=float(x.mean()*y.mean()+(1-x.mean())*(1-y.mean()))
        kappa=(po-pe)/(1-pe) if abs(1-pe)>1e-14 else None
    else:kappa=None
    tp=cells['v21_WG1'];fn=cells['v20_WG1'];fp=cells['v21_WG0']
    return {'n_retained':len(a),'valid_pairs':n,'invalid_pairs':int((~valid).sum()),'cells':cells,'kappa':kappa,
        'model_referenced_v2_recall':tp/(tp+fn) if tp+fn else None,'model_referenced_v2_precision':tp/(tp+fp) if tp+fp else None,
        'v2_refusal_count':int(np.nansum(a)),'WG_refusal_yes':int(np.nansum(b)),'WG_refusal_invalid':int(np.isnan(b).sum())}


def rules():
    sys.path.insert(0,str(ROOT/'src'));from judge.refusal import new_rule
    source=ROOT/'tools/handoff_20261106/audit.py';tree=ast.parse(source.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='v3'];assert len(nodes)==1
    scope={'re':re};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),scope)
    return new_rule,scope['v3']


def rule_values():
    rows=mapping();v2,union=np.zeros((2000,10)),np.zeros((2000,10));fn2,fn3=rules()
    for j,name in enumerate(['alpha0']+NAMES):
        for i,row in enumerate(rows):
            x=load(generation_path(name,row['id']));text=x['text'] if 'text' in x else x['items'][0]['text']
            v2[i,j]=fn2(text);union[i,j]=bool(v2[i,j] or fn3(text))
    return v2,union


def do_stage(stage):
    rows=mapping();groups=np.array([r['group'] for r in rows]);low=np.array([r['low_similarity'] or r['low_margin'] for r in rows]);strata={'all':np.ones(2000,dtype=bool),'high':~low,'low':low}
    if stage=='status':
        sys.path.insert(0,str(ROOT/'tools/handoff_20261106'));from operational_metadata import capture
        status=capture();manifest={};units={};mapping_sha=sha(BASE/'wjb_mapping255.json')
        for name in NAMES:
            units[name]={}
            input_meta=load(BASE/'wildguard'/(name+'_input_manifest.json'))
            assert input_meta['input_sha256']==sha(BASE/'wildguard'/(name+'_inputs.private.json'))
            for judge in ['HB_top1','WildGuard']:
                folder=score_dir(judge,name);mp=directory_manifest(folder);assert set(mp)=={r['id']+'.json' for r in rows}
                manifest[str(folder.relative_to(ROOT))]=mp
                invalid=collections.Counter()
                for row in rows:
                    x=load(folder/(row['id']+'.json'))
                    if judge=='HB_top1':
                        assert x['signature']['generation_sha256']==sha(generation_path(name,row['id']))
                        assert x['signature']['mapping_sha256']==mapping_sha
                        invalid['label']+=x['label'] not in (0,1)
                    else:
                        assert x['signature']['input_sha256']==input_meta['input_sha256']
                        for field in FIELDS:invalid[field]+=x['labels'].get(field) not in ['yes','no']
                units[name][judge]={'files':2000,'invalid_counts':dict(invalid),'directory_fingerprint_sha256':fingerprint(mp),'directory':str(folder.relative_to(ROOT))}
        save(OUT/'score_file_manifest.json',manifest)
        return {'operational_status':status,'units':units,'score_manifest_sha256':sha(OUT/'score_file_manifest.json'),'labels_used_only_for_invalid_counts':True}
    if stage=='baseline_hashes':
        report={}
        for judge in ['HB_top1','WildGuard']:
            mp=directory_manifest(score_dir(judge,'alpha0'));assert len(mp)==2000
            report[judge]={'files':2000,'directory_fingerprint_sha256':fingerprint(mp)}
            save(OUT/(judge+'_alpha0_file_manifest.json'),mp)
        previous_hb=load(BASE/'wildguard/alpha0_harmbench_source_hashes.json')
        assert len(previous_hb)==2000
        for name,expected in previous_hb.items():assert sha(ROOT/name)==expected
        previous_wg={x['id']:x for x in load(BASE/'wildguard/alpha0_labels.private.json')}
        current_wg={x['id']:x for x in (load(p) for p in score_dir('WildGuard','alpha0').glob('*.json'))}
        assert fingerprint(previous_wg)==fingerprint(current_wg)
        report['historical_bytes_verified']={'HB_prior_2000_file_hashes_match':True,'WG_prior_cached_records_match':True,
            'HB_prior_manifest_sha256':sha(BASE/'wildguard/alpha0_harmbench_source_hashes.json'),'WG_prior_cache_sha256':sha(BASE/'wildguard/alpha0_labels.private.json')}
        report['interpretation']='Previously read alpha0 outputs: byte hashes only, no baseline rate recalculation or new interpretation.'
        return report
    if stage=='main_contrast':
        return {judge:paired_summary(labels(judge,NAMES),groups) for judge in ['HB_top1','WildGuard']}
    if stage=='sign_consistency':
        report={}
        for judge in ['HB_top1','WildGuard']:
            matrix=labels(judge,NAMES);report[judge]={name:paired_summary(matrix[mask],groups[mask]) for name,mask in strata.items()}
        signs=[report[j][layer]['conditional_complete_pair_mean_pp'] for j in ['HB_top1','WildGuard'] for layer in strata]
        same=all(x<0 for x in signs) or all(x>0 for x in signs)
        top2={n:len(list((BASE/'public255/mapped_top2_scores'/n).glob('*.json'))) for n in NAMES}
        report['cross_judge_and_strata_same_sign']=same;report['all_negative']=all(x<0 for x in signs)
        report['top2_coverage']=top2;report['top2_full_robustness']='pending' if any(v!=2000 for v in top2.values()) else 'complete outputs; corresponding sensitivity still must be read'
        report['wording']='judge-dependent; report both' if not same else 'cross-judge sign criterion satisfied; retain earlier top2 requirement, no automatic abstract edit'
        return report
    if stage=='unit_permutation':
        result={}
        for judge in ['HB_top1','WildGuard']:
            m=labels(judge,NAMES);complete=np.isfinite(m).all(axis=1);a=m[complete];g=groups[complete]
            bygroup=np.array([a[g==k].mean(axis=0) for k in np.unique(g)])
            result[judge]={}
            for estimand,means in [('row',a.mean(axis=0)*100),('equal_behavior',bygroup.mean(axis=0)*100)]:
                observed=float(means[:5].mean()-means[5:].mean());perms=[]
                for selected in itertools.combinations(range(9),5):
                    rest=[i for i in range(9) if i not in selected];perms.append(float(means[list(selected)].mean()-means[rest].mean()))
                assert len(perms)==126
                result[judge][estimand]={'complete_pair_rows':int(complete.sum()),'unit_means_pct':dict(zip(NAMES,means.tolist())),'contrast_pp':observed,
                    'allocations':126,'p_lower':sum(x<=observed+1e-12 for x in perms)/126,'p_two_sided_absolute':sum(abs(x)>=abs(observed)-1e-12 for x in perms)/126,
                    'all20_seed_direction_differences_pp':{NAMES[i]+'-'+NAMES[j]:float(means[i]-means[j]) for i in range(5) for j in range(5,9)},
                    'leave_one_out_pp':{name:float(np.delete(means[:5],k).mean()-means[5:].mean()) if k<5 else float(means[:5].mean()-np.delete(means[5:],k-5).mean()) for k,name in enumerate(NAMES)},
                    'caveat':'Exploratory unit-exchangeability assumption; five training seeds and four random directions. Missing rows explicitly conditioned upon; full-row bounds are in stage3.'}
        return result
    if stage=='downflip_refusal':
        v2,union=rule_values();refusal=labels('WildGuard',['alpha0']+NAMES,'Response refusal');result={}
        for judge in ['HB_top1','WildGuard']:
            harmful=labels(judge,['alpha0']+NAMES);units={};pooled={}
            for j,name in enumerate(NAMES,1):
                down=(harmful[:,0]==1)&(harmful[:,j]==0);n=int(down.sum());rr=refusal[down,j];yes=int(np.nansum(rr));invalid=int(np.isnan(rr).sum())
                units[name]={'downflip_n':n,'WG_refusal_yes':yes,'WG_refusal_no':int((rr==0).sum()),'WG_refusal_invalid':invalid,
                    'WG_fraction_bounds':[yes/n,(yes+invalid)/n] if n else None,'v2_refusal':int(v2[down,j].sum()),'union_refusal':int(union[down,j].sum()),
                    'v2_fraction':float(v2[down,j].mean()) if n else None,'union_fraction':float(union[down,j].mean()) if n else None}
            for kind,names in [('learned',NAMES[:5]),('random',NAMES[5:])]:
                counts={k:sum(units[name][k] for name in names) for k in ['downflip_n','WG_refusal_yes','WG_refusal_no','WG_refusal_invalid','v2_refusal','union_refusal']};n=counts['downflip_n']
                counts['fractions']={k:counts[k]/n if n else None for k in ['WG_refusal_yes','v2_refusal','union_refusal']};pooled[kind]=counts
            result[judge]={'downflip_definition':judge+' baseline harmful to condition harmless, both labels valid','units':units,'pooled_correlated_events':pooled}
        result['caveat']='Repeated prompts across conditions are correlated. Model refusal attribution is descriptive, not a causal mechanism or human-certified fraction.'
        return result
    if stage=='refusal_agreement':
        v2,_=rule_values();wg=labels('WildGuard',['alpha0']+NAMES,'Response refusal')
        return {'conditions':{name:{layer:agreement(v2[mask,j],wg[mask,j]) for layer,mask in strata.items()} for j,name in enumerate(['alpha0']+NAMES)},
            'v2_source_sha256':sha(ROOT/'src/judge/refusal.py'),'primary_rule':'v2 unchanged; WildGuard sensitivity/model reference only, not human calibration'}
    if stage=='invalid_ids':
        result={}
        for name in ['alpha0']+NAMES:
            ids={field:[] for field in FIELDS};over=[];reasons={};hb=[];maximum=0
            for row in rows:
                key=row['id'];x=load(score_dir('WildGuard',name)/(key+'.json'));maximum=max(maximum,x['input_tokens'])
                for field in FIELDS:
                    if x['labels'].get(field) not in ['yes','no']:ids[field].append(key);reasons[key]=x['invalid_reason']
                if x['input_tokens']>4096:over.append(key)
                if load(score_dir('HB_top1',name)/(key+'.json'))['label'] not in (0,1):hb.append(key)
            result[name]={'WG_field_ids':ids,'WG_reason_by_id':reasons,'input_gt4096_ids':over,'max_input_tokens':maximum,'HB_invalid_ids':hb}
        return result
    if stage=='prediction':
        main=load(OUT/'03_main_contrast.json')['result'];observed=main['WildGuard']['conditional_complete_pair_mean_pp']
        return {'frozen_prediction_pp':-17.33,'observed_WG_complete_pair_contrast_pp':observed,'observed_all2000_identification_bounds_pp':main['WildGuard']['all_rows_identification_bounds_pp'],
            'observed_minus_prediction_pp':observed+17.33,'same_negative_sign':observed<0,'numerical_tolerance':None,
            'interpretation':'Descriptive comparison only; the prediction used a four-unit HB anchor whereas this is nine units. No pass/fail threshold, mechanism claim, scheduling or stopping change.'}
    raise AssertionError(stage)


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=STAGES);args=p.parse_args();check_clock()
    receipt=load(OUT/'execution_publication.json');assert receipt['script_sha256']==sha(Path(__file__))
    for name,expected in receipt['source_sha256'].items():assert sha(ROOT/name)==expected,name
    index=STAGES.index(args.stage)+1;previous=[]
    for i,stage in enumerate(STAGES[:index-1],1):
        path=OUT/f'{i:02d}_{stage}.json';assert path.exists();entry=load(path);assert entry['step']==i
        previous.append({'file':str(path.relative_to(ROOT)),'sha256':sha(path)})
    path=OUT/f'{index:02d}_{args.stage}.json';assert not path.exists(),'Each stage is immutable; inspect existing output instead of silently overwriting it.'
    OUT.mkdir(parents=True,exist_ok=True);started=utc().isoformat()
    result=do_stage(args.stage);finished=utc().isoformat()
    entry={'step':index,'stage':args.stage,'started_utc':started,'saved_utc':finished,'unlock_utc':UNLOCK.isoformat(),'previous_steps':previous,'script_sha256':sha(Path(__file__)),'result':result}
    save(path,entry)
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{finished} NINE_UNIT_ORDERED_READ step={index} stage={args.stage} started={started} output={path.relative_to(ROOT)} SHA256={sha(path)} prior_steps={len(previous)}; no scheduling or stopping change.\n')
    public={'step':index,'stage':args.stage,'saved_utc':finished,'sha256':sha(path)}
    if args.stage in ['main_contrast','prediction']:public['result']=result
    elif args.stage=='status':public['units']=result['units']
    elif args.stage=='sign_consistency':public['criterion']={k:result[k] for k in ['cross_judge_and_strata_same_sign','all_negative','top2_coverage','wording']}
    print(json.dumps(public,ensure_ascii=False))


if __name__=='__main__':main()
