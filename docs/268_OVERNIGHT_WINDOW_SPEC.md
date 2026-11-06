# 268 — 随机生成后的单一判官窗口（开窗前）

写入UTC：2026-11-06T14:27:14.504955+00:00。当前rand2/3仍在生成，不在innet物理GPU2/3启动其他GPU作业。

复用已有单一CPU控制器PID1467341，不重复起抢卡控制器。它等待两份300完整输出和完成心跳，并等待两个生成进程退出释放idle_gpu锁及原wait_gpu≤2000MiB。随后按顺序：HF gate20（同数值误差<1e-3，旧/新PYes在0.05–0.95均至少8条）→rand2/3共600→现有旧曲线全部7个唯一alpha点和旧s1–s7共980→HF子进程退出→Guard在共同HF有害的24条提示上读两份输出，共48次同协议前向。没有量化或静默改变分块/阈值。

用户所述9个alpha点，目前文件库存只能定位0/0.25/0.5/0.75/1/1.25/1.5，缺的2点已询问，未补造；收到文件可在开窗前追加清单并哈希。现有d最近重建脚本实际用HF_node01旧曲线，而FRONTIER_POINTS保留vLLM验证横轴。新报告并列vLLM验证混后端诊断、原HF_node01对HF_innet、全部HF_innet三版，固定合法侧388口径，绝不因重判改标签文件或规则。

Guard既有2x2只说明提示覆盖重叠，不解释组合剩余。新24条配对分别列Punsafe_baseline、Punsafe_A、差和0.2拦截翻转；31/40对12/26只描述不同有害输出集合，不能称本配对检验。保留输出形式解释为假设。

rand2/3向量种子与两种sha256已补入results/frozen_vectors/manifest_wjb_rand2_rand3_addendum8.json；只补新只读文件，目录只读模式已恢复，旧向量不改。rand0/1的node01与rand2/3的innet跨节点局限保留；不在本夜再追加跨节点20条长生成抢占判官窗口。

## 哈希
- results/audit/handoff_round7/old_window_jobs.json: bc6dd97751ec3aef5606aec55fabc183d83befc2409d75bd80450027f67a3cab
- tools/handoff_20261106/round7_hf_window.py: 2d4f728283bd28677e0539233d19e53c569f87a258ad221e6623fda282be1caa
- tools/handoff_20261106/round7_guard_pair.py: ac572d30d4979b6fcfcb126050362ce3f1a27987443a9e04f41b2e5e314f02a5
- tools/handoff_20261106/round6_judge_randoms.py: 502894d898f1a623bc1a41af7a48d45bc72c3aeb83227805b7f8365b6374b9ee
- tools/handoff_20261106/round7_analyze_window.py: d2a124665cf2127498d7afbdbaba5fb714f4196aa3fe536ccd6394f091eaf682
- results/frozen_vectors/manifest_wjb_rand2_rand3_addendum8.json: 1dc38e3eb726ecdc8ad8a5d73dc24f9759ff759de28599905b7c61364a5b6c5d
