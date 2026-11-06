# 246 追加：近邻审计与第二个随机方向（任何配对生成之前）

原文件保持不变，原 sha256=44629af52476026ee94ae4b3faf38e522fb259ba4b19186b94c82f5096ed81b0。
固定条件：alpha0、old s0 alpha=1、rand0、rand1；同一份 300 对清单，同节点 innet，同顺序，单条生成（batch size=1），每侧 120 token，统一 generate_with_injection。
随机方向：np.random.default_rng(0/1) 各自生成 4096 维高斯后归一到 5.21；方向间分别报告，不合并成一个随机点。
数值判据不变：learned 双重差 >=3pp 且 95% 区间排除 0；随机方向双重差在 +/-3pp 内。对 rand0、rand1 分别应用原判据并并列报告；不因新增方向改阈值或筛选方向。
分析集：alpha0 对两侧均回答的配对；固定规则 v2；按 vanilla 聚类 bootstrap 2000 次（seed=20261106）。v3/V_b 仅作并列敏感性，不替换主口径。
抽样 seed=20261106，按固定随机顺序取最先通过排除与近邻检查的 300 个不同 vanilla；比较 val296 双侧、keep60、train_strat 全部文本，并排除清单内部 >=0.85 近邻。
清单：configs/stage0_data/wjb_benign246_pairs300.json；sha256=1166dec3ee8a9b6946e2004e4e013b8254b1af270c231f4d4598a00d1ee303f1。
审计：results/audit/handoff_20261106/doc246_nearest_neighbor_audit.json；sha256=1e4c73de31204ad0d5193f888d03d3c72eedcda77bea1af6adea1a61c244bf0f。
模型为缓存 all-MiniLM-L6-v2；max_seq_length=256，长文本会被截断，不能把通过阈值解释为完整语义互斥。
