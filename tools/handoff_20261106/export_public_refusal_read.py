"""Generate public-result tables, traceable report, and bounded manuscript prose."""
import collections
import csv
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'public_read_20261109'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def main():
    phasefiles=[OUT/n for n in ['01_status.json','02_baseline.json','03_main.json','04_unsafe.json','05_unseen.json','06_sensitivity.json','07_samples.json']]
    primary=load(phasefiles[2])['result'];unsafe=load(phasefiles[3])['result'];unseen=load(phasefiles[4])['result'];sensitivity=load(phasefiles[5])['result'];groups=[load(OUT/f'08_recall_group{i}.json') for i in range(1,7)]
    assert (OUT/'09_scatter.json').exists()
    layers={'all':primary,'keep60_unseen':unseen};datasets=['xstest_safe','or_hard','wildjailbreak_benign'];pretty={'xstest_safe':'XSTest safe','or_hard':'OR-Bench-Hard','wildjailbreak_benign':'WildJailbreak benign'}
    ledger=[]
    for p in phasefiles:
        x=load(p);ledger.append({'stage':x['stage'],'utc':x['saved_utc'],'file':str(p.relative_to(ROOT)),'sha256':sha(p)})
    for i,g in enumerate(groups,1):
        p=OUT/f'08_recall_group{i}.json';ledger.append({'stage':g['group'],'utc':g['utc'],'file':str(p.relative_to(ROOT)),'sha256':sha(p)})
    for name in ['09_scatter.json','09_scatter_labels_v2.json']:
        p=OUT/name;x=load(p);ledger.append({'stage':name,'utc':x['utc'],'file':str(p.relative_to(ROOT)),'sha256':sha(p)})
    save(OUT/'step_ledger.json',ledger)
    coded=[r for g in groups for r in g['coded_rows']];assert len(coded)==180 and len({r['review_index'] for r in coded})==180
    save(OUT/'recall_coded_rows.json',sorted(coded,key=lambda x:x['review_index']))
    rows=[]
    for layer,data in layers.items():
        for dataset,x in data.items():
            rows.append({'layer':layer,'dataset':dataset,'rule':'v2','n':x['retained_n'],'difference_pp':x['learned_minus_random_pp'],'ci_low':x['paired_prompt_bootstrap95_pp'][0],'ci_high':x['paired_prompt_bootstrap95_pp'][1],
                'WG_sensitivity_pp':sensitivity[dataset][layer]['rules']['WG']['learned_minus_random_pp'],'source':str((phasefiles[2] if layer=='all' else phasefiles[4]).relative_to(ROOT)),'sha256':sha(phasefiles[2] if layer=='all' else phasefiles[4])})
    p=ROOT/'paper/data/public_refusal_nine.csv'
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    tex=['\\begin{table*}[t]','\\centering\\small','\\begin{tabular}{lrrrrr}','\\toprule','Benign-labelled set & Full $n$ & V2 difference (pp) & Prompt bootstrap 95\\% & Unseen difference (pp) & WG sensitivity (pp) \\\\','\\midrule']
    for d,x in primary.items():
        lo,hi=x['paired_prompt_bootstrap95_pp'];tex.append(f'{pretty[d]} & {x["retained_n"]} & {x["learned_minus_random_pp"]:+.2f} & [{lo:.2f}, {hi:.2f}] & {unseen[d]["learned_minus_random_pp"]:+.2f} & {sensitivity[d]["all"]["rules"]["WG"]["learned_minus_random_pp"]:+.2f} \\\\')
    tex+=['\\bottomrule','\\end{tabular}',r'\caption{Five learned vectors minus four norm-matched random directions: operational refusal differences on benign-labelled public sets. V2 is primary; WildGuard is sensitivity, not human calibration. Unseen layers retain238,1301,210 rows respectively. All responses are capped at120 target tokens; intervals condition on the observed vectors. WildGuard has204 complete nine-unit pairs on the210-row benign WildJailbreak set; its all-row difference bounds are8.83--9.43pp. Source CSV contains complete file hashes.}',r'\label{tab:public-refusal-nine}','\\end{table*}']
    (ROOT/'paper/tables/public_refusal_nine.tex').write_text('\n'.join(tex)+'\n')
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    lines=['# 公开过拒侧按冻结顺序读取','',f'导出UTC：{now}。v2为主；其余规则与WG为敏感性。保留全体与keep60未见层；这些是规则/模型操作计数，未经人工校准。','',
        '| 集合 | 全体n | v2学出减随机pp | 95%提示配对自助 | 未见n | 未见差pp / 95% | WG敏感性pp / 95% |','|---|---:|---:|---|---:|---|---|']
    for d,x in primary.items():
        u=unseen[d];wg=sensitivity[d]['all']['rules']['WG'];lines.append(f'| {pretty[d]} | {x["retained_n"]} | {x["learned_minus_random_pp"]:+.4f} | {x["paired_prompt_bootstrap95_pp"]} | {u["retained_n"]} | {u["learned_minus_random_pp"]:+.4f}; {u["paired_prompt_bootstrap95_pp"]} | {wg["learned_minus_random_pp"]:+.4f}; {wg["paired_prompt_bootstrap95_pp"]} |')
    lines+=['',f'XSTest unsafe对照200行：拒答率差{unsafe["learned_minus_random_pp"]:+.4f}pp，区间{unsafe["paired_prompt_bootstrap95_pp"]}。这是拒答能力操作计数，不等于有害合规率。','',
        '| 条件 | XSTest safe拒答/250 | OR-Hard拒答/1319 | WJB良性拒答/210 | unsafe拒答/200 |','|---|---:|---:|---:|---:|']
    for name in primary['xstest_safe']['conditions']:
        counts=[primary[d]['conditions'][name]['refused'] for d in datasets]+[unsafe['conditions'][name]['refused']];lines.append('| '+name+' | '+' | '.join(map(str,counts))+' |')
    lines+=['','## 六组字段遮蔽模型复核','',
        '抽样与180条打乱展示名单先于文本读取冻结并push（c42b79ba8f47）。显示复核编号、原始任务和完整已存回复（上限120tokens），不显示逐条条件/类/规则/WG标签。共享上下文仍在，不是独立盲读或人工校准。内容准确性与完整任务成功不在此标注验证范围。','',
        '| 集合/类 | seed | R | RA | W | C | U | 明确漏判/30 | 保守计数/30 | 独立提示数 | 保守线<=3 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for g in groups:
        c=g['categories'];lines.append(f'| {g["group"]} | {g["seed"]} | {c["R"]} | {c["RA"]} | {c["W"]} | {c["C"]} | {c["U"]} | {g["clear_model_read_misses"]} | {g["conservative_misses"]} | {g["unique_prompt_count"]} | {g["conservative_pass"]} |')
    lines+=['','WJB良性随机组5条U，使保守线失败；不补换样本、不声称全部召回验证通过。R/RA为0也不是零漏判保证。重复提示被单列，样本不是30个独立提示。U包含输出截断、只澄清未作答或原始任务不完整，逐条原因编码见recall_coded_rows.json。','',
        'WG看到的也是120-token截断回复；其与v2的2x2/κ在第6步按条件、集合、未见层保存。差异不能直接当成v2漏判。v2并v3与V_b敏感性不替换主规则。','',
        '## 读取落盘记录','', '| 阶段 | UTC | SHA256 |','|---|---|---|']
    for x in ledger:lines.append(f'| {x["stage"]} | {x["utc"]} | {x["sha256"]} |')
    lines+=['','九点散点：paper/figures/wjb_harm_public_refusal_all_labels_v2.png及PDF；未见层另图。上排HB映射，下排WG；横轴WJB有害侧相对alpha0变化，纵轴各良性集合v2拒答变化。未拟合曲线、无决策阈值，全部九个向量均报告。标签排版v2没有改变点值CSV，原图与阶段记录均保留。',
        '',f'逐文件WG分数哈希清单SHA256={sha(OUT/"source_file_manifest.json")}。',f'规则标签表SHA256={sha(OUT/"rule_labels.json")}。']
    doc=ROOT/'docs/255_PUBLIC_ORDERED_READ_RESULTS.md';doc.write_text('\n'.join(lines)+'\n')
    # Generate manuscript paragraphs from the saved artifacts, not copied cells.
    generated=ROOT/'paper/generated';generated.mkdir(exist_ok=True)
    text='\\subsection{Public benign refusal costs}\n\\input{tables/public_refusal_nine}\n'
    text+=('The harmful-side advantage does not imply uniform benign costs. The frozen v2 comparison gives '+f'{primary["xstest_safe"]["learned_minus_random_pp"]:+.2f}, {primary["or_hard"]["learned_minus_random_pp"]:+.2f}, and {primary["wildjailbreak_benign"]["learned_minus_random_pp"]:+.2f} pp on XSTest safe, OR-Bench-Hard, and official WildJailbreak benign prompts, respectively. '+
        'Full and keep60-unseen layers are shown together; the training overlap is retained, not removed from the main result. WildGuard refusal sensitivity has the same signs, but it sees the same120-token truncated outputs and is not human ground truth.\n\n')
    text+=('In six fixed30-pair model reviews, no response was read as a clear task refusal or refusal with alternative. The benign WildJailbreak random group has five uncertain responses and fails the conservative rule that treats uncertainty as a miss. Thus these samples do not validate absolute refusal accuracy. The samples repeat some prompts across vector conditions, use shared conversation context, and lack independent human calibration.\n\n')
    text+=f'On the separately reported200-row unsafe XSTest control, the v2 refusal difference is{unsafe["learned_minus_random_pp"]:+.2f} pp; this refusal-capability reading is not an attack-success estimate.\n'
    (generated/'public_refusal_results.tex').write_text(text)
    results=ROOT/'paper/sections/04_results.tex';s=results.read_text();entry='\\input{generated/public_refusal_results}'
    if entry not in s:results.write_text(s+'\n'+entry+'\n')
    manuscript_manifest={str(p.relative_to(ROOT)):sha(p) for p in [doc,ROOT/'paper/data/public_refusal_nine.csv',ROOT/'paper/tables/public_refusal_nine.tex',generated/'public_refusal_results.tex']}
    save(OUT/'export_manifest.json',{'utc':now,'files':manuscript_manifest,'step_ledger_sha256':sha(OUT/'step_ledger.json'),'selection_manifest_sha256':sha(OUT/'recall_selection_manifest.json'),'primary_rule':'v2 unchanged','human_calibration':False})
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{now} PUBLIC_READ_COMPLETE_EXPORTED docSHA={sha(doc)} exportSHA={sha(OUT/"export_manifest.json")} all six groups retained; WJB-random conservative recall line failed5/30U, no rule/schedule change.\n')
    print(json.dumps({'utc':now,'report_sha256':sha(doc),'export_manifest_sha256':sha(OUT/'export_manifest.json'),'model_recall':[{k:g[k] for k in ['group','categories','conservative_pass','unique_prompt_count']} for g in groups]},ensure_ascii=False))


if __name__=='__main__':main()
