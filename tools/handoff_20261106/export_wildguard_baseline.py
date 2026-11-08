"""Generate baseline tables and provenance directly from saved read stages."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path('/data/HZX/Def');OUT=ROOT/'results/audit/pair500/wildguard';READ=OUT/'baseline_read'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    stages={name:json.loads((READ/(name+'.json')).read_text()) for name in ['status','primary','labels_and_strata','refusal_agreement']}
    primary=stages['primary']['value'];labels=stages['labels_and_strata']['value'];agree=stages['refusal_agreement']['value']
    table=ROOT/'paper/data/wildguard_alpha0.csv'
    with table.open('w',newline='') as f:
        fields=['layer','field','n','yes','invalid','rate_all_rows','bound_low','bound_high','source','sha256'];w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
        for layer,values in labels.items():
            if layer=='invalid_any':continue
            for field,row in values.items():
                w.writerow({'layer':layer,'field':field,**{k:row[k] for k in ['n','yes','invalid','rate_all_rows']},'bound_low':row['bounds'][0],'bound_high':row['bounds'][1],'source':str((READ/'labels_and_strata.json').relative_to(ROOT)),'sha256':sha(READ/'labels_and_strata.json')})
    with table.open() as f:rows=list(csv.DictReader(f))
    lines=['\\begin{table}[t]','\\centering\\small','\\begin{tabular}{lrrr}','\\toprule','Layer & $n$ & Harmful & Rate bounds (\\%) \\\\','\\midrule']
    for row in rows:
        if row['field']!='Harmful response' or row['layer'] not in ['all','high','low']:continue
        name={'all':'All','high':'High mapping confidence','low':'Low mapping confidence'}[row['layer']]
        lo,hi=100*float(row['bound_low']),100*float(row['bound_high'])
        lines.append(f'{name} & {row["n"]} & {row["yes"]} & [{lo:.2f}, {hi:.2f}] \\\\')
    lines+=['\\bottomrule','\\end{tabular}','\\caption{Official WildJailbreak evaluation baseline under primary \\texttt{wildguard\\_node01}, using full prompt and response. Bounds retain invalid response-harmfulness labels in the denominator. Confidence refers to the supplementary behavior mapping, not WildGuard confidence. Source SHA256: \\texttt{'+sha(READ/'labels_and_strata.json')[:12]+'}; full hashes are in the companion CSV.}','\\label{tab:wildguard-alpha0}','\\end{table}']
    (ROOT/'paper/tables/wildguard_alpha0.tex').write_text('\n'.join(lines)+'\n')
    report=['# Ordered WildGuard alpha0 read','',f'Primary source SHA256: `{sha(READ/"primary.json")}`.',
        '',f'Primary response harmful: {primary["yes"]}/{primary["n"]}; invalid{primary["invalid"]}; bounds {primary["bounds"]}; descriptive25% gate {primary["gate25"]}.',
        '', 'Read timestamps: '+json.dumps({k:v['first_read_utc'] for k,v in stages.items()}),
        '', 'Status/length metadata: '+json.dumps(stages['status']['value']),
        '', '| Layer | v2 no/model no | v2 no/model yes | v2 yes/model no | v2 yes/model yes | kappa |', '|---|---:|---:|---:|---:|---:|']
    for name,row in agree.items():
        m=row['matrix'];report.append(f'| {name} | {m["v20_model0"]} | {m["v20_model1"]} | {m["v21_model0"]} | {m["v21_model1"]} | {row["kappa"]} |')
    report+=['', 'The only >4096-token input is ID701 (4817 tokens), also the only response-harmfulness INVALID. Its output lacks the expected Harmful response field and instead emits refusal subcategories. Request/refusal labels remain parseable; their agreement denominator is2000. No silent truncation, relabeling or rerun occurred. This single co-occurrence does not identify a mechanism.',
        '', 'WildGuard is primary; mapped HarmBench top1=993/2000, top2=304/2000 and random-reference2/200 are supplementary reference-dependent diagnostics. Their input protocols also differ (mapped judge response clip versus full WildGuard interaction); the difference in absolute rates is not a calibration result.',
        '', 'All results are model labels without human calibration, with WildGuard/WildJailbreak source affinity. Only alpha0 has been conversationally read. Conditions follow frozen order on node01GPU0; nine-unit effects remain unread until all primary units complete. No abstract effectiveness claim is added.']
    (ROOT/'docs/255_WILDGUARD_ALPHA0_ORDERED_READ.md').write_text('\n'.join(report)+'\n')
    record={str(p.relative_to(ROOT)):sha(p) for p in [table,ROOT/'paper/tables/wildguard_alpha0.tex',ROOT/'docs/255_WILDGUARD_ALPHA0_ORDERED_READ.md']+[READ/(name+'.json') for name in stages]}
    (OUT/'baseline_export_hashes.json').write_text(json.dumps(record,indent=2)+'\n');print('EXPORTED',record)


if __name__=='__main__':main()
