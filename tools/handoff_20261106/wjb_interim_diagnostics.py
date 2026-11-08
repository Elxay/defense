"""Four authorized interim units only; never inspect other defense outcomes."""
import ast
import collections
import csv
import datetime
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT=Path('/data/HZX/Def')
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
from judge.refusal import new_rule
from pair500_generate import digest,load,write
BASE=ROOT/'results/audit/pair500';EVAL=BASE/'public255'


def main():
    mapping=load(BASE/'wjb_mapping255.json')['rows']
    source=ROOT/'tools/handoff_20261106/audit.py'
    tree=ast.parse(source.read_text())
    fn=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='v3']
    assert len(fn)==1
    scope={'re':re};exec(compile(ast.Module(body=fn,type_ignores=[]),str(source),'exec'),scope)
    result={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'v2_source_sha256':digest(ROOT/'src/judge/refusal.py'),'v3_source_sha256':digest(source)}
    assigned=collections.Counter(r['candidates'][0]['behavior_id'] for r in mapping)
    result['mapping_distribution']={'behavior_count':200,'zero_count':200-len(assigned),
        'min':min(assigned.values()),'max':max(assigned.values()),'mean':2000/200,
        'histogram':dict(sorted(collections.Counter(assigned.values()).items())),
        'counts_by_behavior_id':dict(sorted(assigned.items()))}
    units={};hashes={}
    for name in ['old_s3','old_s4','rand0','rand1']:
        chars=[];tokens=[];caps=0;caps_no_eos=0;eos_at_cap=0;v2=0;down=0;refused_down=0;union=0;harmful=0
        for row in mapping:
            key=row['id'];p=EVAL/'harmful.private'/name/'wildjailbreak_harmful'/(key+'.json')
            x=load(p);text=x['items'][0]['text'];meta=x['generation']
            tokens.append(meta['new_tokens']);chars.append(len(text));cap=meta['new_tokens']>=2400
            caps+=cap;caps_no_eos+=cap and not meta['eos'];eos_at_cap+=cap and meta['eos']
            r2=new_rule(text);ru=r2 or scope['v3'](text);v2+=r2;union+=ru
            before=load(EVAL/'mapped_scores/alpha0'/(key+'.json'))['label']
            after=load(EVAL/'mapped_scores'/name/(key+'.json'))['label']
            assert before in (0,1) and after in (0,1)
            harmful+=after
            if before==1 and after==0:down+=1;refused_down+=ru
            hashes[str(p.relative_to(ROOT))]=digest(p)
        units[name]={'n':2000,'top1_yes':harmful,'mean_new_tokens':statistics.mean(tokens),'mean_characters':statistics.mean(chars),
            'tokens_at_limit':caps,'limit_without_eos':caps_no_eos,'eos_exactly_at_limit':eos_at_cap,
            'v2_refused':v2,'v2_union_v3_refused':union,'top1_harmful_to_harmless':down,
            'union_refused_among_down':refused_down}
    result['four_conditions']=units
    result['pooled_attribution']={}
    for group,names in [('learned',['old_s3','old_s4']),('random',['rand0','rand1'])]:
        result['pooled_attribution'][group]={k:sum(units[n][k] for n in names) for k in ['top1_harmful_to_harmless','union_refused_among_down']}
    refs=load(EVAL/'alpha0_reference_directional.json')
    result['baseline_reference_labels']={k:refs[k] for k in ['all','high','low','small_margin','random200']}
    report=load(EVAL/'four_condition_analysis.json')
    result['top2']={layer:report['top2'][layer]['contrasts_pp']['learned_mean_minus_random_mean'] for layer in ['all','high','low']}
    result['top2_read_order_note']='First conversational top2 read at07:47:30UTC after addenda12/13 push. Full length/attribution diagnostics computed subsequently; do not backdate them as preceding that read. Top1 unit outcomes had been read in the earlier interim report. No result changed arrangements.'
    result['guard_status']=report['guard_status']
    if 'guard_probability' in report:
        result['guard_output_only_mean_unsafe']={k:v['mean_valid'] for k,v in report['guard_probability']['all']['conditions'].items()}
    hp=EVAL/'four_interim_diagnostic_sources.json';write(hp,hashes);result['generation_hash_manifest_sha256']=digest(hp)
    target=EVAL/'four_interim_diagnostics.json';write(target,result)
    source_sha=digest(target)
    table=ROOT/'paper/data/wjb_four_interim_diagnostics.csv'
    with table.open('w',newline='') as f:
        fields=['condition','n','top1_yes','mean_new_tokens','mean_characters','tokens_at_limit','limit_without_eos','eos_exactly_at_limit','v2_refused','v2_union_v3_refused','top1_harmful_to_harmless','union_refused_among_down','source_file','source_sha256']
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for name,row in units.items():writer.writerow(dict(row,condition=name,source_file=str(target.relative_to(ROOT)),source_sha256=source_sha))
    lines=['\\begin{table}[t]','\\centering\\small','\\begin{tabular}{lrrr}','\\toprule','Behavior reference & $n$ & Harmful & Rate (\\%) \\\\','\\midrule',
        'Top-1 & 2000 & 993 & 49.65 \\\\', 'Top-2 & 2000 & 304 & 15.20 \\\\', 'Random mismatch & 200 & 2 & 1.00 \\\\',
        '\\bottomrule','\\end{tabular}',
        '\\caption{Same official WildJailbreak baseline outputs with different behavior references. Absolute mapped rates are descriptive, not independently validated WildJailbreak ASR. The random mismatch uses a 200-row subset. The frozen dynamic-range gate uses top-1 alone; top-2 would fall below it. Source SHA256: \\texttt{'+source_sha[:12]+'}; full hashes are in the companion CSV.}',
        '\\label{tab:wjb-reference-three}','\\end{table}']
    # Substitute values from the source payload, rather than maintaining constants.
    refs=result['baseline_reference_labels'];values=[('Top-1',2000,refs['all']['top1_yes']),('Top-2',2000,refs['all']['top2_yes']),('Random mismatch',refs['random200']['n'],refs['random200']['random_label_yes'])]
    lines[6:9]=[f'{name} & {n} & {yes} & {100*yes/n:.2f} \\\\' for name,n,yes in values]
    (ROOT/'paper/tables/wjb_reference_three.tex').write_text('\n'.join(lines)+'\n')
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:
        f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} FOUR_INTERIM_DIAGNOSTICS SHA={digest(target)}; actual conversational top2 first read07:47:30UTC after addenda12/13 push, full length/attribution diagnostics calculated afterward. Prior automatic aggregation finished03:34UTC; not a before-machine-processing freeze. Nine-unit unseen outcomes not inspected.\n')
    print(json.dumps({'sha256':digest(target),'result':result}))


if __name__=='__main__':main()
