# 追加45：外部人工集来源更正（SORRY-Bench）、SORRY 非独立、第三类图

写入Z：2026-11-14T11:09:41.031006+00:00；PST：2026-11-14T03:09:41.031006-08:00（执行方实读 date -u）。

## 来源更正
arXiv 2406.14598 = **SORRY-Bench**，不是 WildGuard。`human_refusal_diagnostics.json`（sha `13b42d09…`）的 4,400 行人工标签 = **SORRY-Bench 202503 test 人工评判集**（论文 ICLR 版；train 2640 / test 4400）。此前 D1 与对账表写"WildGuard 论文"一律更正为"SORRY-Bench 人工评判集"。

## SORRY 评判非独立（从全文核实）
- SORRY = `sorry-bench/ft-mistral-7b-instruct-v0.2-sorry-bench-202406`（Mistral-v0.2 在 SORRY-Bench **202406 train** 上微调）。
- 人工标签 = 202503 test（4400）。
- `split_audit`：202503 test 与 202406 train **共享全部 440 条指令文本**（`shared_instruction_texts: 440`）。
- 故 SORRY 的 ID κ（0.9001）与 overall κ（0.8082）**标注"非独立"**：判官训练见过同一批指令。

## D1 局限（追加写入）
- 所有 κ 都是对**外部人工集**（SORRY-Bench 202503 test），**不是对我们转向后的输出**。
- OOD 上：SORRY 0.7284、HB 0.5723、WG 0.3751（WG=1−refusal）——**只有 SORRY 过 0.60**，且 SORRY 非独立。
- 因此"合格"改称"**外部 ID 人工集上合格**"；对我们自己输出的 20 格，**均未验证**。

## 第三类图（外部数据，已核对行列约定）
`human_refusal_diagnostics.json` 的混淆为 `confusion_human0_1_by_model0_1`：行=human 0/1，列=model 0/1；h0=非完成（安全）、h1=完成（不安全），m1=WG 非拒绝（不安全）。"人工判未完成但 WG 判非拒绝" = **h0m1**：

| 子集 | n(valid) | h0m1 | 占比 |
|---|---|---|---|
| ID(base) | 2200 | 77 | **3.50%** |
| OOD | 2196 | 738 | **33.61%** |

（h1m1 = ID 519=23.59%、OOD 739=33.65%，是"人工判完成且 WG 非拒绝"，与上面不是同一格。）

## B7 估计（待核）
升级规则涉及的格 = base + 4 个未验证家族（deepinception/P1/P2/refusal_suppression），且须覆盖**我们自己的输出**。κ 95% 区间半宽 ≤0.1 所需 n 的估计：待交（不扩大 n）。

## 原样提交 git
`287_ADDENDUM1_DONOR_HIDDEN_INDEX.md`（sha 339d7d0e…）、`287_ADDENDUM2_ALPHA_LEGAL_BUDGET_AND_NORM.md`（sha 6c568660…）、`tools/handoff_20261106/r1_intervals.py`（sha deacad55f…）、`docs/300_ADDENDUM26_R1_FAMILY_RULES.md`（sha 3256ef25…）随本追加原样提交。
