"""Additional already-authorized descriptive counts and deterministic audit replay."""
from pathlib import Path
import datetime
import hashlib
import json
import sys
import tempfile
import numpy as np
from scipy.stats import t

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'public_followup_20261109';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
import public_refusal_ordered_read as public
import wjb_nine_ordered_read as harmful
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def interval(values):
    x=np.asarray(values,dtype=float);x=x[np.isfinite(x)];n=len(x);mean=float(x.mean());sd=float(x.std(ddof=1)) if n>1 else None
    half=float(t.ppf(.975,n-1)*sd/np.sqrt(n)) if n>1 else None
    return {'n':n,'mean_pp':mean,'sd_pp':sd,'t95_pp':[mean-half,mean+half] if half is not None else None,'df':n-1}

def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();report={}
    for dataset in public.DATASETS:
        _,m=public.matrix(dataset,'v2');unit=[]
        for j,name in enumerate(public.NAMES):
            d=(m[:,j]-m[:,0])*100
            unit.append({'condition':name,'refused':int(m[:,j].sum()),'n':len(m),'absolute_refusal_pct':float(m[:,j].mean()*100),'change_vs_alpha0_pp':float(d.mean()),'within_prompt_paired_t':interval(d)})
        report[dataset]={'units':unit,'across_five_seed_changes_t':interval([x['change_vs_alpha0_pp'] for x in unit[1:6]]),'interpretation':'Per-condition t interval is over prompt-paired operational labels for this vector, not repeated training runs. Seed t uses five observed learned-minus-baseline changes; samples are small/shared and not population independence proof.'}
    save(OUT/'absolute_refusal_and_baseline_changes.json',{'utc':now,'script_sha256':sha(Path(__file__)),'datasets':report,'primary_rule':'v2 unchanged','post_hoc_descriptive':True})
    original_out=public.OUT
    with tempfile.TemporaryDirectory(prefix='def_recall_replay_') as directory:
        public.OUT=Path(directory);result=public.stage('samples');checks=[]
        for name in ['recall_blind.private.json','recall_mapping.private.json','recall_selection_groups.json']:
            old=sha(original_out/name);new=sha(public.OUT/name);checks.append({'file':name,'old_sha256':old,'regenerated_sha256':new,'byte_equal':old==new});assert old==new
        old=public.load(original_out/'recall_selection_manifest.json');new=public.load(public.OUT/'recall_selection_manifest.json');old.pop('utc');new.pop('utc');assert old==new
        public.OUT=original_out
    save(OUT/'sampling_replay_checks.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'manifest_equal_excluding_new_creation_utc':True,'old_files_untouched':True,'source_sha256':sha(ROOT/'tools/handoff_20261106/public_refusal_ordered_read.py')})
    names=['alpha0']+harmful.NAMES;v2,union=harmful.rule_values();wgref=harmful.labels('WildGuard',names,'Response refusal');decomp={}
    for judge in ['HB_top1','WildGuard']:
        h=harmful.labels(judge,names);data=[]
        for j,name in enumerate(names):
            keep=np.isfinite(h[:,0])&np.isfinite(h[:,j]);a=h[keep,0];b=h[keep,j]
            x={'condition':name,'comparison_valid_n':int(keep.sum()),'harmful_change_vs_alpha0_pp':float((b-a).mean()*100),'baseline_harmful_n':int(a.sum()),'down':int(((a==1)&(b==0)).sum()),'baseline_nonharmful_n':int((a==0).sum()),'up':int(((a==0)&(b==1)).sum()),'v2_refusal_pct':float(v2[:,j].mean()*100),'union_refusal_pct':float(union[:,j].mean()*100),'WG_refusal_yes':int(np.nansum(wgref[:,j])),'WG_refusal_invalid':int(np.isnan(wgref[:,j]).sum()),'rules':{}}
            for label,r in [('v2',v2),('union',union)]:
                baseline_negative=(r[keep,0]==0);beta=float(a[baseline_negative].mean());delta=float((r[keep,j]-r[keep,0]).mean());negative=(r[keep,j]==0)
                predicted=-delta*beta*100
                x['rules'][label]={'nonrefusal_valid_n':int(negative.sum()),'harmful_among_nonrefusal_pct':float(b[negative].mean()*100) if negative.any() else None,'baseline_harmful_among_nonrefusal_pct':beta*100,'predicted_harmfulness_change_pp':predicted,'observed_harmfulness_change_pp':x['harmful_change_vs_alpha0_pp'],'observed_minus_predicted_pp':x['harmful_change_vs_alpha0_pp']-predicted}
            data.append(x)
        decomp[judge]={'units':data,'across_five_seed_harmful_changes_t':interval([x['harmful_change_vs_alpha0_pp'] for x in data[1:6]])}
    save(OUT/'refusal_decomposition.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha(Path(__file__)),'judges':decomp,'status':'post-hoc descriptive after primary read; conditional decomposition is not a causal mechanism test','INVALID':'pair-specific valid fields counted; no rows removed from retained dataset'})
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{p.name:sha(p) for p in OUT.glob('*.json')},'sampling_all_three_byte_equal':True,'public_across_seed_t':{d:x['across_five_seed_changes_t'] for d,x in report.items()},'unsafe_units':report['xstest_unsafe']['units']}
    save(OUT/'cpu_followup_manifest.json',result)
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{result["utc"]} PUBLIC_FOLLOWUP_COUNTS sample replay3/3 byte-identical; decompositionSHA={sha(OUT/"refusal_decomposition.json")} manifestSHA={sha(OUT/"cpu_followup_manifest.json")} posthoc descriptive; no PAIR effects read.\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
