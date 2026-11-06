# 264 — 两方向与四方向随机参照补充

首次全量效应读取UTC：2026-11-06T14:58:06.323576+00:00。原addendum7保持3/5，未达至少4/5；不补救或重判。

| 方向 | ASR% | 相对α0下降pp |
|---|---|---|
| rand0 | 38.33 | 1.00 |
| rand1 | 35.33 | 4.00 |
| rand2 | 39.67 | -0.33 |
| rand3 | 40.33 | -1.00 |

| 参照方向数 | 随机ASR均值% | 方向样本SD pp | 平均降幅pp | 五learned平均优势pp | seed样本SD pp | 条件seed t95 pp |
|---|---|---|---|---|---|---|
| 2 | 36.83 | 2.12 | 2.50 | 12.30 | 3.53 | [7.91,16.69] |
| 4 | 38.42 | 2.22 | 0.92 | 13.88 | 3.53 | [9.50,18.27] |

| learned seed | vs rand0 pp | vs rand1 pp | vs rand2 pp | vs rand3 pp |
|---|---|---|---|---|
| s3 | 19.00 | 16.00 | 20.33 | 21.00 |
| s4 | 11.33 | 8.33 | 12.67 | 13.33 |
| s5 | 10.33 | 7.33 | 11.67 | 12.33 |
| s6 | 15.67 | 12.67 | 17.00 | 17.67 |
| s7 | 12.67 | 9.67 | 14.00 | 14.67 |

Both t and paired intervals condition on observed fixed random directions; four directions still provide limited direction uncertainty. No replacement of original#7 decision.

| 来源 | sha256 |
|---|---|
| results/audit/handoff_round6/random_references_complete_results.json | b7657859b858e3c8ef7feb49f01b61ee8e0b4370e07b3ec84422d4db54db6750 |
| results/hfjudge/JUDGE_HF_wjb_rand0_innet_round2 | 2d67f022648695b29620a8c6bdb516f73ae2d6c866c5a56b977bec0e4780f50f |
| results/hfjudge/JUDGE_HF_wjb_rand1_innet | 86e0107d59f907106c0b73f20c06fef301098ecd7e94c6936f64a793d5ddde3c |
| results/hfjudge/JUDGE_HF_wjb_rand2_innet_round6 | 9fe1a35605bb0c6da96fb24ce0341c73ed2855cdd996217e92b6b5900682a13b |
| results/hfjudge/JUDGE_HF_wjb_rand3_innet_round6 | 76c79ecfc9324095103cddab99f6fd025859928809af2aa4db452ab741d4aea9 |
