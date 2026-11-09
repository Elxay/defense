"""Publish operational tail progress, length audit and draft dependencies only."""
from pathlib import Path
import datetime,fcntl,hashlib,json,re,shutil,subprocess
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';O=B/'tail_contextual_followup_20261109';G=R/'prereg_repo'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def jst(value):return datetime.datetime.fromisoformat(value).astimezone(datetime.timezone(datetime.timedelta(hours=9))).strftime('%m/%d %H:%M:%S JST')if value else'尚未产生'
def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();source=sorted(O.glob('tail_snapshot_*.json'))[-1];x=load(source);c=load(O/'contextual_length_audit.json');doc=R/'docs/254_TAIL_RESOURCE_AND_CONTEXTUAL_FOLLOWUP.md'
    lines=['# 尾部资源与contextual路径核对','',f'状态UTC {x["utc"]}；JST {x["jst"]}。只读进度、长度和运行元数据，不读判分标签。','',
           '公开侧总数1979 = 良性1779（XSTest safe250、OR-Bench-Hard1319、WJB良性210）+ XSTest unsafe200。unsafe已包含在1979内，以下拆列。','',
           '| 条件 | WJB有害/2000 | XSTest safe/250 | OR-Hard/1319 | WJB良性/210 | unsafe/200 | 公开总计/1979 |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for n,z in x['conditions'].items():
        d=z['public']['dataset_counts'];lines.append(f'| {n} | {z["harmful"]["total_rows"]} | {d.get("xstest_safe",0)} | {d.get("or_hard",0)} | {d.get("wildjailbreak_benign",0)} | {d.get("xstest_unsafe",0)} | {z["public"]["total_rows"]} |')
    lines+=['','## 实测速率与ETA','', '| 条件/侧 | 已计时新行 | 含启动秒/行 | v2阶段秒/行 | 剩余卡时（当前速率） | 短期日历ETA |','|---|---:|---:|---:|---:|---|']
    for n,z in x['conditions'].items():
        for kind,a in z.items():
            fmt=lambda v:f'{v:.3f}'if v is not None else'未启动/无实测'
            eta='已齐全'if a['remaining_rows']==0 else jst(a['calendar_ETA_utc_since_v2_rate'])if a['calendar_ETA_utc_since_v2_rate']else'待首批实测'
            lines.append(f'| {n}/{kind} | {a["timed_new_rows"]} | {fmt(a["measured_wall_seconds_per_new_row"])} | {fmt(a["v2_seconds_per_row"])} | {fmt(a["remaining_card_hours_at_current_rate"])} | {eta} |')
    lines+=['','“卡时”只计算生成服务；日历ETA按已观测的调度/让位速率外推，初始样本小且未来条件的输出长度不同。不能把s0速度当A/B实测。未启动条件不报精确完成钟点；此前三条件12–13卡时仍是预算估计。PAIR生成/最终判分优先，辅助尾部不成为PAIR读取前置条件；18:00 GPU0让卡不变。','',
            f'此前辅助缺口可独立触发双卡窗口，影响尾部推进。追加#11先冻结并push，v2于{x["v2_handoff"]["utc"]}接管；{x["v2_handoff"]["unchanged_existing_files"]}个已有生成文件哈希未变。现在只有PAIR待判缓存达到256行或实际搜索结束才启动必要窗口；辅助缓存只复用剩余驻留时间/排在PAIR之后。','',
            '当前租约：'+json.dumps(x['active_leases'],ensure_ascii=False),'',
            '## systemA/B元数据口径','',
            '新记录保存new_tokens、实际EOS观察、系统文本SHA、input_ids SHA、rho_runtime以及nonzero_vector_injection_count。公开批量路径对无向量记录injection_count=0、prefill_hook_count=1；单条统一函数的原generation.injection_count表示钩子调用，零向量也为1，保留该原值，并用nonzero_vector_injection_count=0明确没有非零注入。新wrapper不改变原数值调用，也不追填旧记录。','',
            '## contextual路径','',
            f'核对UTC {c["utc"]}：原始contextual100行均检查源长度；当前已生成{c["measured_generated_inputs"]}个正式模板输入，长度{c["min_tokens"]}–{c["max_tokens"]}，>{1900}为{c["over1900"]}，>2048为{c["over2048"]}，实际分块{c["chunked_inputs"]}。这是当前前缀的长度覆盖，不是最终全量。','',
            '旧night/judge_all.py的>1900分块使用旧CLS_PROMPT，不在PAIR的official contextual调用链中。当前增量和最终HF路径明确拼入原context、行为和冻结512-token输出截段，超过2048则停，不静默截断或改为旧分块。全条件生成完成后重新做长度审计。WildGuard的>4096按另一模型模板另报，不混同。','',
            'copyright只报MinHash命中和拒答，主表不与standard/contextual/JBB平均为ASR；HB400保留为数据集库存n。','',
            '## 完成时间','',
            f'PAIR搜索当前{x["PAIR_search"]["n"]}/500，{x["PAIR_search"]["mean_seconds_per_row"]:.2f}秒/行。搜索实际结束记录：'+('已有记录'if x['search_complete_receipt']else'未产生（搜索仍在运行）')+'；PAIR全条件尾部生成齐全记录：'+('已有记录'if x['target_generation_complete_receipt']else'未产生')+'。',
            'CPU观察器仅写实际事件UTC/文件覆盖，不读取结果；未产生的时间保持空值，不用ETA替代。','',
            f'状态JSON SHA256 {sha(source)}。',f'contextual核对JSON SHA256 {sha(O/"contextual_length_audit.json")}。','']
    qa=O/'first_SYS_A_metadata.json'
    if qa.exists():
        z=load(qa);lines+=['systemA首批实测元数据（仅此样本，不外推未运行B/有害侧）：'+json.dumps(z,ensure_ascii=False),f'首批元数据QA SHA256 {sha(qa)}。','']
    doc.write_text('\n'.join(lines));draft=R/'docs/285_DRAFT_SECTION_DEPENDENCIES.md';draft.write_text(f'''# 11/12初稿依赖

记录UTC {now}。这是写作依赖与排期，不宣称下列全文已经定稿。

- 可先定稿：方法（固定注入、训练/生成/评估路径）、数据集来源/n/标记与库存表、已有证据的陷阱正文、局限。
- 等PAIR500两判官按追加#10读取后定稿：结果的完整数值表与叙述、摘要、引言贡献条目。已有WJB结果可保持来源表，但不提前改摘要。
- 摘要目标11/10晚，整体第1–6节初稿目标11/12不变。固定结果句模板为docs/284_ABSTRACT_RESULT_SENTENCES_TEMPLATE.md，数字从脚本表格填入，采用行口径主估计；不插入绝对ASR或机制句。该模板只适用于完整500行读取，评估不完整时保持空位并写明状态。
- 模型范围：Llama-3.1-8B-Instruct、固定alpha1；Qwen2.5-7B-Instruct仅零训练基线，不加向量结论。
- 人工核对材料已准备、尚无人标注，12/10硬日期；token过期时间仍未核实。
''')
    for n in ['PREREG_LOG.txt','OPS_LOG.txt']:
        with(R/'docs'/n).open('a')as f:f.write(f'{now} TAIL_CONTEXTUAL_FOLLOWUP report_SHA={sha(doc)} source_SHA={sha(source)} contextual_SHA={sha(O/"contextual_length_audit.json")} no effect labels read. DRAFT_DEPENDENCIES_SHA={sha(draft)} methods/traps/dataset/limits first; results/abstract/intro claims wait_PAIR_dual_read; no pooled copyright ASR.\n')
    files=[str(doc.relative_to(R)),str(draft.relative_to(R)),str(source.relative_to(R)),'docs/PREREG_LOG.txt','docs/OPS_LOG.txt','tools/handoff_20261106/report_tail_and_contextual_progress.py','tools/handoff_20261106/publish_tail_contextual_followup.py','tools/handoff_20261106/handoff_lease_priority_v2.py','results/audit/pair500/lease_priority/v2_handoff_complete.json']
    if qa.exists():files.append(str(qa.relative_to(R)))
    for n in files:assert not re.search(r'hf_[A-Za-z0-9]{20,}',(R/n).read_text())
    with(R/'logs/prereg_publish.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
        for n in files:p=G/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
        manifest='manifests_tail_contextual_followup.json';(G/manifest).write_text(json.dumps({'utc':now,'files':{n:sha(G/n)for n in files},'no_outcome_labels_selected':True},indent=2)+'\n')
        subprocess.run(['git','add',*files,manifest],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Record tail resource progress, contextual length limits and draft dependencies'],cwd=G,check=True);commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip();subprocess.run(['git','push','origin','main'],cwd=G,check=True)
    result={'utc':now,'commit':commit,'report_sha256':sha(doc),'snapshot_sha256':sha(source),'contextual_sha256':sha(O/'contextual_length_audit.json')};(O/'publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
