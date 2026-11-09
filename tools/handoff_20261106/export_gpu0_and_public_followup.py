"""Export project-aware operations and the requested post-hoc public tables."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
import sys
import numpy as np
from scipy.stats import t

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'public_followup_20261109'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def interval(v):
    a=np.asarray(v,float);mean=float(a.mean());half=float(t.ppf(.975,len(a)-1)*a.std(ddof=1)/np.sqrt(len(a)));return [mean-half,mean+half]
def perf(raw):
    result={}
    for i,section in enumerate(raw.split('GPU 00000000:')[1:],2):
        counters={}
        for key in ['SW Thermal Slowdown','HW Thermal Slowdown','SW Power Capping','HW Power Braking']:
            match=re.search(r'^\s*'+re.escape(key)+r'\s*:\s*(\d+) us\s*$',section,re.M);counters[key]=int(match.group(1)) if match else None
        reasons={}
        for key in ['SW Thermal Slowdown','HW Thermal Slowdown','SW Power Cap','HW Slowdown','HW Power Brake Slowdown']:
            match=re.search(r'^\s*'+re.escape(key)+r'\s*:\s*(Not Active|Active)\s*$',section,re.M);reasons[key]=match.group(1) if match else None
        sm=re.search(r'^\s*SM\s*:\s*(\d+) MHz\s*$',section,re.M)
        result[str(i)]={'counters_us':counters,'reasons':reasons,'current_SM_MHz':int(sm.group(1))}
    return result

def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();baseline=BASE/'gpu23_performance_check.txt';latest=BASE/'gpu23_performance_after_borrow.txt'
    latest.write_text('UTC '+now+'\n'+subprocess.check_output(['nvidia-smi','-q','-d','PERFORMANCE,CLOCK','-i','2,3'],text=True))
    p0=perf(baseline.read_text());p1=perf(latest.read_text());thermal={'first_file_sha256':sha(baseline),'last_file_sha256':sha(latest),'first_utc_header':baseline.read_text().splitlines()[0],'last_utc':now,'gpus':{}}
    for card in ['2','3']:
        thermal['gpus'][card]={**p1[card],'counter_increase_us':{k:p1[card]['counters_us'][k]-p0[card]['counters_us'][k] for k in p1[card]['counters_us']}}
    thermal['interpretation']='No active thermal slowdown and no additional thermal-counter time in this window if deltas are zero. Lower-than-max dynamic clocks alone are not throttling. No counterfactual estimate of MTA impact on throughput.'
    save(BASE/'gpu23_thermal_counter_comparison.json',thermal)
    # Validate newly generated hardware-bound signatures without reading decoded text.
    checks={};uuids={line.split(',')[0].strip():line.split(',')[1].strip() for line in subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid','--format=csv,noheader'],text=True).splitlines()}
    for p in (BASE/'prefix254/generation.private').glob('*/*.json'):
        x=load(p)
        if 'execution_signature' not in x:continue
        sig=x['execution_signature'];card=x['physical_gpu'].split(':')[1]
        normalize=lambda value:str(value).removeprefix('GPU-').lower()
        assert sig['prompt_sha256']==x['signature']['prompt_sha256'] and normalize(sig['device_uuid'])==normalize(x['result']['device_uuid'])==normalize(uuids[card])
        assert x['execution_signature_sha256']==hashlib.sha256(json.dumps(sig,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert x['result']['injection_count']==1;checks[card]=checks.get(card,0)+1
    save(BASE/'borrowed_hardware_signature_check.json',{'utc':now,'checked_rows_per_card':checks,'all_passed':True,'no_PAIR_outcome_labels_read':True,'uuid_format_note':'PyTorch stores bare UUID; nvidia-smi adds GPU- prefix. Validation strips only that prefix and normalizes case. Original execution signatures and generated rows are unchanged.'})
    public=load(OUT/'absolute_refusal_and_baseline_changes.json')['datasets'];decomp=load(OUT/'refusal_decomposition.json');sample=load(OUT/'sampling_replay_checks.json');labels=load(OUT/'uncertain400_model_labels.json');generation=load(OUT/'uncertain400_generation_check.json');status=load(BASE/'borrowed_gpu_projects_status.json');timing=load(BASE/'borrowed_gpu_measured_throughput.json');gate=load(BASE/'gpu0_zero20_result.json');freeze=load(BASE/'gpu0_borrow_freeze_receipt.json')
    scope=load(BASE/'nine_read_20261109/supplemental_tables.json')['unit_table'];baseline_ref=scope[0];refrows=[]
    for row in scope:
        refrows.append({'condition':row['condition'],'v2_refusal_pct':row['v2_refusal_pct'],'v2_change_vs_alpha0_pp':row['v2_refusal_pct']-baseline_ref['v2_refusal_pct'],'WG_refusal_bounds_pct':row['WG_refusal_bounds_pct'],'WG_change_vs_alpha0_bounds_pp':[v-baseline_ref['WG_refusal_bounds_pct'][0] for v in row['WG_refusal_bounds_pct']]})
    seed_summary={rule:{'n_seeds':5,'mean_change_pp':float(np.mean(values)),'t95_df4_pp':interval(values)} for rule,values in [('v2',[r['v2_change_vs_alpha0_pp'] for r in refrows[1:6]]),('WG',[r['WG_change_vs_alpha0_bounds_pp'][0] for r in refrows[1:6]])]}
    save(OUT/'harmful_refusal_baseline_changes.json',{'utc':now,'rows':refrows,'five_seed_summary':seed_summary,'source_sha256':sha(BASE/'nine_read_20261109/supplemental_tables.json'),'interpretation':'Single-seed rows are point observations from one trained vector. Five-seed t intervals use df4 and condition on the fixed baseline; they are distinct from prompt bootstrap intervals and do not quantify full trainer population variation.'})
    lines=['# GPU0借用、项目归属与公开侧追加读数','',f'生成UTC {now}；PAIR-500条件效应和alpha0有害标签未读。','',
        f'调度追加#8 SHA256 {freeze["doc_sha256"]}；冻结UTC {freeze["frozen_utc"]}，push commit {freeze["commit"]}。用户确认已告知hzx；GPU0最迟18:00 JST让出，提前请求按行边界退出。','',
        f'GPU0门：{gate["started_utc"]}至{gate["completed_utc"]}，字节{gate["byte_equal"]}/{gate["n"]}，输入哈希/单次注入/零范数均通过，结果SHA256 {sha(BASE/"gpu0_zero20_result.json")}。','',
        '旧双卡控制器完成在途批次后退出；1900个交接前文件SHA全部不变。新三卡控制器经登记启动，条件×行分工、门禁和租约未放宽。实际让卡测试完成当前1行后退出，149个旧文件SHA未变；测试标记已清除并恢复生产。PAIR仍是原worker2295103，其登记启动器为2295099，历史OOM重启计数仍1。两个GPU交替工作，瞬时0%不是等数据/故障证据。','',
        '## 项目归属快照','',f'快照UTC {status["utc"]}。账号不等于项目。','', '| 节点 | 账号 | 项目 | worker PID | 登记PID | 命令 |','|---|---|---|---:|---|---|']
    for node,group in [('innet',status['innet']),('node01',status['node01'])]:
        for x in group['compute']:lines.append(f'| {node} | {x["account"]} | {x["project"]} | {x["pid"]} | {x["registry_pids"]} | {x["command"].strip()} |')
    for x in status['node01']['early_WG_batch_workers']:
        if not any(r['pid']==x['pid'] for r in status['node01']['compute']):lines.append(f'| node01 | {x["account"]} | Def/early-WildGuard（加载/校验中，当前未列CUDA上下文） | {x["pid"]} | {x["registry_pids"]} | {x["command"].strip()} |')
    lines+=['','node01 GPU0的659MiB不是一个计算PID：全表显示Xorg2142/4155、gnome2311/4270、远程桌面4522/4595/4617和chrome4684等图形进程。早期WG计算PID2625063加载时占约14866MiB，登记匹配；GPU0持续预留给评分，批间/加载时不放生成。MTA的trigger27351结束后转入train1468669，属于外部项目，未发信号、未改配置。','',
        '## 降频检查','',f'首份原始输出SHA256 {sha(baseline)}；后份 {sha(latest)}。','', '| GPU | 当前SM MHz | 当前原因 | 热降频累计增加us | 功耗限幅累计增加us |','|---|---:|---|---:|---:|']
    for card,x in thermal['gpus'].items():lines.append(f'| {card} | {x["current_SM_MHz"]} | {x["reasons"]} | {x["counter_increase_us"]["SW Thermal Slowdown"]} / HW {x["counter_increase_us"]["HW Thermal Slowdown"]} | {x["counter_increase_us"]["SW Power Capping"]} |')
    lines+=['','历史累计不代表当前降频。没有给MTA造成的吞吐损失编造数值；各条件实测时间另表。','',
        '## 各条件的绝对拒答和相对alpha0变化','', '| 条件 | XSTest safe% / delta pp | OR-Hard% / delta pp | WJB良性% / delta pp | XSTest unsafe% / delta pp |','|---|---|---|---|---|']
    datasets=list(public)
    # Fixed display order, independent of mapping insertion order.
    datasets=['xstest_safe','or_hard','wildjailbreak_benign','xstest_unsafe']
    for i in range(10):
        parts=[public[d]['units'][i] for d in datasets];lines.append('| '+parts[0]['condition']+' | '+' | '.join(f'{x["absolute_refusal_pct"]:.4f} / {x["change_vs_alpha0_pp"]:+.4f}' for x in parts)+' |')
    lines+=['','| 集合 | 五seed学出减alpha0均值pp | seed t95(df4) |','|---|---:|---|']
    for d in datasets:
        x=public[d]['across_five_seed_changes_t'];lines.append(f'| {d} | {x["mean_pp"]:+.4f} | {x["t95_pp"]} |')
    lines+=['','逐seed提示配对t区间已在absolute_refusal_and_baseline_changes.json按条件保存；它不是单seed训练重复区间。每个seed只有一次训练，不能声称估计了该seed的重训方差。主文仍用已冻结的提示配对自助区间；这里的seed t是追加描述。','',
        '| 有害侧条件 | v2绝对拒答% | v2减alpha0 pp | WG拒答%边界 | WG减alpha0 pp边界 |','|---|---:|---:|---|---|']
    for x in refrows:lines.append(f'| {x["condition"]} | {x["v2_refusal_pct"]:.2f} | {x["v2_change_vs_alpha0_pp"]:+.2f} | {x["WG_refusal_bounds_pct"]} | {x["WG_change_vs_alpha0_bounds_pp"]} |')
    lines+=['',f'有害侧五seed拒答增量t95：{seed_summary}。','',
        '## 五条400-token补读','', '| 复核编号 | 条件 | 原ID | 120复跑一致 | 400前缀一致 | 400分类 |','|---:|---|---|---|---|---|']
    byindex={x['review_index']:x for x in labels['labels']}
    for x in generation['rows']:lines.append(f'| {x["review_index"]} | {x["condition"]} | {x["original_id"]} | {x["stored120_vs_replay120_byte_equal"]} | {x["replay400_starts_with_stored120"]} | {byindex[x["review_index"]]["category"]} |')
    lines+=['','400-token补读R0、RA0、W1、C3、U1；剩余U是澄清式非回答，没有明确拒答。四条重分词长度400，尚有未读的后续；该旧批量函数补读未保存原始EOS，不把代理当真值。标注同模型、共享上下文、未经人工校准；原120-token五条U及保守线失败不改。','',
        '## 重抽清单与拒答分解','']
    for x in sample['checks']:lines.append(f'- {x["file"]}：重生SHA={x["regenerated_sha256"]}，原SHA相同，字节一致={x["byte_equal"]}。')
    lines+=['',f'拒答分解输出SHA256 {sha(OUT/"refusal_decomposition.json")}；脚本SHA256 {decomp["script_sha256"]}。包含两个判官各九单元的v2/并集拒答率、未拒答有害比例、拒答增量预测对观察变化、下翻/上翻计数；事后描述，不是机制检验。','',
        '## 实测吞吐与ETA','',f'各条件采用最近至多三份完成且>=25行的批次；不含加载/等卡。快照UTC {timing["utc"]}。','', '| 条件 | 已存行 | 定时样本行 | 秒/行 | 单卡行/小时 |','|---|---:|---:|---:|---:|']
    for x in timing['rows']:lines.append(f'| {x["condition"]} | {x["saved_rows"]} | {x["timed_completed_rows"]} | {x["seconds_per_row"]:.2f} | {x["rows_per_hour_per_active_card"]:.1f} |')
    pair=status['node01']['pair'];eta=datetime.datetime.fromisoformat(status['utc'])+datetime.timedelta(seconds=(500-pair['completed_rows'])*pair['seconds_per_row'])
    lines+=['',f'PAIR {pair["completed_rows"]}/500，累计{pair["seconds_per_row"]:.2f}秒/行，按累计速度外推搜索结束{eta.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat()}，不含后续中断。现有前缀未完成工作约{timing["remaining_to_accepted_prefix_gpu_hours"]:.2f}卡小时，补至500约{timing["remaining_to500_gpu_hours"]:.2f}卡小时，均未含加载/判官。不是1.5倍吞吐承诺；最终评测仍受搜索结束、GPU0到期和双卡判官窗口约束。','',
        '新worker的各卡/条件逐行计时另存于项目快照；不同条件分列，不把短样本速率外推给全部条件。','']
    doc=ROOT/'docs/255_PUBLIC_FOLLOWUP_AND_GPU0_HANDOFF.md';doc.write_text('\n'.join(lines)+'\n')
    generated=ROOT/'paper/generated/public_refusal_followup.tex';generated.write_text('\\paragraph{Truncation follow-up.} The five uncertain benign WildJailbreak random-condition responses were regenerated in their original batch compositions at120 and400 tokens. All five120-token replays and400-token prefixes match the stored text. Model rereading assigns three to substantive compliance, one to compliance with a warning and one to a clarification without a substantive answer; none is read as an explicit refusal. Four outputs still retokenize to400 tokens, and raw EOS was not saved by this legacy-batch supplement. The original120-token uncertainty labels and failed conservative line are retained; this is shared-context model annotation, not independent calibration.\n')
    p=ROOT/'paper/generated/public_refusal_results.tex';s=p.read_text();entry='\\input{generated/public_refusal_followup}'
    if entry not in s:p.write_text(s+'\n'+entry+'\n')
    manifest={'utc':now,'report_sha256':sha(doc),'files':{str(p.relative_to(ROOT)):sha(p) for p in [doc,BASE/'gpu0_zero20_result.json',BASE/'gpu0_borrow_publication.json',BASE/'gpu0_cooperative_release_check.json',BASE/'borrowed_hardware_signature_check.json',BASE/'gpu23_thermal_counter_comparison.json',generated,*[p for p in OUT.glob('*.json')]]},'PAIR_outcomes_read':False,'no_raw_prompt_or_response_text':True}
    save(BASE/'gpu0_public_followup_report_manifest.json',manifest)
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{now} GPU0_PUBLIC_FOLLOWUP_REPORT reportSHA={sha(doc)} manifestSHA={sha(BASE/"gpu0_public_followup_report_manifest.json")} original120 guard unchanged; sample replay3/3 hashes match; PAIR restart count1; no PAIR effect reads.\n')
    with (ROOT/'docs/OPS_LOG.txt').open('a') as f:f.write(f'{now} GPU_PROJECT_INVENTORY accounts are not projects; PAIR registered timeout2295099->worker2295103; node01GPU0 graphics baseline659MiB plus registered WG jobs reserved. MTA27351 trigger ended then1468669 train, no signal sent. Two public400 shell wrapper failures occurred before Python/model inference (redirection escaping and CRLF path), corrected by Python launcher; not PAIR restarts. Thermal reportSHA={sha(BASE/"gpu23_thermal_counter_comparison.json")}.\n')
    print(json.dumps({'utc':now,'report_sha256':sha(doc),'manifest_sha256':sha(BASE/'gpu0_public_followup_report_manifest.json'),'thermal':thermal,'seed_refusal_summary':seed_summary,'hardware_checks':checks},ensure_ascii=False))

if __name__=='__main__':main()
