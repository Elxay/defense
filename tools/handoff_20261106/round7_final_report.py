from pathlib import Path
import json,hashlib,datetime
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round7';R6=B/'results/audit/handoff_round6'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
S=load(O/'final_status_snapshot.json');A=load(R6/'random_references_complete_results.json');C=load(R6/'doc250_complete_results.json');D=load(O/'window_frontier_results.json');G=load(O/'guard_paired24.json');W=load(O/'wjb_all_flips228_fullread.json');V=load(O/'doc246_adv52_fullread.json')['summary'];K=load(O/'old_backend_comparison980.json')
assert C['k_pass']==5 and not A['original_addendum7_criterion_met']and A['original_addendum7_k']==3
assert sum(z['label_discordant']for z in K)==0 and max(z['max_abs_p_delta']for z in K)==0
assert D['joint_same_backend']['outside_interpolation_range']==4764
assert len(G['rows'])==24 and G['cached48_max_abs_delta']==0
assert len(W['items'])==228
add8=(B/'docs/239_ADDENDUM8_RANDOM_REFERENCES.md').read_text();assert sha(B/'docs/239_ADDENDUM8_RANDOM_REFERENCES.md')=='da60bc663af9ad93af7c5467e0ae0efdafbfbb0bed6151438ab9fc536ccb8441'
quote=add8.split('## 分析与读取\n',1)[1].split('\n原始攻击与输出不推送。',1)[0].strip()
lines=['# 270 — 过夜队列最终汇报','',f"状态快照：{S['jst']}。以下作业已完成；完成心跳停止刷新，年龄不代表卡住。innet GPU2/3已回到15MiB空闲，GPU0/1未使用。",'', '| 作业 | PID | 主机/GPU | 条数 | 秒/条 | 心跳年龄 |','|---|---|---|---|---|---|']
for z in S['jobs']:lines.append(f"| {z['job']} | {z['pid']} | {z['host']} {z['gpu']} | {z['completed']}/{z['total']} | {z['seconds_per_item']:.2f} | {z['heartbeat_age_s']/60:.1f}min |")
lines+=['','生成速度是全程不含加载；HF/Guard是阶段墙钟折算（含加载/交接），C2是检查点49→600增量折算。rand2/rand3首25条分别15.64/13.61秒。控制器1467341 phase=complete；GPU进程均退出。','', '## 固定结论与addendum8原文','', '#7原结论3/5未达至少4/5，严格留出s5–s7为2/3。四方向只是事后补充，不重判通过。','',quote,'', '## 随机方向结果','', '| 方向 | 有害n/300 | ASR% | 相对alpha0降幅pp |','|---|---|---|---|']
for z in A['rows']:lines.append(f"| rand{z['direction']} | {round(z['asr_pct']*3)} | {z['asr_pct']:.2f} | {z['alpha0_reduction_pp']:.2f} |")
lines+=['','负降幅表示该方向ASR略高于alpha0，不据此宣称差异显著。','', '| 随机参照 | ASR均值±方向样本SD% | learned优势均值±seed样本SD pp | 条件seed t95 pp |','|---|---|---|---|']
for z in A['variants'].values():lines.append(f"| {z['n_directions']}方向 | {z['direction_asr_mean_pct']:.2f} ± {z['direction_asr_sample_sd_pp']:.2f} | {z['learned_seed_benefit_mean_pp']:.2f} ± {z['learned_seed_benefit_sample_sd_pp']:.2f} | [{z['seed_t95_pp'][0]:.2f},{z['seed_t95_pp'][1]:.2f}] |")
lines+=['', '各seed对各方向的优势完整20项见[264](264_WJB_RANDOM_REFERENCES.md)。随机seed2/3与array/.npy完整SHA见[向量清单](../manifests_window7_preread.json)，对应私有results/frozen_vectors的只读向量及manifest；旧向量未改。新随机方向跨节点生成复现未补，保留该局限，不能用判官后端一致性替代生成一致性。','', '## 后端统一的d','', '9个可追溯历史参照为FRONTIER旧8点加alpha0，含与seed云重复的s1/s2；不同alpha只有7。去重14份原生成、980条，同HF_node01缓存对hf_innet重判的所有标签和PYes逐项一致（max absΔP=0）。新点仍使用既有hf_innet来源。','', '| 版本 | d均值pp | 条件seed t95 pp |','|---|---|---|']
for name,z in D['variants'].items():lines.append(f"| {name} | {z['mean_pp']:.2f} | [{z['t95_pp'][0]:.2f},{z['t95_pp'][1]:.2f}] |")
j=D['joint_same_backend'];lines+=['','联合重抽沿用原round2的RNG2026110602、重合横轴平均和每次seed抽样，隔离后端影响，不混入算法变化。三行：','', '| 联合区间口径 | n重抽 | 95% pp |','|---|---|---|']
for key,label in [('fixed5_conditional','固定5seed，仅可内插'),('seed_cluster_conditional','seed聚类，仅可内插'),('boundary_clipped_diagnostic','截平诊断')]:
 z=j[key];lines.append(f"| {label} | {z['n']} | [{z['ci95'][0]:.2f},{z['ci95'][1]:.2f}] |")
