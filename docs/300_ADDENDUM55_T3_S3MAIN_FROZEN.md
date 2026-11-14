# 追加55：Table 3 改 s3 为主，脚本冻结

冻结时刻：Z 2026-11-14T15:22:02.928224+00:00；PST 2026-11-14T07:22:02.928224-08:00（执行方实读 date -u）。
**脚本在运行、查看任何 s3-main 成本 Δ 之前冻结。**

## 脚本
`tools/handoff_20261106/u300_T3_s3main_54.py`，sha256 `64cbf2027d07f65b96580b7024c0a76f4f465a078d8b29a8c3334bfaec5f39d1`。

## 冻结约定
1. **learned = s3 单条**；random = rand0（Llama）/ 61000（Qwen）。
2. 去掉 30 条 keep 重叠：or_hard:120–127、130–139（18）；xstest_safe:221–225、251–257（12）。
3. 拒绝标签 = `labels["Response refusal"]=="yes"`；逐行来自 `cost_WG/<model>/<cond>/<set>.json`。
4. 2000 次 prompt 聚类自助，seed 20261214，95% percentile。
5. 另给 s3/s4/s5 分列（OR-Bench-Hard 与池化 5 集），三 seed 平均只作敏感性。
6. 随机参照：rand0/rand1/61000/61001 在 OR-Bench-Hard 上的（random − none）。
7. XSTest unsafe（200）同口径重算。
8. 旧表（cost_read_draft / cost intervals）此前口径不一致，本脚本输出为主表，旧表整套作废。
