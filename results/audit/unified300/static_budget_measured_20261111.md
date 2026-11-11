# 各家族α=0实测吞吐与预算

更新UTC：2026-11-11T05:06:51.385863+00:00

20个英语单元全部活跃：α=0净生成11.4862卡时，含原门检墙钟11.9862；五个非零同速假设57.4309，六条件合计69.4171卡时。不是上界，加载、判分和其它家族另计。

正常完成且有实测的24个单元，α=0净生成累计16.2114卡时。语言闸门尚未读取，不假定它们全部活跃，不外推尚无数据的编码家族。

| 模型 | 家族 | 正常完成 | 行/小时 | α=0净生成卡时 | 闸门 |
|---|---|---|---:|---:|---|
| llama | base | 是 | 1221.32 | 0.3603 | active |
| llama | deepinception | 是 | 367.44 | 1.1975 | active |
| llama | refusal_suppression | 是 | 1107.26 | 0.3974 | active |
| llama | logical_appeal | 是 | 990.64 | 0.4442 | active |
| llama | authority_endorsement | 是 | 1059.23 | 0.4154 | active |
| llama | misrepresentation | 是 | 943.97 | 0.4661 | active |
| llama | evidence-based_persuasion | 是 | 1063.09 | 0.4139 | active |
| llama | expert_endorsement | 是 | 1038.49 | 0.4237 | active |
| llama | prefix_P1 | 是 | 932.59 | 0.4718 | active |
| llama | prefix_P2 | 是 | 931.82 | 0.4722 | active |
| llama | translate-ml | 否/待完成 | — | — | not read/unavailable |
| llama | translate-ta | 否/待完成 | — | — | not read/unavailable |
| llama | translate-mr | 否/待完成 | — | — | not read/unavailable |
| llama | translate-zh-cn | 是 | 1171.87 | 0.3755 | not_read |
| llama | translate-fr | 是 | 577.00 | 0.7626 | not_read |
| llama | ascii | 否/待完成 | — | — | not read/unavailable |
| llama | caesar | 否/待完成 | — | — | not read/unavailable |
| llama | morse | 否/待完成 | — | — | not read/unavailable |
| llama | atbash | 否/待完成 | — | — | not read/unavailable |
| qwen | base | 是 | 1031.67 | 0.4265 | active |
| qwen | deepinception | 是 | 302.97 | 1.4523 | active |
| qwen | refusal_suppression | 是 | 1329.37 | 0.3310 | active |
| qwen | logical_appeal | 是 | 716.22 | 0.6143 | active |
| qwen | authority_endorsement | 是 | 724.28 | 0.6075 | active |
| qwen | misrepresentation | 是 | 660.28 | 0.6664 | active |
| qwen | evidence-based_persuasion | 是 | 701.50 | 0.6272 | active |
| qwen | expert_endorsement | 是 | 712.92 | 0.6172 | active |
| qwen | prefix_P1 | 是 | 815.07 | 0.5398 | active |
| qwen | prefix_P2 | 是 | 812.42 | 0.5416 | active |
| qwen | translate-ml | 是 | 235.44 | 1.8689 | not read/unavailable |
| qwen | translate-ta | 是 | 256.06 | 1.7183 | not_read |
| qwen | translate-mr | 否/待完成 | — | — | not read/unavailable |
| qwen | translate-zh-cn | 否/待完成 | — | — | not read/unavailable |
| qwen | translate-fr | 否/待完成 | — | — | not read/unavailable |
| qwen | ascii | 否/待完成 | — | — | not read/unavailable |
| qwen | caesar | 否/待完成 | — | — | not read/unavailable |
| qwen | morse | 否/待完成 | — | — | not read/unavailable |
| qwen | atbash | 否/待完成 | — | — | not read/unavailable |

Llama translate-ml即使440行已保存，3GiB资源断言失败，不纳入正常完成吞吐。新α/条件会改变输出长度；以上是测得路径的净生成速度。
