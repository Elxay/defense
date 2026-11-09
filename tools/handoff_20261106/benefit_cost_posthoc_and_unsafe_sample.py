"""Requested post-hoc rate juxtaposition and targeted unsafe discordance read list."""
from pathlib import Path
import datetime
import hashlib
import json
import sys
import numpy as np

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'lease_priority_followup_20261109'
sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
import public_refusal_ordered_read as pub
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def main():
    source=BASE/'nine_read_20261109/supplemental_tables.json';units=json.loads(source.read_text())['unit_table'];values=np.array([x['v2_refusal_pct'] for x in units]);rows=[]
    def row(name,n,a,l,r):return {'prompt_set':name,'n':n,'alpha0_refusal_pct':float(a),'learned_mean_refusal_pct':float(l),'random_mean_refusal_pct':float(r),'learned_minus_alpha0_pp':float(l-a),'learned_minus_random_pp':float(l-r)}
    rows.append(row('WJB evaluation adversarial harmful',2000,values[0],values[1:6].mean(),values[6:].mean()))
    names=['wildjailbreak_benign','or_hard','xstest_safe','xstest_unsafe']
    for name in names:
        _,m=pub.matrix(name,'v2');rates=m.mean(axis=0)*100;rows.append(row(name,len(m),rates[0],rates[1:6].mean(),rates[6:].mean()))
    gaps={k:rows[0][k]-rows[1][k] for k in ['alpha0_refusal_pct','learned_mean_refusal_pct','random_mean_refusal_pct']}
    output={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'post_hoc':True,'primary_refusal_rule':'v2 unchanged','rows':rows,'unpaired_harmful_minus_benign_refusal_gap_pp':gaps,'scope':'WJB sets have different construction and sizes and are not paired; gaps are descriptive, not selectivity or a mechanism test. OR-Hard is not a paired unwrapped control. Juxtapose with docs246/250 matched prompt results.','source_sha256':{'harmful':sha(source),'public_rules':sha(BASE/'public_read_20261109/rule_labels.json')},'script_sha256':sha(Path(__file__))}
    save(OUT/'benefit_cost_posthoc.json',output)
    payload={name:{r['id']:r for r in pub.payload(name) if r['dataset']=='xstest_unsafe'} for name in pub.NAMES}
    _,m=pub.matrix('xstest_unsafe','v2');baseline=list(payload['alpha0']);assert len(baseline)==200
    selected=[];counts={}
    for j,name in enumerate(pub.NAMES[1:6],1):
        down=[k for i,k in enumerate(baseline) if m[i,0]==1 and m[i,j]==0];up=[k for i,k in enumerate(baseline) if m[i,0]==0 and m[i,j]==1]
        counts[name]={'down':len(down),'up':len(up),'net':len(down)-len(up)}
        for k in down:
            r=payload[name][k];selected.append({'condition':name,'id':k,'original_id':r['original_id'],'prompt':r['prompt'],'response':r['response'],'baseline_response':payload['alpha0'][k]['response']})
    permutation=np.random.default_rng(20261201).permutation(len(selected));blind=[];mapping=[]
    for index,j in enumerate(permutation,1):
        r=selected[int(j)];blind.append({'review_index':index,'task':r['prompt'],'response':r['response']});mapping.append({'review_index':index,**{k:v for k,v in r.items() if k not in ['prompt','response','baseline_response']}})
    save(OUT/'unsafe_downflip_blind.private.json',blind);save(OUT/'unsafe_downflip_mapping.json',mapping)
    selection={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':'all baseline-v2-positive -> learned-v2-negative condition-prompt pairs; targeted posthoc, not population sampling','seed_for_display_only':20261201,'n_condition_prompt_pairs':len(selected),'unique_prompt_ids':len({r['id'] for r in selected}),'counts':counts,'blind_sha256':sha(OUT/'unsafe_downflip_blind.private.json'),'coded_mapping_sha256':sha(OUT/'unsafe_downflip_mapping.json'),'fields_shown':['review_index','full original task','full stored120-token response'],'fields_hidden':['condition','baseline/v2/WG labels'],'shared_context':True,'human_calibration':False}
    save(OUT/'unsafe_downflip_selection.json',selection)
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{selection["utc"]} BENEFIT_COST_JUXTAPOSITION_POSTHOC SHA={sha(OUT/"benefit_cost_posthoc.json")} targeted unsafe review selected n={len(selected)} unique={selection["unique_prompt_ids"]} selectionSHA={sha(OUT/"unsafe_downflip_selection.json")} before full-text read; no PAIR outcome read.\n')
    print(json.dumps({'table':rows,'gaps':gaps,'table_sha256':sha(OUT/'benefit_cost_posthoc.json'),'selection':selection},ensure_ascii=False))

if __name__=='__main__':main()
