# 尾部资源与contextual路径核对

状态UTC 2026-11-09T06:11:13.883860+00:00；JST 2026-11-09T15:11:13.883860+09:00。只读进度、长度和运行元数据，不读判分标签。

公开侧总数1979 = 良性1779（XSTest safe250、OR-Bench-Hard1319、WJB良性210）+ XSTest unsafe200。unsafe已包含在1979内，以下拆列。

| 条件 | WJB有害/2000 | XSTest safe/250 | OR-Hard/1319 | WJB良性/210 | unsafe/200 | 公开总计/1979 |
|---|---:|---:|---:|---:|---:|---:|
| old_s0 | 249 | 250 | 1319 | 210 | 200 | 1979 |
| SYS_A | 0 | 128 | 0 | 0 | 8 | 136 |
| SYS_B | 0 | 0 | 0 | 0 | 0 | 0 |

## 实测速率与ETA

| 条件/侧 | 已计时新行 | 含启动秒/行 | v2阶段秒/行 | 剩余卡时（当前速率） | 短期日历ETA |
|---|---:|---:|---:|---:|---|
| old_s0/harmful | 249 | 8.436 | 8.433 | 4.102 | 11/09 17:54:36 JST |
| old_s0/public | 1979 | 0.539 | 0.522 | 0.000 | 已齐全 |
| SYS_A/harmful | 0 | 未启动/无实测 | 未启动/无实测 | 未启动/无实测 | 待首批实测 |
| SYS_A/public | 136 | 0.878 | 0.878 | 0.450 | 11/09 15:38:18 JST |
| SYS_B/harmful | 0 | 未启动/无实测 | 未启动/无实测 | 未启动/无实测 | 待首批实测 |
| SYS_B/public | 0 | 未启动/无实测 | 未启动/无实测 | 未启动/无实测 | 待首批实测 |

“卡时”只计算生成服务；日历ETA按已观测的调度/让位速率外推，初始样本小且未来条件的输出长度不同。不能把s0速度当A/B实测。未启动条件不报精确完成钟点；此前三条件12–13卡时仍是预算估计。PAIR生成/最终判分优先，辅助尾部不成为PAIR读取前置条件；18:00 GPU0让卡不变。

此前辅助缺口可独立触发双卡窗口，影响尾部推进。追加#11先冻结并push，v2于2026-11-09T05:56:46.179680+00:00接管；26385个已有生成文件哈希未变。现在只有PAIR待判缓存达到256行或实际搜索结束才启动必要窗口；辅助缓存只复用剩余驻留时间/排在PAIR之后。

当前租约：[{"kind": "tail", "cards": ["0"], "tail_kind": "harmful", "condition": "old_s0", "shard": 0, "launcher_pid": 1901112}, {"kind": "tail", "cards": ["2"], "tail_kind": "harmful", "condition": "old_s0", "shard": 1, "launcher_pid": 1902106}, {"kind": "tail", "cards": ["3"], "tail_kind": "public", "condition": "SYS_A", "shard": 0, "launcher_pid": 1906109}]

## systemA/B元数据口径

新记录保存new_tokens、实际EOS观察、系统文本SHA、input_ids SHA、rho_runtime以及nonzero_vector_injection_count。公开批量路径对无向量记录injection_count=0、prefill_hook_count=1；单条统一函数的原generation.injection_count表示钩子调用，零向量也为1，保留该原值，并用nonzero_vector_injection_count=0明确没有非零注入。新wrapper不改变原数值调用，也不追填旧记录。

## contextual路径

核对UTC 2026-11-09T05:51:53.260784+00:00：原始contextual100行均检查源长度；当前已生成1144个正式模板输入，长度413–1962，>1900为23，>2048为0，实际分块0。这是当前前缀的长度覆盖，不是最终全量。

旧night/judge_all.py的>1900分块使用旧CLS_PROMPT，不在PAIR的official contextual调用链中。当前增量和最终HF路径明确拼入原context、行为和冻结512-token输出截段，超过2048则停，不静默截断或改为旧分块。全条件生成完成后重新做长度审计。WildGuard的>4096按另一模型模板另报，不混同。

copyright只报MinHash命中和拒答，主表不与standard/contextual/JBB平均为ASR；HB400保留为数据集库存n。

## 完成时间

PAIR搜索当前439/500，382.07秒/行。搜索实际结束记录：未产生（搜索仍在运行）；PAIR全条件尾部生成齐全记录：未产生。
CPU观察器仅写实际事件UTC/文件覆盖，不读取结果；未产生的时间保持空值，不用ETA替代。

状态JSON SHA256 66df6de8983cf889a04a3a6e7e4b64b8c9648003af05a635c9442135738f7aee。
contextual核对JSON SHA256 35f3bbd2c08640223f95d82d860e62e03542dead5ac9b0fb24b95b523d92b440。

systemA首批实测元数据（仅此样本，不外推未运行B/有害侧）：{"utc": "2026-11-09T06:10:46.016136+00:00", "SYS_A_public_rows": 96, "injection_count_values": [0], "prefill_hook_count_values": [1], "nonzero_vector_injection_count_values": [0], "rho_values": [0.0], "system_hash_values": ["d33c70fdd0c40dc6d2b38a6be972bb8806bd5ac174db361930bb85341be974c3"], "new_tokens_eos_present": true, "only_system_differs_asserted": true}
首批元数据QA SHA256 499cf2fd87a27ca12b499a2fae4b774049d2e9c24ee49cee707a6b556a78c37b。
