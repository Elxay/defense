# 租约调度部署与实测状态

记录UTC 2026-11-09T05:06:07.367275+00:00；JST 2026-11-09T14:06:07.367275+09:00。本报告只采集进度与生成耗时，不读取PAIR500的新有害标签或条件效应。

追加#9先冻结并push，之后发布实现哈希，最后在04:17:42.581765 UTC完成控制器交接。旧480行控制器已停；4763个交接前生成文件哈希未变。PAIR租约优先，低优先级单条生成在行边界、公开侧在原batch8边界让出。GPU0仍在18:00 JST让卡，GPU1不属于本项目。

当前主调度PID 1735804，phase=lease_priority_running，心跳年龄1.0秒。
当前租约（launcher_PID为启动进程，非模型worker PID）：[{"kind": "hb", "cards": ["2", "3"], "launcher_pid": 1804140}, {"kind": "prefix", "cards": ["0"], "condition": "old_s6", "launcher_pid": 1811613}]
PAIR搜索429/500，worker PID 2295103，历史OOM重启计数1。累计381.67秒/行；不计未来中断的累计速率ETA UTC 2026-11-09T12:37:46.180637+00:00。

首次实测积压清空：UTC 2026-11-09T05:00:34.355146+00:00，该时点已接纳428行，13条件覆盖均相同。其后搜索继续新增行，所以清空不是搜索完成，也不代表后续永无积压。
清空记录SHA256 bd7f715879e890b50c3019c43e8f8b361c2b40f3a984c946834efaa930f2cc43。

| 条件 | 前缀已生成行数 | 实测完成批次数 | 行数 | 净生成秒/行 | 含启动墙钟秒/行 | 含启动行/小时 |
|---|---:|---:|---:|---:|---:|---:|
| alpha0 | 429 | 30 | 33 | 19.907 | 31.661 | 113.7 |
| old_s3 | 428 | 7 | 199 | 7.195 | 7.534 | 477.8 |
| rand0 | 428 | 6 | 249 | 16.248 | 16.505 | 218.1 |
| old_s4 | 428 | 7 | 299 | 8.731 | 8.995 | 400.2 |
| rand1 | 428 | 5 | 250 | 16.512 | 16.727 | 215.2 |
| old_s5 | 429 | 5 | 250 | 9.682 | 9.920 | 362.9 |
| rand2 | 429 | 5 | 250 | 16.625 | 16.819 | 214.0 |
| old_s6 | 428 | 4 | 200 | 7.849 | 8.045 | 447.5 |
| rand3 | 428 | 5 | 250 | 16.344 | 16.555 | 217.5 |
| old_s7 | 428 | 5 | 250 | 10.125 | 10.317 | 349.0 |
| old_s0 | 428 | 5 | 230 | 8.253 | 8.501 | 423.5 |
| SYS_A | 428 | 5 | 250 | 7.706 | 7.890 | 456.3 |
| SYS_B | 428 | 4 | 200 | 4.399 | 4.665 | 771.7 |

实测速率来源是已完成任务，不是整集合外推；alpha0含很多单行重载，不能与50行任务直接比较。加载时间中位数约8.3–8.6秒，墙钟口径还包含写盘。不同条件输出长短与批次组成不同，不将这些差异解释成硬件效应。

## 首个增量判官窗口

窗口PID 1804163：{"started": {"utc": "2026-11-09T05:00:53.119400+00:00", "stage": "verifying_model_files"}, "started_sha256": "e873f9bcec838f50f6ad25f83b32c82cfd791edef11e2e84ae4b83fe6b5d03b4", "ready": {"utc": "2026-11-09T05:05:05.562596+00:00", "fresh_model_hash_check": true, "reference20_passed": true}, "ready_sha256": "46b4b426c017bb52c10353423a71bff445dbfe8e07a665b23ae31cf819814797", "gate": {"max_abs_delta": 0.0, "passed": true, "n": 20}, "gate_sha256": "bf7b49345572e425ee93f24ecb728463e001646a4a9d75c87945f764bab0f769"}
本窗口完整权重校验、加载及20条门合计252.44秒，另计于缓存判分耗时；不把前缀小模型的约8秒启动速度套用到13B判官。

窗口先核验模型文件，再过原20条门，之后只写判分缓存；copyright仍走CPU MinHash。读取锁不变。PAIR缓存优先，余下驻留时间用于已冻结的WJB top2与尾部top1；窗口有界、可续跑。

## 尾部补跑

以下是各卡最近一次尾部观察；process_exists=false表示该段已结束/让出，不能视为仍在占卡。
{"utc": "2026-11-09T05:04:53.531422+00:00", "pid": 1803958, "kind": "harmful", "condition": "old_s0", "shard": 0, "new_rows": 42, "wall_seconds": 249.7001606663689, "effects_read": false, "wall_seconds_per_new_row": 5.945241920627831, "metadata_sha256": "4f2872d539f403a954dc9d3e9fe90557f8607df4d80402e505f44f4f9047f3c6", "process_exists": false, "observation_age_seconds": 73.835853}
{"utc": "2026-11-09T05:00:44.616387+00:00", "pid": 1803281, "kind": "public", "condition": "old_s0", "shard": 0, "new_rows": 24, "wall_seconds": 20.589158524293453, "effects_read": false, "wall_seconds_per_new_row": 0.8578816051788939, "metadata_sha256": "6d5b1c67adabac3726ae7c846b0908536318b00cb53de28f80c58571938a67c1", "process_exists": false, "observation_age_seconds": 322.750888}

Harmful injection metadata is stored at record.generation; public injection metadata at each item. No generation record edited.
{"harmful": {"rows": 10, "injection_metadata_complete": 10, "injection_count_values": [1], "rho_min": 5.210000038146973, "rho_max": 5.210000038146973}, "public": {"rows": 24, "injection_metadata_complete": 24, "injection_count_values": [1], "rho_min": 5.210000038146973, "rho_max": 5.210000038146973}}
元数据核对SHA256 8d74ee04069c0c9f8fce04c4baa068c82839bc19791aec261533308594a8e21f。

各尾部条件old_s0、SYS_A、SYS_B沿原生成函数；公开侧原1979行、batch8、120token，有害侧2000行、单条、2400token。输出侧Guard按同一原模板低优先级填缓存，不聚合读取。WildGuard的WJB尾部队列先停在条件边界，PAIR WildGuard全部完成后再恢复，避免抢node01 GPU0。

快照SHA256：6d731bccc3684075b731d9db1ce0ade6eab52ef2e16c5fe298c3a3b2c736e032。
前缀耗时记录SHA256：314525ce906ea4c67598305f5c9060232ad1665714852517bb988e378a31a2c8。
