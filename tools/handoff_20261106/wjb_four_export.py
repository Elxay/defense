"""Export only aggregate values/provenance to CSV, LaTeX and the handoff report."""
import csv
import datetime
import io
import collections
from pathlib import Path

from pair500_generate import digest,load,write
ROOT=Path('/data/HZX/Def')
EVAL=ROOT/'results/audit/pair500/public255'


def baseline_reference_table():
    rows=load(ROOT/'results/audit/pair500/wjb_mapping255.json')['rows']
    top1={r['id']:load(EVAL/'mapped_scores/alpha0'/(r['id']+'.json')) for r in rows}
    top2={r['id']:load(EVAL/'mapped_top2_scores/alpha0'/(r['id']+'.json')) for r in rows}
    result={}
    for name,selected in [('all',rows),('high',[r for r in rows if not(r['low_similarity'] or r['low_margin'])]),
                          ('low',[r for r in rows if r['low_similarity'] or r['low_margin']]),
                          ('small_margin',[r for r in rows if r['low_margin']])]:
        counts=collections.Counter((top1[r['id']]['label'],top2[r['id']]['label']) for r in selected)
        result[name]={'n':len(selected),'top1_yes':sum(top1[r['id']]['label']==1 for r in selected),
            'top2_yes':sum(top2[r['id']]['label']==1 for r in selected),'both_no':counts[0,0],
            'top1_yes_top2_no':counts[1,0],'top1_no_top2_yes':counts[0,1], 'both_yes':counts[1,1],
            'invalid':sum(v for k,v in counts.items() if None in k)}
    paths=sorted((EVAL/'random_reference_scores/alpha0').glob('*.json'))
    randoms=[load(p) for p in paths];originals=[top1[p.stem] for p in paths]
    result['random200']={'n':len(paths),'top1_mean_p_yes':sum(v['p_yes'] for v in originals)/len(paths),
        'random_mean_p_yes':sum(v['p_yes'] for v in randoms)/len(paths),
        'top1_label_yes':sum(v['label']==1 for v in originals),'random_label_yes':sum(v['label']==1 for v in randoms),
        'random_invalid':sum(v['label'] is None for v in randoms)}
    target=EVAL/'alpha0_reference_directional.json'
    if target.exists():
        # Avoid last-bit mean changes solely from filesystem enumeration order.
        old=load(target)
        for layer in ['all','high','low','small_margin']:assert old[layer]==result[layer]
        for key,value in result['random200'].items():assert abs(old['random200'][key]-value)<1e-12
    else:write(target,result)


