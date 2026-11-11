# 静态/变换预算实测更新

| 模型 | 家族 | 正常完成 | α0行/小时 | α0生成卡时 |
|---|---|---|---:|---:|
| llama | base | 是 | 1221.32 | 0.360 |
| llama | deepinception | 是 | 367.44 | 1.197 |
| llama | refusal_suppression | 是 | 1107.26 | 0.397 |
| llama | logical_appeal | 是 | 990.64 | 0.444 |
| llama | authority_endorsement | 是 | 1059.23 | 0.415 |
| llama | misrepresentation | 是 | 943.97 | 0.466 |
| llama | evidence-based_persuasion | 是 | 1063.09 | 0.414 |
| llama | expert_endorsement | 是 | 1038.49 | 0.424 |
| llama | prefix_P1 | 是 | 932.59 | 0.472 |
| llama | prefix_P2 | 是 | 931.82 | 0.472 |
| llama | translate-ml | 否 | 未测/资源失败 | — |
| llama | translate-ta | 否 | 未测/资源失败 | — |
| llama | translate-mr | 否 | 未测/资源失败 | — |
| llama | translate-zh-cn | 否 | 未测/资源失败 | — |
| llama | translate-fr | 否 | 未测/资源失败 | — |
| llama | ascii | 否 | 未测/资源失败 | — |
| llama | caesar | 否 | 未测/资源失败 | — |
| llama | morse | 否 | 未测/资源失败 | — |
| llama | atbash | 否 | 未测/资源失败 | — |
| qwen | base | 是 | 1031.67 | 0.426 |
| qwen | deepinception | 是 | 302.97 | 1.452 |
| qwen | refusal_suppression | 是 | 1329.37 | 0.331 |
| qwen | logical_appeal | 是 | 716.22 | 0.614 |
| qwen | authority_endorsement | 是 | 724.28 | 0.607 |
| qwen | misrepresentation | 是 | 660.28 | 0.666 |
| qwen | evidence-based_persuasion | 是 | 701.50 | 0.627 |
| qwen | expert_endorsement | 是 | 712.92 | 0.617 |
| qwen | prefix_P1 | 是 | 815.07 | 0.540 |
| qwen | prefix_P2 | 是 | 812.42 | 0.542 |
| qwen | translate-ml | 是 | 235.44 | 1.869 |
| qwen | translate-ta | 否 | 未测/资源失败 | — |
| qwen | translate-mr | 否 | 未测/资源失败 | — |
| qwen | translate-zh-cn | 否 | 未测/资源失败 | — |
| qwen | translate-fr | 否 | 未测/资源失败 | — |
| qwen | ascii | 否 | 未测/资源失败 | — |
| qwen | caesar | 否 | 未测/资源失败 | — |
| qwen | morse | 否 | 未测/资源失败 | — |
| qwen | atbash | 否 | 未测/资源失败 | — |

已正常完成的20个英语单元：α0生成11.486卡时；含每家族门检墙钟11.986卡时。五非零若与各自α0同速，另需57.431卡时；合计69.417卡时，未含模型加载/评分。
语言/编码未全部测齐，整轮19家族不填一个伪精确总数。Llama ml虽保存440条，但2.0995GiB资源门失败，不把它当作已验收的运行速度。此预算是同速情景，不是上界；无需因预算预先跳过条件。
