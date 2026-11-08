"""Render completed ordered-read artifacts; no raw prompts or completions."""
from pathlib import Path
import csv
import datetime
import hashlib
import json
import sys

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';READ=BASE/'nine_read_20261109'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def main():
    stages=sorted(READ.glob('0[1-9]_*.json'));assert len(stages)==9
    entries=[load(p) for p in stages]
    for i,e in enumerate(entries,1):
        assert e['step']==i and datetime.datetime.fromisoformat(e['started_utc'])>=datetime.datetime(2026,11,8,23,tzinfo=datetime.timezone.utc)
        for previous in e['previous_steps']:assert sha(ROOT/previous['file'])==previous['sha256']
        if i>1:assert e['started_utc']>entries[i-2]['saved_utc']
    main=entries[2]['result'];strata=entries[3]['result'];permutation=entries[4]['result'];attribution=entries[5]['result'];agreement=entries[6]['result'];invalid=entries[7]['result'];prediction=entries[8]['result'];status=entries[0]['result']
    sys.path.insert(0,str(ROOT/'tools/handoff_20261106'));from operational_metadata import capture
    progress=capture();nodes={}
    for name in main['HB_top1']['conditions']:
        pass
    for name in progress['prefix_generation_coverage']:
        values={load(p)['generation_node'] for p in (BASE/'prefix254/generation.private'/name).glob('*.json')};nodes[name]=sorted(values)
    progress['prefix_generation_nodes']=nodes
    progress['alpha0_first50_diagnostic']=load(BASE/'prefix254/alpha0_first50_cross_node.json')
    progress['alpha0_first50_diagnostic_sha256']=sha(BASE/'prefix254/alpha0_first50_cross_node.json')
    progress['search_caps']={k:load(BASE/'config.json')[k] for k in ['search_target_max_new_tokens','eval_target_max_new_tokens']}
    save(READ/'current_progress.json',progress)
    ledger=[{'step':e['step'],'stage':e['stage'],'started_utc':e['started_utc'],'saved_utc':e['saved_utc'],'file':str(p.relative_to(ROOT)),'sha256':sha(p)} for e,p in zip(entries,stages)]
    save(READ/'step_ledger.json',ledger)
    lines=['# WildJailbreak九单元：按冻结顺序读取的结果','',f'导出 UTC：{datetime.datetime.now(datetime.timezone.utc).isoformat()}。没有因结果修改排期、停止规则或摘要。',
        '', 'WildGuard为主判官；HarmBench top-1映射判定为补充。全部2000行保留。WildGuard完整九条件配对为1997行；其余3行不计为观察到的无害，而给出全2000行的识别边界。普通区间条件于实际观察到的向量单元；不代表向量总体不确定性。',
        '', '## 两判官主差与分层','', '| 判官 | 全部保留n / 完整配对n | 学出减随机 pp | 行自助95% | 200行为聚类95% | 全行识别边界 pp |', '|---|---|---:|---|---|---|']
    records=[]
    for judge,r in main.items():
        lines.append(f'| {judge} | {r["retained_rows"]} / {r["complete_pair_rows"]} | {r["conditional_complete_pair_mean_pp"]:.4f} | {r["row_bootstrap95_pp"]} | {r["behavior_cluster_bootstrap95_pp"]} | {r["all_rows_identification_bounds_pp"]} |')
        for layer in ['all','high','low']:
            s=strata[judge][layer]
            records.append({'judge':judge,'stratum':layer,'n_retained':s['retained_rows'],'n_complete':s['complete_pair_rows'],'difference_pp':s['conditional_complete_pair_mean_pp'],'row_low':s['row_bootstrap95_pp'][0],'row_high':s['row_bootstrap95_pp'][1],'behavior_low':s['behavior_cluster_bootstrap95_pp'][0],'behavior_high':s['behavior_cluster_bootstrap95_pp'][1],'bound_low':s['all_rows_identification_bounds_pp'][0],'bound_high':s['all_rows_identification_bounds_pp'][1],'source':str(stages[3].relative_to(ROOT)),'source_sha256':sha(stages[3])})
    lines+=['','| 判官 | 高置信1689行，差/聚类95% | 低置信311行，差/聚类95% |','|---|---|---|']
    for j in main:
        a,b=(strata[j][k] for k in ['high','low']);lines.append(f'| {j} | {a["conditional_complete_pair_mean_pp"]:.4f}; {a["behavior_cluster_bootstrap95_pp"]} | {b["conditional_complete_pair_mean_pp"]:.4f}; {b["behavior_cluster_bootstrap95_pp"]} |')
    lines+=['',f'两判官与两层同为负：{strata["all_negative"]}。全九条件top-2稳健性仍待完成；不得写成已通过。摘要继续遵守PAIR/稳健性待读规则。',
        '', '| 判官 | 等行为权差pp / 95% | 126分配下尾p | 双侧绝对统计量p | 行口径留一范围pp |','|---|---|---|---|---|']
    for j,r in main.items():
        p=permutation[j]['row'];loo=list(p['leave_one_out_pp'].values());lines.append(f'| {j} | {r["conditional_equal_behavior_mean_pp"]:.4f}; {r["equal_behavior_bootstrap95_pp"]} | {p["p_lower"]:.8f} | {p["p_two_sided_absolute"]:.8f} | [{min(loo):.4f}, {max(loo):.4f}] |')
    lines+=['','置换遵循addendum13冻结的均值差绝对值定义，并非旧WJB-300的Mann–Whitney U检验；五对四组大小不同，绝对统计量双侧概率不必等于下尾概率乘二。可交换性是假设，检验是探索性的。所有20项seed-direction差和所有留一结果保存在第5步JSON。',
        '', '## 下翻拒答归因（相关事件计数，非机制）','', '| 下翻判官 | 单元类别 | 下翻数 | WG拒答 | v2拒答 | v2∪v3拒答 |','|---|---|---:|---:|---:|---:|']
    for j in ['HB_top1','WildGuard']:
        for group,x in attribution[j]['pooled_correlated_events'].items():lines.append(f'| {j} | {group} | {x["downflip_n"]} | {x["WG_refusal_yes"]} | {x["v2_refusal"]} | {x["union_refusal"]} |')
    lines+=['','同一提示可在多个单元重复，以上事件不独立；完整逐单元归因在第6步。','',
        '## v2与WildGuard拒答一致性','', '| 条件 | 双阴 | v2阴/WG阳 | v2阳/WG阴 | 双阳 | WG拒答INVALID | κ | 模型参照召回 |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,d in agreement['conditions'].items():
        x=d['all'];c=x['cells'];lines.append(f'| {name} | {c["v20_WG0"]} | {c["v20_WG1"]} | {c["v21_WG0"]} | {c["v21_WG1"]} | {x["invalid_pairs"]} | {x["kappa"]:.6f} | {x["model_referenced_v2_recall"]:.6f} |')
    lines+=['','这是模型与规则的一致性，不是人工校准；v2主规则不变。完整高/低置信层在第7步。','',
        '## INVALID逐字段ID','', '| 条件 | 提示有害INVALID | 回复有害INVALID | 回复拒答INVALID | 输入>4096 |','|---|---|---|---|---|']
    for name,x in invalid.items():
        f=x['WG_field_ids'];lines.append(f'| {name} | {f["Harmful request"]} | {f["Harmful response"]} | {f["Response refusal"]} | {x["input_gt4096_ids"]} |')
    lines+=['','HB全部单元INVALID=0。WG以上原因均为invalid_format。>4096是滑窗标记，硬上限32768；未静默截断，不能据此断言解析失败的原因。','',
        f'读前预测{prediction["frozen_prediction_pp"]:.2f}pp，观察到的完整配对差{prediction["observed_WG_complete_pair_contrast_pp"]:.4f}pp，差{prediction["observed_minus_prediction_pp"]:.4f}pp：同号、量级接近，只作描述；四单元预测锚与九单元目标不同，没有通过线。',
        '', '## 逐步读取记录（UTC与完整SHA256）','', '| 步 | 阶段 | 开始UTC | 落盘UTC | SHA256 |','|---|---|---|---|---|']
    for x in ledger:lines.append(f'| {x["step"]} | {x["stage"]} | {x["started_utc"]} | {x["saved_utc"]} | {x["sha256"]} |')
    lines+=['','## 九单元文件清单摘要','',f'逐文件SHA256完整清单：results/audit/pair500/nine_read_20261109/score_file_manifest.json，SHA256={sha(READ/"score_file_manifest.json")}。下表目录摘要是排序文件名到SHA映射的规范JSON摘要。',
        '', '| 条件 | HB文件/INVALID | WG文件/提示、回复、拒答INVALID | HB目录摘要 | WG目录摘要 |','|---|---|---|---|---|']
    for name,x in status['units'].items():
        h,w=x['HB_top1'],x['WildGuard'];f=w['invalid_counts'];lines.append(f'| {name} | 2000/{h["invalid_counts"]["label"]} | 2000/{f["Harmful request"]},{f["Harmful response"]},{f["Response refusal"]} | {h["directory_fingerprint_sha256"]} | {w["directory_fingerprint_sha256"]} |')
    lines+=['','## 当前提前生成进度','',f'运行快照UTC：{progress["utc"]}；PAIR搜索{progress["pair"]["completed_rows"]}/500。','', '| 条件 | 已保存行数 | 节点 |','|---|---:|---|']
    for name,n in progress['prefix_generation_coverage'].items():lines.append(f'| {name} | {n} | {nodes[name]} |')
    diag=progress['alpha0_first50_diagnostic'];lines+=['',f'正式500行条件均未完成，搜索结束后补齐。前50行alpha0字节诊断：{diag["identical"]}/{diag["n"]}一致，UTC {diag["utc"]}，SHA256={progress["alpha0_first50_diagnostic_sha256"]}。比较的是独立2400-token生成路径，不是512-token搜索候选回复；它不替代迁移条件的20条同函数节点门。','',
        '公开侧71分钟间隔的来源及让位UTC边界见 docs/255_NINE_UNIT_ORDERED_READ_EXECUTION.md。当前队列安排不变，WJB s0/system A/B仍排在PAIR之后。']
    doc=ROOT/'docs/255_NINE_UNIT_ORDERED_READ_RESULTS.md';doc.write_text('\n'.join(lines)+'\n')
    csvpath=ROOT/'paper/data/wjb_official_nine.csv'
    with csvpath.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');writer.writeheader();writer.writerows(records)
    tex=['\\begin{table}[t]','\\centering\\small','\\begin{tabular}{lrr}','\\toprule','Judge & Difference (pp) & Behavior-cluster 95\\% CI \\\\','\\midrule']
    for j,r in main.items():
        lo,hi=r['behavior_cluster_bootstrap95_pp'];label='Mapped HarmBench' if j=='HB_top1' else 'WildGuard'
        tex.append(f'{label} & {r["conditional_complete_pair_mean_pp"]:.2f} & [{lo:.2f}, {hi:.2f}] \\\\')
    tex+=['\\bottomrule','\\end{tabular}',r'\caption{Learned-five minus random-four paired harmfulness differences on the WildJailbreak evaluation set (2000 adversarial harmful prompts). HarmBench uses assigned top-1 behavior references. WildGuard has 1997 complete nine-unit pairs; all rows remain in the reported identification bounds. Intervals condition on the observed units; mapped-reference top-2 robustness remains pending. Source SHA256: \texttt{'+sha(stages[2])[:12]+'}.}',r'\label{tab:wjb-official-nine}','\\end{table}']
    (ROOT/'paper/tables/wjb_official_nine.tex').write_text('\n'.join(tex)+'\n')
    source_manifest={str(p.relative_to(ROOT)):sha(p) for p in stages+[READ/'step_ledger.json',READ/'current_progress.json',READ/'score_file_manifest.json',doc,csvpath,ROOT/'paper/tables/wjb_official_nine.tex']}
    save(READ/'export_manifest.json',source_manifest)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{now} NINE_UNIT_ORDERED_READ_ALL9_EXPORTED docSHA={sha(doc)} exportManifestSHA={sha(READ/"export_manifest.json")}; primary cross-judge/strata signs agree, top2 remains pending; methods-only abstract retained and no schedule/stopping changes.\n')
    print(json.dumps({'report_sha256':sha(doc),'score_manifest_sha256':sha(READ/'score_file_manifest.json'),'ledger':ledger,'progress_utc':progress['utc'],'pair_rows':progress['pair']['completed_rows'],'prefix_counts':progress['prefix_generation_coverage'],'prefix_nodes':nodes,'diagnostic_identical':diag['identical'],'diagnostic_n':diag['n'],'diagnostic_sha256':progress['alpha0_first50_diagnostic_sha256']},ensure_ascii=False))


if __name__=='__main__':main()