lines+=['','4764/10000不可内插，前两行是条件区间；截平只作诊断。三行均含0且不落在±3pp内：不确定，未检出差异，也未达到等价边界。[完整同后端表及24条Guard值](267_JUDGE_WINDOW_RESULTS.md)。','', '## Guard配对','',f"相同24个提示均在baseline和A输出下被HF判有害。阈值0.2：baseline检出{G['baseline_blocks']}/24，A检出{G['A_blocks']}/24；baseline-only={G['discordant_baseline_only']}，A-only={G['discordant_A_only']}，探索性精确p={G['exploratory_exact_p']:.6f}。Punsafe均值差A−baseline={G['mean_delta_A_minus_baseline']:.6f}，配对bootstrap95=[{G['mean_delta_pair_bootstrap95'][0]:.6f},{G['mean_delta_pair_bootstrap95'][1]:.6f}]。48次新前向对原缓存最大差0。",'', '31/40对12/26是不同有害集合上的HF口径检出比例，不称这个配对检验；13/16对18/24覆盖率不支持A先处理掉“容易项”的解释。输出文本/角色/免责声明影响Guard是假设，不写机制。','', '## docs250最终5/5及规格','',f"首次完整效应读取{C['first_effect_read_utc']}，即23:58:47 JST；全部五seed出齐后统一分析，已写日志。",'', '| seed | adversarial新增 | vanilla新增 | DD pp | 95% pp | 数值达标 |','|---|---|---|---|---|---|']
for z in C['rows']:lines.append(f"| s{z['seed']} | {z['adversarial_new']} | {z['vanilla_new']} | {z['double_difference_pp']:.2f} | [{z['ci95_pp'][0]:.2f},{z['ci95_pp'][1]:.2f}] | 是 |")
lines+=['','固定300对，任一侧alpha0命中v2则整对排除，主分析292对；该排除说明书面写于s3/s5完成后，承认生成后补充。逐seed DD=100×mean(Radv−Rvan)，vanilla聚类bootstrap2000次、seed20261106、同组重抽用于五seed。至少4/5 DD≥3pp且95%区间排除0，实际5/5。alpha0复用innet缓存依据是node01前20对40个输出逐字节一致；不当成全部300对跨节点等价，原同节点条款记复用例外。完整规格与哈希见[265](265_BENIGN_SEEDS_RESULTS.md)。','', '## 对称全文复核','', '| 条件 | 全部R+RA/翻转 | 仅英语主体R+RA/翻转 |','|---|---|---|']
for cond in ['old_s0','old_s3','old_s4','rand0','rand1']:
 z=next(r for r in W['summary']if r['condition']==cond and r['scope']=='all');e=next(r for r in W['summary']if r['condition']==cond and r['scope']=='English_primary');lines.append(f"| {cond} | {z['model_refusal_R_RA']}/{z['n']} | {e['model_refusal_R_RA']}/{e['n']} |")
lines+=['','全部228条翻转的全文范围、语言、规则/模型标签与SHA见[269](269_FULL_READ_COMPLETION.md)。rand0有拒答语句后继续给键盘监听代码的WC边界；另有角色隐含回避，边界敏感性并列。拒答占比只作描述，非英语判官有效性未验证。docs246 adversarial22全文为R20/RA2，包含一个处方格式/澄清边界；阴性样本30未见明确R/RA、9项截断待定。模型标注、未经人工校准，原规则DD6.85不改。','', '## 限时干预决定','', '做一版训练数据组成干预，训练尚未启动。[252](252_STYLE_HARD_NEGATIVE_INTERVENTION.md)已在此次docs250聚合之前、训练之前冻结。60个WJB良性vanilla组、双侧120新增输入，排除与分组/embedding0.85审计完成后才生成Llama目标；保留损失总权重4.5不变。先复建旧seed3，cos>0.999且val70标签差≤1才继续，训练器不换。alpha只按val70 HF匹配，留出输出不用于选择；冻结C2及合法/WJB护栏。11/9 20:00 JST无首批向量即停，11/10 00:00前无完整结果即按未完成收口，不推迟论文骨架。','',f"docs252 SHA256={sha(B/'docs/252_STYLE_HARD_NEGATIVE_INTERVENTION.md')}",'', '## 哈希与验证','']
sources=[O/'final_status_snapshot.json',O/'old_backend_comparison980.json',O/'window_frontier_results.json',O/'guard_paired24.json',R6/'random_references_complete_results.json',R6/'doc250_complete_results.json',O/'wjb_all_flips228_fullread.json',O/'doc246_adv52_fullread.json']
for p in sources:lines.append(str(p.relative_to(B))+' '+sha(p))
(B/'docs/270_OVERNIGHT_FINAL_REPORT.md').write_text('\n'.join(lines)+'\n')
print('FINAL_REPORT_WRITTEN; ALL_NUMERIC_AND_SCOPE_ASSERTIONS_PASS')
