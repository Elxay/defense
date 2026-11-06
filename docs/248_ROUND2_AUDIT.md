# 第二轮口径审计（post-hoc）

粗筛实际遍历每条件全部400条，不是仅规则阴性；0个纯拒答来自首次分类中把替代提议归RA，不是排除规则阳性的构造。不得把RA列整体加到规则新增数上。

逐条表不含输入/输出文本；固定391/392基线集，未复核项保留规则状态，U不强判。两列是操作性结果区间，不是统计置信区间或真值上下界。盲读为同一模型第二次呈现，条件/既有标签隐藏，但历史上下文未擦除；29/30一致不构成人工校准。

| 分析文件 | 当前重建采用基线 | 历史使用是否证实 |
|---|---|---|
| results/audit/LEGALVALB_ASYS_a0.5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_ASYS_a1.0.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_B1A_k1_v3e_s100.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_B1A_k1_v3e_s200.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_B1A_k1_v3e_s40.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_QWEN_A_append.json | results/audit/LEGALVALB_qwen_a0.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_QWEN_A_replace.json | results/audit/LEGALVALB_qwen_a0.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_QWEN_B_append.json | results/audit/LEGALVALB_qwen_a0.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_QWEN_B_replace.json | results/audit/LEGALVALB_qwen_a0.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_SYS_A.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_SYS_B.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s0.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s1.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s2.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s3.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s3_a0.25.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s3_a0.5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s3_a0.75.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s4.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s4_a0.25.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s4_a0.5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s4_a0.75.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s5_a0.5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s5_a0.75.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s6.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s6_a0.5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s6_a0.75.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s7.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s7_a0.25.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s7_a0.5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_newseed_s7_a0.75.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_none.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_a0.25.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_a0.5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_a0.75.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_a1.0.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_a1.25.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_a1.5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_a1.75.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_a2.0.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_s0.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_s1.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_old_s2.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_oldseed_s1.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_oldseed_s2.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_oldseed_s3.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_oldseed_s4.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_oldseed_s5.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_oldseed_s6.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_oldseed_s7.json | results/audit/LEGALVALB_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVALB_qwen_a0.json | results/audit/LEGALVALB_qwen_a0.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_none.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_old.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_old_a05.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_old_a05_scaled.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_old_s0.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_old_s1.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_old_s2.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_oldseed_s0.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_oldseed_s1.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |
| results/audit/LEGALVAL_oldseed_s2.json | results/audit/LEGALVAL_none.json | 未逐文件证实历史调用；当前按生成文件族重建 |

已证实的历史混用仅为上一轮旧曲线：单条 LEGALVAL_none 配批量 LEGALVALB_old_a*。不能据文件命名断言其他家族历史上也混过。当前重建新seed、A/B、B1a、随机方向统一使用对应模型批量基线。

联合抽样与边界限制详见 results/audit/handoff_round2/joint_d.json。10000次，4764次至少一个点超出随机参考曲线范围。条件区间不是无条件置信保证；端点截平仅作诊断。

cosine前五对逐条检查：前四对明显任务重叠，第五对人物主题重叠但时间范围不同。原300主集保持冻结；全部四条件出齐后一次性读数，追加排除前五对敏感性，首次读取时间记录PREREG_LOG。通过0.85不能称语义独立。

## 自动生成计数（固定分母，非真值界限）

| 条件 | 分母 | v2新增 | 规则加复核新增 | 边界配对 |
|---|---:|---:|---:|---:|
| A_replace | 392 | 2 | 1 | 1 |
| A_replace | 391 | 2 | 1 | 1 |
| A_append | 392 | 4 | 1 | 2 |
| A_append | 391 | 4 | 1 | 2 |
| B_replace | 392 | 2 | 7 | 1 |
| B_replace | 391 | 2 | 7 | 1 |
| B_append | 392 | 3 | 4 | 3 |
| B_append | 391 | 3 | 4 | 3 |

联合重抽：{"replicates": 10000, "outside_draws": 4764, "joint_fixed5_conditional_interpolable": {"n": 5236, "95_percentile": [-0.9453009941089837, 3.555197594501718]}, "joint_seed_cluster_conditional_interpolable": {"n": 5236, "95_percentile": [-1.3378283014236625, 3.875561091106397]}, "boundary_clipped_diagnostic_only": {"n": 10000, "95_percentile": [-2.1217330242781274, 3.5732817869415805]}, "warning": "Conditional intervals exclude non-interpolable draws and may under-cover; clipped version substitutes endpoints and is diagnostic, not primary inference.", "mean_p_s6_single_point_added": {"cluster_means": [0.18785213607275209, 2.1955617003864125, 2.417806176950679, 0.10528776007325602, -0.33051451689752875], "mean": 0.9151986513171142, "t95": [-0.6838443818604902, 2.514241684494719]}}