def main():
    baseline_reference_table()
    baseline=EVAL/'alpha0_reference_directional.json'
    analysis=EVAL/'four_condition_analysis.json'
    b,a=load(baseline),load(analysis)
    records=[]
    for layer in ['all','high','low','small_margin']:
        row=b[layer]
        records.append({'analysis':'baseline_reference','layer':layer,'n':row['n'],
            'top1_yes':row['top1_yes'],'top2_yes':row['top2_yes'],
            'yes_to_no':row['top1_yes_top2_no'],'no_to_yes':row['top1_no_top2_yes'],
            'both_no':row['both_no'],'both_yes':row['both_yes'],
            'file':str(baseline.relative_to(ROOT)),'sha256':digest(baseline)})
    for reference in ['top1','top2']:
        if 'all' not in a[reference]:continue
        for layer in ['all','high','low']:
            row=a[reference][layer]
            v=row['contrasts_pp']['learned_mean_minus_random_mean']
            records.append({'analysis':'learned_minus_random','reference':reference,'layer':layer,
                'n':row['n'],'difference_pp':v['mean'],
                'row95_low':v['row_bootstrap95'][0],'row95_high':v['row_bootstrap95'][1],
                'group95_low':v['behavior_bootstrap95'][0],'group95_high':v['behavior_bootstrap95'][1],
                'file':str(analysis.relative_to(ROOT)),'sha256':digest(analysis)})
    fields=list(dict.fromkeys(k for row in records for k in row))
    target=ROOT/'paper/data/wjb_official_mapping.csv'
    with target.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(records)
    # Render from the exported CSV; manuscripts do not copy numbers by hand.
    with target.open() as f: rows=list(csv.DictReader(f))
    tex=['\\begin{table}[t]','\\centering\\small','\\begin{tabular}{lrrr}',
         '\\toprule','Layer & $n$ & Top-1 (\\%) & Top-2 (\\%) \\\\', '\\midrule']
    for row in rows:
        if row['analysis']!='baseline_reference':continue
        n=int(row['n']);label={'all':'All','high':'High confidence','low':'Low confidence','small_margin':'Small margin'}[row['layer']]
        tex.append(f"{label} & {n} & {100*int(row['top1_yes'])/n:.2f} & {100*int(row['top2_yes'])/n:.2f} \\\\")
    tex+=['\\bottomrule','\\end{tabular}',
          '\\caption{Official WildJailbreak evaluation baseline: mapped-reference judge ASR, descriptive only. Top-2 substitution measures reference sensitivity, not mapping error. Source SHA256: \\texttt{'+digest(baseline)[:12]+'}; full source paths and hashes accompany the exported CSV.}',
          '\\label{tab:wjb-official-mapping}','\\end{table}']
    (ROOT/'paper/tables/wjb_official_mapping.tex').write_text('\n'.join(tex)+'\n')
    doc=['# WJB official evaluation: frozen four-condition read',
         '',f'Generated UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}',
         '',f'Analysis plan SHA256: `{a["plan_sha256"]}`.',
         f'Baseline table source: `{baseline.relative_to(ROOT)}` SHA256 `{digest(baseline)}`.',
         f'Four-condition source: `{analysis.relative_to(ROOT)}` SHA256 `{digest(analysis)}`.',
         '', '| Layer | n | Top1 yes | Top2 yes | yes-to-no | no-to-yes | both-no | both-yes |',
         '|---|---:|---:|---:|---:|---:|---:|---:|']
    for layer in ['all','high','low','small_margin']:
        r=b[layer];doc.append('| '+layer+' | '+' | '.join(str(r[k]) for k in ['n','top1_yes','top2_yes','top1_yes_top2_no','top1_no_top2_yes','both_no','both_yes'])+' |')
    r=b['random200']
    doc+=['',f'Random-reference 200 rows: top1 mean pair-normalized P(Yes) {100*r["top1_mean_p_yes"]:.4f}%, random mean {100*r["random_mean_p_yes"]:.4f}%. Greedy-label ASR is separately {r["top1_label_yes"]}/200 versus {r["random_label_yes"]}/200. These are distinct statistics.',
          '', '| Reference/layer | Learned-minus-random pp | Row bootstrap95 | Assigned-behavior bootstrap95 |',
          '|---|---:|---|---|']
    for reference in ['top1','top2']:
        if 'all' not in a[reference]:continue
        for layer in ['all','high','low']:
            c=a[reference][layer]['contrasts_pp']['learned_mean_minus_random_mean']
            doc.append(f'| {reference}/{layer} | {c["mean"]:.4f} | {c["row_bootstrap95"]} | {c["behavior_bootstrap95"]} |')
    doc+=['',a['robust_abstract_claim'],
          '', 'All rows are retained. Top1 assigned groups are inferred and imperfect. Item/group bootstrap intervals condition on two learned seeds and two fixed random directions; they are not seed-population intervals. Top2 and Guard sensitivity are post-alpha0 decisions.',
          '', 'The alpha0 top1/top2 and random-reference contrasts establish sensitivity to the supplied behavior. Whether mapping mistakes attenuate or reverse a defense contrast remains untested; sign preservation is not guaranteed. 49.65% lies below the frozen 50% check, which is not validation.',
          '', 'The original docs230 independent-test and second-model-alpha-scan clause remains unchanged. The methods-only abstract remains unchanged.']
    (ROOT/'docs/255_FOUR_CONDITION_READ.md').write_text('\n'.join(doc)+'\n')
    write(EVAL/'four_condition_export_hashes.json',{str(p.relative_to(ROOT)):digest(p) for p in [baseline,analysis,target,ROOT/'paper/tables/wjb_official_mapping.tex',ROOT/'docs/255_FOUR_CONDITION_READ.md']})
    print('EXPORTED',digest(target))


if __name__=='__main__':main()
