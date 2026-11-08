"""Place previously read alpha0 descriptions in the dataset table, not abstract."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    hp=BASE/'public255/alpha0_reference_directional.json';wp=BASE/'wildguard/baseline_read/primary.json'
    hb=json.loads(hp.read_text())['all'];wg=json.loads(wp.read_text())['value'];assert hb['n']==wg['n']==2000
    records=[]
    for judge,count,invalid,source in [('HarmBench mapped top-1',hb['top1_yes'],hb['invalid'],hp),('WildGuard',wg['yes'],wg['invalid'],wp),('HarmBench mapped top-2',hb['top2_yes'],hb['invalid'],hp)]:
        records.append({'dataset':'WildJailbreak evaluation adversarial harmful','n':2000,'judge':judge,'harmful_yes':count,'invalid':invalid,'yes_over_all_rows_pct':100*count/2000,'upper_pct':100*(count+invalid)/2000,'source':str(source.relative_to(ROOT)),'sha256':sha(source)})
    path=ROOT/'paper/data/wjb_official_alpha0_dataset.csv'
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
    lines=['\\begin{table}[t]','\\centering\\small','\\begin{tabular}{lrrr}','\\toprule','Judge/reference & Yes/$n$ & Yes/$n$ (\\%) & Invalid \\\\','\\midrule']
    for r in records:lines.append(f'{r["judge"]} & {r["harmful_yes"]}/2000 & {r["yes_over_all_rows_pct"]:.2f} & {r["invalid"]} \\\\')
    bound=f'{records[1]["yes_over_all_rows_pct"]:.2f}--{records[1]["upper_pct"]:.2f}'
    lines += ['\\bottomrule','\\end{tabular}',r'\caption{Previously read alpha-zero model labels on the WildJailbreak evaluation set (2000 adversarial harmful prompts). Mapped-reference values are descriptive and depend on the reference behavior. The WildGuard missing-label bound is '+bound+r'\%; INVALID is not an observed harmless label. These absolute baseline descriptions are excluded from the abstract. Sources and complete SHA256 values accompany the CSV.}',r'\label{tab:wjb-alpha0-dataset}','\\end{table}']
    (ROOT/'paper/tables/wjb_official_alpha0_dataset.tex').write_text('\n'.join(lines)+'\n')
    setup=ROOT/'paper/sections/03_setup.tex';s=setup.read_text();entry='\\input{tables/wjb_official_alpha0_dataset}'
    if entry not in s:setup.write_text(s+'\n'+entry+'\n')
    results=ROOT/'paper/sections/04_results.tex';s=results.read_text();entry='\\input{tables/wjb_official_nine}'
    if entry not in s:results.write_text(s+'\n'+entry+'\n')
    print('DATASET_BASELINE_AND_NINE_UNIT_TABLES_INCLUDED; abstract unchanged')


if __name__=='__main__':main()
