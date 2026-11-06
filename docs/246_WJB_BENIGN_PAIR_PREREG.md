# 246 — WJB adversarial_benign 配对上的风格效应（生成前预注册）

## 目的
C2 的风格效应目前只在 val 的 296 条配对上一个样本。用 WJB 的 adversarial_benign 新建独立配对，检验是否复现。

## 数据
- 源：WildJailbreak `adversarial_benign`，每行含 vanilla 与 adversarial 两列；
- 排除：val 的 296 条、keep60、train_strat；
- 抽样 300 对（seed 与清单哈希写入 PREREG_LOG）。

## 条件（3 个）
α=0、old s0 α=1.0、rand0（同范数 5.21 随机方向）。

## 生成
单条或批量一致；120 token；同节点；同清单；`generate_with_injection`；记录 injection_count/rho。

## 判据（写死）
- 主量：双重差 = 包装侧新增拒答率 − vanilla 侧新增拒答率（按 vanilla 聚类 bootstrap）；
- old s0 的双重差 ≥3pp 且 95% 区间排除 0，**且** rand0 的双重差在 ±3pp 内 → "在 WJB 配对上也观察到风格效应"；
- 否则写成"仅在 val 配对上观察到"。

## 备注
若时间不足，300 对可降为 150 对，但须在读取任何输出前决定并记录。
EOF