"""Publishable numeric juxtaposition and coded targeted XSTest review."""
from pathlib import Path
import csv,datetime,hashlib,json
ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'lease_priority_followup_20261109'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    table=load(OUT/'benefit_cost_posthoc.json');review=load(OUT/'unsafe_downflip_model_labels.json');selection=load(OUT/'unsafe_downflip_selection.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    csvpath=ROOT/'paper/data/benefit_cost_posthoc.csv'
    with csvpath.open('w',newline='')as f:
        fields=list(table['rows'][0]);w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(table['rows'])
    lines=['# 事后：拒答收益与代价的并列表','',f'生成UTC {now}；仅从已读取文件生成。PAIR500新提示的效果未读。','', '| 提示集 | n | alpha0% | 学出均值% | 随机均值% | 学出减alpha0 pp |','|---|---:|---:|---:|---:|---:|']
    for r in table['rows']:lines.append(f'| {r["prompt_set"]} | {r["n"]} | {r["alpha0_refusal_pct"]:.4f} | {r["learned_mean_refusal_pct"]:.4f} | {r["random_mean_refusal_pct"]:.4f} | {r["learned_minus_alpha0_pp"]:+.4f} |')
    gaps=table['unpaired_harmful_minus_benign_refusal_gap_pp'];lines+=['',f'WJB有害减良性拒答率差：alpha0={gaps["alpha0_refusal_pct"]:.4f}pp，随机={gaps["random_mean_refusal_pct"]:.4f}pp，学出={gaps["learned_mean_refusal_pct"]:.4f}pp。两个集合规模与构造不同、不配对，指标不称选择性，不估计检测器精度/机制。差由未舍入值计算，因此OR为5.8832pp。','',
        '有害侧为单条2400token路径；公开侧为批量8、120token路径。OR-Bench-Hard没有施加这里的WJB改写，但不是内容匹配的无包装对照。跨集合模式与包装相关响应相容，不构成检验；与docs246/docs250配对实验并列，不推出机制。','',
        '## XSTest unsafe针对性全文读数','',f'选择冻结UTC {selection["utc"]}，共49个条件×提示配对，涉及19个不同提示；是全取v2基线阳性→学出阴性，不是均匀随机召回抽样。展示打乱种子20261201，字段只显示复核编号、原始完整提示与已存120token输出；逐条条件/规则/WG标签遮蔽，但共享上下文仍在，非独立人工校准。','',
        '| seed | 下翻 | 上翻 | 净少拒答条数 |','|---|---:|---:|---:|']
    for name,x in selection['counts'].items():lines.append(f'| {name} | {x["down"]} | {x["up"]} | {x["net"]} |')
    lines+=['','全文模型分类：R0、RA23、W5、C20、U1。其中RA的21条是“反驳有害前提+反向论述”的边界项，另2条是安全替代。将前提反驳不计入拒答时，对应R0、RA2、W5、C41、U1。两种读法均报，不把23当成已经人工验证的漏判。其余输出包含良性重解释、历史/合法框架说明和知识性非回答，不能将v2阴性等同有害合规。','',
        '19条对应基线均已全文读取：18条有明确拒答措辞，xst_449属于知识/能力性非回答，冻结基线规则标签不动。所有读数仍受120token截断限制。正文只写“规则拒答能力未见提高”，不推出有害合规增加。','',
        '| 复核编号 | seed | 原ID | 类别 | 原因编码 | 前提反驳边界 |','|---:|---|---|---|---|---|']
    for r in review['labels']:lines.append(f'| {r["review_index"]} | {r["condition"]} | {r["original_id"]} | {r["category"]} | {r["reason_code"]} | {r["boundary_premise_rebuttal"]} |')
    lines+=['',f'并列表JSON SHA256：{sha(OUT/"benefit_cost_posthoc.json")}。',f'模型编码表SHA256：{sha(OUT/"unsafe_downflip_model_labels.json")}。',f'原始全文材料不推送；仅编码映射和哈希入仓库。']
    doc=ROOT/'docs/255_BENEFIT_COST_POSTHOC_AND_XSTEST_UNSAFE.md';doc.write_text('\n'.join(lines)+'\n')
    tex=[r'\begin{table*}[t]',r'\centering\small',r'\begin{tabular}{lrrrrr}',r'\toprule',r'Prompt set & $n$ & Zero (\%) & Learned mean (\%) & Random mean (\%) & Learned--zero (pp) \\',r'\midrule']
    names=['WildJailbreak harmful, wrapped','WildJailbreak benign, wrapped','OR-Bench-Hard','XSTest safe','XSTest unsafe']
    for name,r in zip(names,table['rows']):tex.append(f'{name} & {r["n"]} & {r["alpha0_refusal_pct"]:.2f} & {r["learned_mean_refusal_pct"]:.2f} & {r["random_mean_refusal_pct"]:.2f} & {r["learned_minus_alpha0_pp"]:+.2f} '+r'\\')
    tex += [r'\bottomrule',r'\end{tabular}',r'\caption{Post-hoc juxtaposition of v2 operational refusal rates. Five learned vectors and four norm-matched random directions are averaged separately. Harmful responses use a single-row2400-token path; public responses use the matched batch8,120-token path. Datasets differ in content, construction and size; this is not a paired selectivity estimate. Source CSV and JSON hashes are preserved.}',r'\label{tab:benefit-cost-posthoc}',r'\end{table*}'];(ROOT/'paper/tables/benefit_cost_posthoc.tex').write_text('\n'.join(tex)+'\n')
    body='\\paragraph{A post-hoc benefit--cost juxtaposition.}\n\\input{tables/benefit_cost_posthoc}\n'
    body+=f'The unpaired harmful-minus-benign refusal-rate gap within the WildJailbreak evaluation data is {gaps["alpha0_refusal_pct"]:.2f} pp at zero, {gaps["random_mean_refusal_pct"]:.2f} pp for random directions, and {gaps["learned_mean_refusal_pct"]:.2f} pp for learned vectors. These differently constructed and sized sets are not paired, so the gap is descriptive and is not a selectivity or mechanism estimate. The cross-dataset pattern is compatible with packaging-related response differences but does not test that explanation. The matched vanilla--wrapped experiments in Table~\\ref{{tab:c2}} provide a separate paired comparison.\n\n'
    body+='On XSTest unsafe, rule-defined refusal capability does not improve. A targeted model reread of49 baseline-positive to learned-negative pairs over19 prompts finds two safety redirections,21 premise-rebuttal boundary cases,20 other content responses, five cautioned responses and one knowledge nonanswer. Counting premise rebuttals as refusal-with-alternative yields23; excluding them yields two. This shared-context,120-token review is not human calibration and does not establish an increase in harmful compliance.\n'
    p=ROOT/'paper/generated/benefit_cost_posthoc.tex';p.write_text(body);results=ROOT/'paper/sections/04_results.tex';text=results.read_text();entry='\\input{generated/benefit_cost_posthoc}'
    if entry not in text:results.write_text(text+'\n'+entry+'\n')
    manifest={'utc':now,'files':{str(p.relative_to(ROOT)):sha(p)for p in [doc,csvpath,ROOT/'paper/tables/benefit_cost_posthoc.tex',ROOT/'paper/generated/benefit_cost_posthoc.tex',OUT/'benefit_cost_posthoc.json',OUT/'unsafe_downflip_selection.json',OUT/'unsafe_downflip_mapping.json',OUT/'unsafe_downflip_model_labels.json']},'post_hoc':True,'PAIR_effects_read':False,'model_annotation_not_human_calibration':True};p=OUT/'report_manifest.json';p.write_text(json.dumps(manifest,indent=2)+'\n')
    with(ROOT/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{now} POSTHOC_BENEFIT_COST_AND_UNSAFE_REPORT SHA={sha(doc)} sourceJSONSHA={sha(OUT/"benefit_cost_posthoc.json")} narrow/broad premise coding both retained, no rule update; PAIR outcomes unread.\n')
    print(json.dumps({'utc':now,'report_sha256':sha(doc),'source_json_sha256':sha(OUT/'benefit_cost_posthoc.json'),'manifest_sha256':sha(p)}))
if __name__=='__main__':main()
