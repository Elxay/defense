# 280 — 五seed第三臂、合法后验复核与文稿核对
UTC: 2026-11-07T02:23:11.853048+00:00
状态快照JST: 2026-11-07 11:23:00

追加#4SHA: 95b9605403552e2c7503d5a74f9222c4c2fadf08fa186643fbf18dc5e137f64f
追加#4冻结时已有s3训练；它早于新增s6/s7优化及所有第三臂留出生成/读取，不声称早于全部第三臂训练。
seed3-B已经排队，仍等node01GPU0原作业释放；0/300有害，0/600配对，不称已生成。

合法新增v2=v2并v3=V_b：s3–s7对照[28,16,14,17,18]，包装[21,12,14,10,11]，各分母388。包装alpha=[1.5,1,1.5,1,1]，并非同强度。
每臂规则未拒答抽30（每seed6），完整读已生成窗口，GPT同会话模型标注、未经人工校准，历史上下文未擦除。明确漏判各0；截断/未完成待定对照3、包装5。明确漏判通过线均通过；待定计漏判时包装5/30不通过，不能声称已排除差异召回。

文件与SHA：
- `results/audit/handoff_round11/legal_rule_sensitivity.json` SHA256 `f979a8b4790c1fe920f863de5d0b3b9b9d785b493580d267780b8b48738fbd2d`
- `results/audit/handoff_round11/legal_recall_summary.json` SHA256 `f4affaf24f4f8a27170b78a7f51113ce2cb95058bbf9df516961380ab6f64a58`
- `results/audit/handoff_round11/legal_recall_blind60_review.json` SHA256 `ae90edf850e3c167f3d33ebece26bb483a8add26b80070a33fc8e42d15779e1e`
- `results/audit/handoff_round11/legal_audit_complete_gate.json` SHA256 `6819d77fd6f60a27525c495d0acea68d394fda430d08f8892a9cf8dda07a6d44`
- `results/audit/handoff_round11/three_reruns_provenance.json` SHA256 `580fe72e40358bb46a020853c94cac2c567de798284829e343db4e09495f62e4`
- `results/audit/handoff_round11/guard_seen_first_and_dispersion_limits.json` SHA256 `7df315965e020c8af8abbb6511f5e9bfde82d6334451bb7766690e4fca0fbd1d`
- `results/audit/handoff_round11/handoff_status_frozen.json` SHA256 `d71e36a3e2949cf2842e2427df8de43d2f95903150ad0c288965024f911757ff`
- `paper/CLAIM_EVIDENCE.json` SHA256 `1e4a737c8e4613deb674050fcbb9a5aa347c47b8153f20f702a05488430db49e`
- `paper/BUILD_QA.json` SHA256 `ff57cb80a95a226a72331da583a5592c2c6663ca0d88b3981df6d4af14724591`
- `paper/manuscript.pdf` SHA256 `4bf9b5c33266cd21ff376425261b644e6d7b16b544a5284c6d988314b8ce10e0`

三次现代重训共用缓存/初始化/优化代码，历史冻结向量另列。正文使用同seed与跨seed离散度可比、不分解方差。0.513的假设F诊断区间[0.087,7.500]不作为实际置信区间（样本重叠/非独立）。
论文现7页，包含参考文献与附录；未用满8页正文额度。正文未用preregistered/preregistration。仅版本化日志预先指定，外部时间戳自2026-11-06 00:34JST起，更早仅服务器日志自证。无原始攻击或有害输出示例。Qwen仅零训练基线。六项指定局限均已列出。
摘要、贡献和局限的逐项来源索引见paper/CLAIM_EVIDENCE.json；原文在main.tex及sections/01_introduction.tex、06_limitations.tex。进行中干预不作为完成证据。

## 主张来源（不发布原始输出）
A_random_and_learned
- `paper/data/zero_line.csv` SHA256 `db83822e0cff605f079364ecc6b9b051d65465cb2561ff8b20ab6a90729e164e`
- `stage136/keep60_seed.py` SHA256 `e7dc6b09cd6f2d6b2f5702a0393c0fc812e7762acba0fde5b884fce36ef56106`
B_residual
- `results/audit/handoff_round3/lmi_pairs.json` SHA256 `0e331cb94a13ff1a2186cbfb4c3b75e4c930c40b3894640010f23119f6900b02`
C_benign_replication_and_ranking
- `results/audit/handoff_round8/doc250_descriptive_stats.json` SHA256 `455e18060369ce04a183342fdd6857edba6eb1ffdb5d00ad327ce2298a2bac08`
- `paper/data/c2.csv` SHA256 `f4907f6ffaf6df1cebcbdb229909ff2d8c2dc2b51805af84e116e22dc5c6d4ef`
D_baseline_mismatch
- `results/audit/handoff_20261106/curve_reconciliation.json` SHA256 `353e1e1f25748923cd9679faa5468cae670ec8b7efb496e1bcda5a4a3551678a`
E_truncation
- `results/audit/handoff_round8/doc246_U9_400_review.json` SHA256 `e7ce0d1985c54f233f13537faa8e0433b8ace228ad1a18f98f611e708f4e93c5`
F_classifier_position_threshold
- `docs/257_GUARD_PROTOCOL_REPAIR.md` SHA256 `bd4bbb1d469a9050ce98d5d7be5d50a893885afb9190942f58c67c57bf7d26d9`
- `docs/258_QWEN_GUARD_RESULTS.md` SHA256 `2d48f64664847d4ee9b22c9411a7c52713d2185c553ce9a8af43beb3f70d2ff0`
G_training_repeat
- `paper/data/repeats.csv` SHA256 `e2bccdc1595adf298aaa92045fa8c59dec8acba8dcb564e3de9f62de6ce4eb1e`
- `results/audit/handoff_round9/repeat_comparison.json` SHA256 `98e24bf28cece9fa90d006fe36f53c4b8c01ba4b2cef82557c9b12e693955f6f`
- `results/audit/handoff_round11/three_reruns_provenance.json` SHA256 `580fe72e40358bb46a020853c94cac2c567de798284829e343db4e09495f62e4`
H_scope_and_missing_evaluations
- `docs/236_PAPER_POSITION_v2.md` SHA256 `22d16ef6bbe81099badde3d68496aa48ef9e328b90ec3bc9e15b73e56f5d32b2`
I_no_human_calibration
- `results/audit/handoff_round11/legal_recall_blind60_review.json` SHA256 `ae90edf850e3c167f3d33ebece26bb483a8add26b80070a33fc8e42d15779e1e`
J_same_source_data_and_audit
- `results/audit/handoff_round10/plain_data_audit.json` SHA256 `313de8389dc8c5029d15ff2b5a052de4b3f1b0b04c6577607a65ec30397a7e3c`
