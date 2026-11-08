"""Export alpha0 pair counts and coded IDs, never raw task material."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path('/data/HZX/Def');OUT=ROOT/'results/audit/pair500/wildguard'


def main():
    source=OUT/'alpha0_crossjudge.json';x=json.loads(source.read_text());digest=hashlib.sha256(source.read_bytes()).hexdigest()
    p=ROOT/'paper/data/wildguard_harmbench_alpha0.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['layer','all_n','complete_pairs','HB0_WG0','HB0_WG1','HB1_WG0','HB1_WG1','kappa','source_sha256'],lineterminator='\n');w.writeheader()
        for name,row in x['agreement'].items():w.writerow({'layer':name,'all_n':row['n_all_rows'],'complete_pairs':row['complete_pairs'],**row['matrix'],'kappa':row['kappa'],'source_sha256':digest})
    p=OUT/'alpha0_refusal16_hb_labels.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','HB_top1_harmful','WG_response_harmful','mapping_layer'],lineterminator='\n');w.writeheader();w.writerows(x['v2_negative_wg_refusal_positive_rows'])
    table=['\\begin{table}[t]','\\centering\\small','\\begin{tabular}{lrrrrr}','\\toprule',
        'Layer & Neither & WG only & HB only & Both & $\\kappa$ \\\\','\\midrule']
    for name,row in x['agreement'].items():
        m=row['matrix'];table.append(f'{name} & {m["HB0_WG0"]} & {m["HB0_WG1"]} & {m["HB1_WG0"]} & {m["HB1_WG1"]} & {row["kappa"]:.3f} \\\\')
    table+=['\\bottomrule','\\end{tabular}','\\caption{Baseline response-harmfulness label agreement: primary WildGuard versus supplementary mapped HarmBench top-1. One WildGuard-invalid row is excluded from this agreement table and retained in primary-rate bounds. Full/high/low valid pair counts are1999/1688/311. Neither judge is human ground truth. Source SHA256: \\texttt{'+digest[:12]+'}; complete provenance accompanies the CSV.}', '\\label{tab:wg-hb-alpha0}','\\end{table}']
    (ROOT/'paper/tables/wildguard_harmbench_alpha0.tex').write_text('\n'.join(table)+'\n')
    report=['# Alpha0 cross-judge paired counts', '',f'Source SHA256: `{digest}`.',
        '', '| Layer | Complete pairs | Both no | WG only yes | HB only yes | Both yes | kappa |','|---|---:|---:|---:|---:|---:|---:|']
    for name,row in x['agreement'].items():
        m=row['matrix'];report.append(f'| {name} | {row["complete_pairs"]} | {m["HB0_WG0"]} | {m["HB0_WG1"]} | {m["HB1_WG0"]} | {m["HB1_WG1"]} | {row["kappa"]} |')
    report+=['', 'ID701 is HB-positive and WG-response-harmfulness-invalid; it is outside the agreement cells, inside the primary2000 denominator and its bounds.',
        '', 'The16 v2-negative/WG-refusal-positive rows have one HB-positive ID856. All16 are WG-response-harmfulness-negative. Coded IDs and HB labels are in alpha0_refusal16_hb_labels.csv; no raw text published.',
        '', 'WG prompt-harmless76 rows: '+json.dumps(x['wg_prompt_harmless_response_harmful']),
        '', 'Direct v2-negative intersection: '+json.dumps(x['v2_negative_response_harmful']),
        '', 'This is descriptive model agreement, not identification of either judge as correct. Different behavior references, response caps and model training limit attribution. No condition WG outcomes were inspected. The frozen nine-unit prediction is exploratory and anchored to a four-unit HB interim; it is not a causal scaling test.']
    (ROOT/'docs/255_WILDGUARD_ALPHA0_CROSSJUDGE.md').write_text('\n'.join(report)+'\n')
    paper=ROOT/'paper/sections/05_traps.tex';text=paper.read_text();marker='\\paragraph{Baseline model-judge disagreement.}'
    if marker not in text:
        row=x['agreement']['all'];m=row['matrix']
        text+='\n'+marker+'\n\\input{tables/wildguard_harmbench_alpha0}\n'+f'The baseline has {m["HB0_WG1"]} WildGuard-only and {m["HB1_WG0"]} mapped-HarmBench-only harmful labels among {row["complete_pairs"]} valid pairs. Agreement does not establish either model as ground truth, and differing references and response-length protocols prevent attributing the gap solely to mapping errors. Unit-level robustness remains unread until all nine units complete.\n'
        paper.write_text(text)
    print('EXPORTED sourceSHA',digest)


if __name__=='__main__':main()
