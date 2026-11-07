# 281 — 实时队列状态

快照JST：2026-11-07 11:23:31；每30秒刷新根工作区，Git报告是发布时快照。训练完成行的旧心跳年龄不表示作业卡死；pending为等待租约或前置步骤。

| 作业 | 节点/GPU | PID | 阶段 | 进度 | 秒/单位 | 心跳年龄s |
|---|---|---|---|---|---|---|
| original_twoarm | innet/CPU | 2224284 | generating_full |  |  | 2.4 |
| plain_five | innet/CPU | 2312701 | plain_training |  |  | 8.1 |
| noise_B | innet/CPU | 2320871 | waiting_node_noise_B |  |  | 21.2 |
| plain_s3_train | innet/2 | 2303730 | vector_complete | 40/40 |  | 1156.7 |
| plain_s4_train | innet/3 | 2337518 | training | 1/40 | 14.711916674859822 | 9.5 |
| plain_s5_train | innet/2 | 2326757 | training | 39/40 | 14.372875030104739 | 5.6 |
| plain_s6_train | innet/3 | pending | waiting_gpu_lease_or_prior_queue | 0/40 |  | pending |
| plain_s7_train | innet/2 | 2315132 | vector_complete | 40/40 |  | 576.2 |
| noise_B_launcher | node01/0 | 1845463 | waiting_original_GPU0_lease | 0 |  | 3.0 |
| plain_s3_grid | node01/0 | pending | not_started_waiting_all_vectors_and_original_window | 0/2820 |  | pending |
| plain_s3_holdout | node01/0 | pending | not_started_before_endpoint_plan_hash | endpoint_count_pending |  | pending |
| plain_s4_grid | node01/1 | pending | not_started_waiting_all_vectors_and_original_window | 0/2820 |  | pending |
| plain_s4_holdout | node01/1 | pending | not_started_before_endpoint_plan_hash | endpoint_count_pending |  | pending |
| plain_s5_grid | node01/2 | pending | not_started_waiting_all_vectors_and_original_window | 0/2820 |  | pending |
| plain_s5_holdout | node01/2 | pending | not_started_before_endpoint_plan_hash | endpoint_count_pending |  | pending |
| plain_s6_grid | innet/2 | pending | not_started_waiting_all_vectors_and_original_window | 0/2820 |  | pending |
| plain_s6_holdout | innet/2 | pending | not_started_before_endpoint_plan_hash | endpoint_count_pending |  | pending |
| plain_s7_grid | innet/3 | pending | not_started_waiting_all_vectors_and_original_window | 0/2820 |  | pending |
| plain_s7_holdout | innet/3 | pending | not_started_before_endpoint_plan_hash | endpoint_count_pending |  | pending |

网格0/2820为6×(70攻击+400合法)，评估合法分母仍是388；留出端点数量在方案冻结前不假定为1。所有GPU任务原门禁>2000MiB拒绝，innetGPU0/1禁用。