同机HF对照：[{"condition": "alpha0", "file": "results/hfjudge/JUDGE_HF_wjb_a0_innet_round2", "sha256": "6968176203df23e74d0681a63ce12dd9187e8c81a13f4c2092f296a4eb675dc2", "harmful": 118, "n": 300, "invalid": 0, "host": "innet", "gate_mid_count": 20, "gate_weak": false}, {"condition": "old_s0", "file": "results/hfjudge/JUDGE_HF_wjb_old_s0", "sha256": "a28fb40e13b9971c2726c040c3f41e0eee7212f06fb511f3fa35fc933a8efb7f", "harmful": 77, "n": 300, "invalid": 0, "host": "innet", "gate_mid_count": null, "gate_weak": null}, {"condition": "rand0", "file": "results/hfjudge/JUDGE_HF_wjb_rand0_innet_round2", "sha256": "2d67f022648695b29620a8c6bdb516f73ae2d6c866c5a56b977bec0e4780f50f", "harmful": 115, "n": 300, "invalid": 0, "host": "innet", "gate_mid_count": 20, "gate_weak": false}]

WJB输出判官尚未在该分布校准。old翻转拒答44/58=75.9%、rand0 10/22=45.5%为规则检出比例；召回不足时是拒答占比的描述性下界。val70既有随机/init翻转中为24/93=25.8%，集合构成不同。删除此前“alpha0对应为0”的解释。WJB rand0降1pp、old0降13.7pp；val70高斯随机方向均值降15.2pp（11方向合并降12.9pp），old0降70.0pp。只能作跨集合描述，不将成功筛选解释为已证实机制；待rand1再讨论方向间稳定性。

## 粗筛RA与既有规则重叠

{
  "baseline": {
    "coarse_RA": 2,
    "v2_already_caught": 2,
    "v2_missed": 0
  },
  "A_replace": {
    "coarse_RA": 5,
    "v2_already_caught": 4,
    "v2_missed": 1
  },
  "A_append": {
    "coarse_RA": 5,
    "v2_already_caught": 4,
    "v2_missed": 1
  },
  "B_replace": {
    "coarse_RA": 13,
    "v2_already_caught": 7,
    "v2_missed": 6
  },
  "B_append": {
    "coarse_RA": 8,
    "v2_already_caught": 5,
    "v2_missed": 3
  }
}
不能把RA总数视为FN；B_replace 13条中7条v2已捕获，新增漏判6条。基线RA2条均已由v2捕获。

391/392口径完整计数：
[{"condition": "A_replace", "fixed_denominator": 392, "baseline_set": "v2", "rule_v2_new": 2, "rule_plus_review_new": 1, "ambiguous_pairs": 1, "rule_v2_union_v3_new": 3}, {"condition": "A_replace", "fixed_denominator": 391, "baseline_set": "v2_union_v3", "rule_v2_new": 2, "rule_plus_review_new": 1, "ambiguous_pairs": 1, "rule_v2_union_v3_new": 3}, {"condition": "A_append", "fixed_denominator": 392, "baseline_set": "v2", "rule_v2_new": 4, "rule_plus_review_new": 1, "ambiguous_pairs": 2, "rule_v2_union_v3_new": 4}, {"condition": "A_append", "fixed_denominator": 391, "baseline_set": "v2_union_v3", "rule_v2_new": 4, "rule_plus_review_new": 1, "ambiguous_pairs": 2, "rule_v2_union_v3_new": 4}, {"condition": "B_replace", "fixed_denominator": 392, "baseline_set": "v2", "rule_v2_new": 2, "rule_plus_review_new": 7, "ambiguous_pairs": 1, "rule_v2_union_v3_new": 5}, {"condition": "B_replace", "fixed_denominator": 391, "baseline_set": "v2_union_v3", "rule_v2_new": 2, "rule_plus_review_new": 7, "ambiguous_pairs": 1, "rule_v2_union_v3_new": 5}, {"condition": "B_append", "fixed_denominator": 392, "baseline_set": "v2", "rule_v2_new": 3, "rule_plus_review_new": 4, "ambiguous_pairs": 3, "rule_v2_union_v3_new": 6}, {"condition": "B_append", "fixed_denominator": 391, "baseline_set": "v2_union_v3", "rule_v2_new": 3, "rule_plus_review_new": 4, "ambiguous_pairs": 3, "rule_v2_union_v3_new": 5}]

同机补判全量跨机核对：
[
  {
    "condition": "alpha0",
    "label_flips": 0,
    "max_abs_delta": 0.0
  },
  {
    "condition": "rand0",
    "label_flips": 0,
    "max_abs_delta": 0.0
  }
]
