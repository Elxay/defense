"""Generate the handoff report and manuscript paragraphs from private numeric artifacts."""
from pathlib import Path
import json,hashlib,datetime,numpy as np
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round9';T=B/'results/style_retrained'
def load(n):return json.loads((O/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):
 q=p.with_suffix('.tmp');q.write_text(s.rstrip()+'\n');q.replace(p)
h=load('historical_rebuild_details.json');n=load('style_top_neighbors_final60.json');sens=load('doc250_posthoc_sensitivity.json');targets=json.loads((T/'style_training_targets.json').read_text());repeat=load('repeat_comparison.json')if(O/'repeat_comparison.json').exists()else None
lines=['# 272 — 同流水线重训对照与重复性','', '生成UTC：'+datetime.datetime.now(datetime.timezone.utc).isoformat()+'。', '', '## 252追加2（训练前冻结）','', '生效文件：252_ADDENDUM2_RETRAINED_CONTROLS.md；SHA256='+sha(B/'docs/252_ADDENDUM2_RETRAINED_CONTROLS.md')+'；训练前公开commit44de24616cb8a8e2cd172eceb16e63c7ac18ef4e。原≤1条门槛保留失败，不改判。主对照换同流水线、同初始化、同物理卡的keep60-only重训；seed3重复A事前指定为主对照，不择优。历史冻结向量只作附加参照。','', '主要量为五seed的DD重训对照−DD处理，均值≥2pp且df4双侧95% t区间排除0；均值护栏为合法≤+1pp、WJB有害ASR≤+5pp。处理α在固定0.25/0.5/0.75/1/1.25/1.5网格匹配重训对照α1自身val70 HF ASR；差>5pp不可比。全部匹配冻结后，才生成两条件各300有害和600配对。','', '五seed区间半宽为1.242*s_d；若配对差SD为2.7–3.8pp，需要观察均值约3.35–4.72pp才能排除0。这是精度示例，不是80%功效计算。未通过应结合实际SD/区间写未检出足够改善，不证明无效。', '', '## 不是同一个复建向量','']
for k,p in h['paths'].items():lines.append(k+'：'+p['file']+'；SHA256='+p['sha256'])
for k,c in h['comparisons'].items():lines.append(f"{k}: cosine={c['cosine']:.12f}, angle={c['angle_degrees']:.6f}deg, difference_norm={c['difference_norm']:.8f}")
lines+=['', '旧冻结ASR19/70=27.1429%；本轮复建16/70=22.8571%。1条上翻、4条下翻，逐条标签不一致5/70=7.1429%，净ASR变化−4.2857pp；不把7.1%逐条变化写成7.1pp ASR方差下界。五条两版均>700token、均EOS，未触及2400上限。首个字符分叉和token分叉均从0计，token为解码文本重新分词的位置。','', '| id | 方向 | 原token→复建token | 首个字符分叉 | 首个重分词token分叉 | 原P→复建P |','|---|---|---|---|---|---|']
for r in h['rows']:lines.append(f"| {r['id']} | {r['direction']} | {r['old_new_tokens']}→{r['new_new_tokens']} | {r['first_different_character_0based']} | {r['first_different_retokenized_token_0based']} | {r['old_p']:.9f}→{r['new_p']:.9f} |")
lines+=['','## 同流水线两次seed3','']
if repeat:
 lines +=[f"同初始化、目标缓存、工作脚本、节点与物理GPU2的校验通过。独立A/B优化目录，不复用对方optimizer。cos={repeat['cosine']:.12f}；差范数={repeat['difference_norm']:.8f}；向量字节相同={repeat['vector_byte_equal']}；val70变化{repeat['label_changes']}/70（上翻{repeat['up']}、下翻{repeat['down']}），ASR计数={repeat['harmful_counts']}。",'',repeat['interpretation']+'。只报告这一次重复对的观察；不能将8seed云的哪部分归于重复噪声作定量分解。']
else:lines+=['重复训练/判分尚未全完成，不报告部分标签比较。']
lines+=['','## 目标过滤、权重与排序','', f"最终60组/120输入，固定候选池顺序检查{len(targets['records'])}组。2组原v2阳性、1组本地模型标非回答、1组GPT全文跟读保守标非回答/不确定而排除。该筛选是在任何处理优化前完成。",'', '对照60×0.075=4.5；处理60×0.0375=2.25，加120×0.01875=2.25，共4.5。fit12及目标缓存不变。','', '排序不是挑选结果：标准化vanilla组键先字典序，numpy default_rng(202611070252)做permutation；按同一RNG从组内原TSV行序选一个变体。原120候选池顺序不改，取双侧目标通过的首60组。目标标注读全文请求及已生成200token全文，由固定Llama3.1-8B快照作结构化标注；GPT复核10组20条完整回应，覆盖非回答排除项及能力/虚构措辞。其余目标不冒称逐条GPT校准。所有标签未经独立人工校准，事实准确性不是这次筛选的验证项目。','', '目标最终SHA256='+sha(T/'style_training_targets.json')+'；完整筛选提示词见tools/handoff_20261106/round9_target_completion_rubric.txt。','', '## 最近5对候选组','', '| 组A | 组B | 侧A/侧B | cosine |','|---|---|---|---|']
for r in n['pool_top5']:lines.append(f"| {r['a']['id']} | {r['b']['id']} | {r['a']['side']}/{r['b']['side']} | {r['cosine']:.6f} |")
lines+=['', '0.84615对应WHO网址与总部地址，两组不在最终训练60组中；最终60组内部最大0.688404。最终60组最近5对另列：','', '| 组A | 组B | cosine |','|---|---|---|']
for r in n['final60_top5']:lines.append(f"| {r['a']['id']} | {r['b']['id']} | {r['cosine']:.6f} |")
lines+=['', '7个embedding排除组的最近参考分别来自val296（5组）和docs250（2组）。0.85阈值下仍可能主题相似；同源WJB干预不证明其他包装泛化。','', '## 排除11行的事后敏感性','', '11个条件×条目行涉及4个配对ID：183985、207563、249215、249682。为让五seed使用同一分析集，主敏感性在所有seed中统一剔除这4对，292→288；另附按seed仅剔除已复核行所在配对的诊断。不是剔除11个互异提示；分母必须随排除更新。冻结主分析不动。','', '| seed | 原DD | 共同288对DD | vanilla新增 | 各seed仅剔对应行DD / n |','|---|---|---|---|---|']
old=json.loads((B/'results/audit/handoff_round8/doc250_descriptive_stats.json').read_text())['rows']
for r,z in zip(sens['rows'],old):
 u=r['shared_union'];c=r['condition_rows'];lines.append(f"| s{r['seed']} | {z['docs250_DD_pp']:.4f} | {u['DD_pp']:.4f} | {u['vanilla_new']}/{u['n']} | {c['DD_pp']:.4f} / {c['n']} |")
lines+=['', '共同子集DD均值='+str(float(np.mean([r['shared_union']['DD_pp']for r in sens['rows']])))+'pp；变化小于先前约1pp的预期，不能按预期替换实际值。两种剔除均为post-hoc，不计入干预主判据。','', '## 队列与来源','', '已登记独立CPU控制器，先完成A/B标签比较，再两张innet获准卡训练配对条件；全部向量出齐后两节点五卡生成网格，innetGPU2/3统一HF判分；匹配冻结后跑选定alpha的留出生成。所有窗口保留原wait_gpu>2000MiB拒绝，无绕过，不占innetGPU0/1。每10条（合法每8条完整batch）原子落盘，生成可按相同签名续跑。预算以首25条实测速率更新，训练与评估未完成不写成功。','']
for p in [O/'historical_rebuild_details.json',O/'doc250_posthoc_exclusion_spec.json',O/'doc250_posthoc_sensitivity.json',O/'style_top_neighbors_final60.json',O/'target_followup_review.json']+([O/'repeat_comparison.json']if repeat else[]):lines.append(str(p.relative_to(B))+' SHA256='+sha(p))
put(B/'docs/272_RETRAINED_CONTROLS_AND_REPEATS.md','\n'.join(lines))
# Replace only our generated section; earlier manuscript history stays intact.
p=B/'docs/251_EVAL_TRAPS_DRAFT.md';text=p.read_text();marker='\n\n<!-- ROUND9_REPRODUCIBILITY_BEGIN -->';text=text.split(marker)[0];para='高度相似的重训向量并不保证逐条判定复现。冻结seed3与本轮复建向量cosine为0.999920，夹角约0.727°、差范数0.0661；在70条固定提示上，五条标签改变，其中一条上翻、四条下翻，ASR由19/70变为16/70。五条都是完整EOS长输出，首个分叉已出现在第11–310个重分词token，而非仅由截断造成。它直接展示了高余弦相似度验证遗漏的生成和判定敏感性；5/70逐条不一致不等于7.1pp的ASR方差下界，也不能据此分解八seed离散度。'
if repeat:para+=f" 在固定同一初始化、缓存、代码和物理卡的两次独立seed3优化中，向量cosine为{repeat['cosine']:.9f}，val70又有{repeat['label_changes']}/70条标签不同（上翻{repeat['up']}、下翻{repeat['down']}）。"+('这提供了本流水线重复训练变异的直接实例；单seed名次不宜当成稳定性质。'if repeat['label_changes']else'这一次未观察到标签重复变异；历史重建差异的完整来源仍未确定。')
para+=' 数据组成干预因此采用同流水线重训的配对对照，保留失败门槛记录，历史冻结向量仅作附加参照。'
put(p,text+marker+'\n\n'+para)
print('REPORT272_WRITTEN',bool(repeat))
