from pathlib import Path
import json,datetime,hashlib,subprocess
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round10';T=B/'results/style_retrained'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run(['python3',str(B/'tools/handoff_20261106/round10_eta.py')],stdout=subprocess.DEVNULL,check=True)
m=load(T/'alpha_matches_frozen.json');d=load(O/'training_repeat_dispersion.json');cards=load(O/'verified_card_mapping.json');eta=load(O/'measured_eta_snapshot.json');audit=load(O/'plain_data_audit.json');targets=load(B/'results/plain_arm/plain_training_targets.json')
lines=['# 274 — 第三臂、状态机与第一批网格结果','', '报告UTC：'+datetime.datetime.now(datetime.timezone.utc).isoformat(),'', '#2匹配表已在UTC '+m['utc']+'（JST08:22:52）冻结，#3写在其后。原表/判据保留，不能称#3在原匹配冻结前。','', '追加3 SHA256='+sha(B/'docs/252_ADDENDUM3_PLAIN_ARM_INTERPOLATION.md')+'；公开commitcdf7293ab66f1ba2b24dbe3096f8eacc09ee1955，早于任何第三臂训练/输出。固定s3/4/5；新增120个WJB vanilla_benign输入，每条0.01875，keep60每条0.0375，总4.5。第三臂标签未经人工校准。','', '最近点差>5pp时，目标被相邻alpha的ASR括住才双端点留出并在ASR轴插值；多括号取最小跨度再较小左alpha。不外推，不用alpha>1.5。区间含0不自动称相当；n3额外收益及近似规则按追加3探索性报告，不改写n5原主结论。','', '## 原两臂状态机','', '| 步骤 | 前置/输出 | 失败行为 |','|---|---|---|','| 审计/目标 | 全文窗口审计、目标/初始化哈希冻结 | 不足/失败不训练 |','| 重复性 | A/B各70条齐，20条判官门通过，A事前固定为主对照 | 原旧门槛失败保留，不择优换A/B |','| 配对训练 | 同seed/初始化/缓存/代码/物理卡，10向量齐 | 任一失败停止下一阶段，缓存保留，不删seed |','| 生成网格 | 对照各alpha1，处理各6alpha；35条件各70攻击+400合法batch8，后取388 | 不改批组成，签名不符停止 |','| 判网格 | 全35条件齐，20条核对至少8中间值且差<1e-3，INVALID0 | 失败不强转阴性，不挑alpha |','| 冻结匹配 | 脚本最近ASR，平手合法新增再alpha；差<=5pp | 不可比不删seed或改n4宣布成功 |','| 记录再生成 | 匹配表原子落盘，SHA写PREREG_LOG并关闭文件，再rsync/启动300有害+600配对 | 仅续跑同签名缓存，不读部分DD |','| 全量分析 | 全10条件输出/判分齐，首次效应读取时间入日志 | n5配对t与均值护栏完整报告 |','', '原匹配表SHA256='+sha(T/'alpha_matches_frozen.json'),'', '## 第三臂状态机','', '240候选审计 → 固定顺序目标筛选/GPT补读 → 数据SHA冻结 → 三seed同卡训练 → 各6alpha网格 → 等原#2判官窗口完成 → 同判官门/网格评分 → 最近点或相邻端点方案生成并哈希入日志 → 必要端点各300+600 → 全3seed齐后补充分析。不可比不删seed，报告补充不可评估。','', 'GPU3目标窗口仅暂停登记的原控制器及s7生成，保留对照300+600与处理10条；原不可变控制器已重启，s7从缓存恢复，最多9条未落盘项可重算。调度不依据标签/双重差，原匹配SHA不变。','', '## 卡位（两训练臂metadata逐项验证）','', '| seed | 重训对照 | 包装臂 | 无包装计划 | 配对评估 |','|---|---|---|---|---|']
for r in cards:lines.append(f"| s{r['seed']} | innet/{r['control_GPU']} | innet/{r['wrapped_GPU']} | "+(f"innet/{r['plain_GPU_planned']}"if r['seed']<=5 else'不做')+f" | {r['generation_host']}/{r['generation_GPU']} |")
lines+=['', '所有判官只用innetGPU2/3，先两卡锁再原wait_gpu；innetGPU0/1禁用。','', '## 首批完整网格的原冻结匹配表','', '| seed | 对照ASR% | 包装alpha | 包装ASR% | 合法新增C/388 | 合法新增T/388 | 差pp |','|---|---|---|---|---|---|---|']
for r in m['rows'].values():lines.append(f"| s{r['seed']} | {r['control_asr_pct']:.2f} | {r['selected_alpha']} | {r['selected_asr_pct']:.2f} | {r['control_new_legal']} | {r['selected_new_legal']} | {r['distance_pp']:.2f} |")
lines+=['', '全部35条件见paper/data/style_alpha_grid.csv。合法为规则操作数，无人工校准。所有seed差<=2.86pp；原两臂无需后备端点。只报匹配结果，不报未完成留出效应。','', '## 四次seed3','', '| 运行 | 有害/70 | ASR% |','|---|---|---|']
for name,k in zip(['历史冻结','本轮复建','同流水线A','同流水线B'],d['four_counts']):lines.append(f'| {name} | {k} | {k/70*100:.4f} |')
lines+=['',f"四次SD={d['four_SD_count']:.6f}条={d['four_SD_pp']:.6f}pp；旧8seed SD={d['old8_SD_count']:.6f}条={d['old8_SD_pp']:.6f}pp；方差比={d['variance_ratio']:.6f}、SD比={d['SD_ratio']:.6f}。仅A/B完全共享缓存，两样本还共享冻结s3，不作独立F检验/精确分解。差范数写0.0661，不写0.007。陷阱正文和英文稿已更新。",'', '## 实测预算','', '实际原网格35条件；最慢node01从最后向量出齐到网格完成约4小时，innet约2小时。首25条WJB约10.88–12.95秒/条（innet）、19.17–20.28秒/条（node01）；配对约3.26–3.37秒/条与6.8秒/条。','', 'ETA快照UTC='+eta['utc']+f"，仅生成剩余最大{eta['max_remaining_seconds']/3600:.2f}小时，另加排队/判分。原两臂预计今天14–15时JST；第三臂受三向量/网格/1或2留出端点影响，暂估今晚至明晨，待第三臂首25条重估，不保证该时刻。所有#2向量10/10已完成；原11/9 20:00首批向量及11/10 00:00完整主表止损不变。",'', '## 第三臂数据','',f"候选240，近参考max={audit['max_reference_cosine']:.8f}、跨候选max={audit['max_other_group_cosine']:.8f}。固定顺序检查{len(targets['records'])}保留120；GPT全文补读36，覆盖14排除与22能力/虚构措辞保留。保守筛选有误删，非人工校准/事实准确性验证。目标SHA="+sha(B/'results/plain_arm/plain_training_targets.json'),'', '## 来源SHA256','']
for p in[T/'alpha_matches_frozen.json',O/'training_repeat_dispersion.json',O/'verified_card_mapping.json',O/'measured_eta_snapshot.json',O/'plain_data_audit.json',O/'plain_target_gpt_followup.json']:lines.append(str(p.relative_to(B))+' '+sha(p))
(B/'docs/274_THIRD_ARM_STATE_AND_GRID.md').write_text('\n'.join(lines)+'\n')
(B/'docs/275_ACL_DRAFT_HANDOFF.md').write_text('''# ACL首版交接

paper/使用官方ACL review样式（commit d5adc823ff0f80f98c80405ca0ab66c68e684409）。第1–6节均有英文正文，6张CSV生成表，编译为6页首版；尚非投稿就绪稿，干预留出结果仍待完整读取。

旧249/5.1→新4.1，旧255/5.3→新4.3，旧251陷阱→第5节；中文快照保存在sources/。scripts/export_tables.py从数值来源导出CSV再生成表；--from-csv支持独立重建。全部35点网格另存CSV。原始攻击、输出及训练缓存不入稿件仓库。

六页PNG已检查，无越界排版、未解析引用或重叠；manuscript.pdf为最终本次交付。训练变异、非独立翻转计数、三种前沿联合区间均已进入正文/附录。人工作标注缺口、PAIR独立test未做、Qwen未训练向量、同源数据限制保留。

11/12前完整初稿目标保留：在当前六节上补完整干预结果或未完成说明，统一术语图表和核对相关工作，不将排队实验写成结果。ARR政策已读，见276。
''')
print('REPORTS274_275_WRITTEN')
