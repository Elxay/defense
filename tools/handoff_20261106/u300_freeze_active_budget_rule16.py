from pathlib import Path
import copy,json
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
newrows=[]
for method in ['PAIR','TAP','AutoDAN']:
 for model in ['llama','qwen']:
  for p in (U/(method+'_progressive')/model).glob('tier88/rows.private/*.json'):
   newrows.append(str(p.relative_to(R)))
assert not newrows,'New 88-tier rows already exist; do not claim a prospective freeze'
doc=R/'docs/300_ADDENDUM16_ACTIVE_CELL_SEARCH_BUDGET_AND_PREPARATION_SCHEDULE.md'
doc.write_text('''# 追加16：按alpha0有效格分配扩档预算、低成本先行及模型准备调度

取代追加15“失败格仍占全档预测成本”的条款。冻结时PAIR/TAP/AutoDAN的88档新增搜索记录为0；既有十个计时行为保留，不重搜、不删。任何搜索类非零重放仍未放行。

1. 先完成每格88档及原SORRY alpha0门。只有明确通过或沿旧INVALID跨线继续的格子进入扩档集合；上界<25%的格子停止，未来220/440预测费用从扩档表剔除。INVALID跨线者暂计成本、标未决，不借解析失败省预算。
2. 600卡小时总账不变。已经实际花掉的所有搜索费（含失败/被闸门淘汰格的先导、88档）仍计入实际已耗；不能退还已花算力。候选档总预测＝全格实际已耗＋仅对活跃格的剩余新增行成本与预计新加载费。取不超剩余预算的最大88/220/440档。W、主轮重放、自适应按原条款另记，不混入600主搜索账。当前轮已纳入Llama/Qwen；Gemma/Mistral加入时采用同一剩余账及同一规则，新增模型未计时成本不记为0，也不据此宣称四模型总预算已可行。
3. 四格88的就绪顺序是PAIR-Llama、PAIR-Qwen、TAP-Llama、TAP-Qwen。按已测窗口法含一次冷启动的88预测排序：3.4099457、5.3782385、21.0453350、35.9078106卡小时。不是直接把含冷启动440总数除5；总计65.7413298。只改变调度，不改算法、种子或闸门。已有AutoDAN前20热身计时不强行中断；该任务退出后按上述就绪顺序，未过执行门的任务不抢卡。
4. 主轮不加SORRY重排序，不因88门结果补救或换候选。论文暂不声称每个模型的搜索攻击都有动态范围；若某格88失败，按实际行集/数值写“该本地角色配置下无动态范围”，不泛指该算法无效。静态家族结果与搜索失败分别报告。
5. n=10独立重放诊断只留日志/时序审计，不进正文或附录结果表，不参与主统计。十个计时行为本身仍留在88/220/440正式行集中；其正式全档重放随全档报告，禁止据小样本删除这些ID。
6. Gemma/Mistral准备不等待整轮结束。优先目标为11/13–11/14第一张获准释放的生成卡：先补Mistral基线和两模型拒答复核/目标包，再训练三seed与统一700校准。所有旧基线、旧val70/388复核与新700校准分别标识。未通过各模型编译/批处理/目标编码/拒答门之前不训练或正式校准；PAIR/TAP等主任务租约仍优先，不修改选择规则。
7. 先补Llama泰米尔语alpha0作为调度例外，但已有中文/法语回复翻译不等它。WG首波释放后CF翻译先行；后续WG波次后尽快补泰米尔原生成。编码和印度其他条件保持低优先。为避免释放收据尚在同步时编码门抢先，所有未启动编码任务显式依赖CF完成；已运行的编码工程门不杀进程，完成后交卡。
8. FigTxt作者load_FigTxt函数没有类别筛选，上游CSV500行/10类、作者README350行/7类的子集来源未解决。按现可执行作者代码使用完整500并标非原设置，不自行猜取前七类，也不套用原设置复现通过措辞。原350条准入线保留，未宣称通过。
''')
plan=U/'search_active_cell_budget_rule16.json'
save(plan,dict(utc_frozen=utc(),doc_sha256=H(doc),replaces='addendum15 inactive-cell projected expansion cost',
 budget_GPUh=600,actual_sunk_cost_all_cells_counted=True,
 expansion_cells='active OR INVALID_crossing_continue; exclude no_dynamic_range future costs',
 prospective_new_88_rows=0,prior_pilot_IDs_retained=True,
 cost_order=[dict(method=m,model=k,cost88=v) for m,k,v in [
 ('PAIR','llama',3.409945704033038),('PAIR','qwen',5.378238473919974),
 ('TAP','llama',21.045335044504132),('TAP','qwen',35.907810611895776)]],
 unknown_costs_never_zero=True,reranking=False,pilot10_diagnostic_tables_in_paper=False,
 preparation_trigger='first admitted generation card released, target Nov13-Nov14; gates unchanged',
 nonzero_effects_read=False))
commit=publish([doc,plan,Path(__file__)],'Freeze active-cell expansion accounting and cost-ordered88 before new search rows')
pub=U/'rule16_publication.json';save(pub,dict(utc=utc(),published=True,commit=commit,plan_sha256=H(plan)))
C=U/'ready_queue_catalog.json';cat=L(C);S=L(U/'ready_queue/state.json')['tasks']
priorities={'PAIR_progressive_llama_gate_v1':14,'PAIR_progressive_llama_88_v1':15,
 'PAIR_progressive_qwen_gate_v1':16,'PAIR_progressive_qwen_88_v1':17}
for t in cat['tasks']:
 if S.get(t['id'],{}).get('state')=='running':continue
 if t['id'] in priorities:
  t['priority']=priorities[t['id']];t['requires'].append(dict(path=str(pub.relative_to(R)),key='published',value=True))
 if t['id'].startswith('encoding_'):
  t['requires'].append(dict(path='results/audit/unified300/language_processed_alpha0_v1/complete_CF.json'))
 if t['id']=='language_llama_translate-ta_B4_generate':t['priority']=9
save(C,cat)
print(json.dumps(dict(commit=commit,doc_sha256=H(doc),plan_sha256=H(plan),new88rows=len(newrows))))
