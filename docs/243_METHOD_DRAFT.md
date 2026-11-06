# 243 — 方法与设置（正文初稿）

## 3.1 模型与注入协议
Llama-3.1-8B-Instruct（rev 0e9e39f2）与 Qwen2.5-7B-Instruct。转向向量 v = α·ρ·θ/‖θ‖，注入残差流：Llama 第 9 层、Qwen 第 8 层（28 层约 30% 深度）。仅注入最后一个 prompt token，单次；统一用 generate_with_injection，断言 injection_count==1、positions==[n-1]、rho_runtime。α=0 走同一函数零向量路径；20 条 WJB 提示上与无 hook 的 model.generate 逐字节相同（20/20）；跨节点（驱动 575 vs 580）、跨显卡、带注入 α=1.0 70/70 逐字节相同。

ρ：Llama layer 9 范数约 5.6–6.0（‖h‖≈5.8），取 ρ=5.21（≈0.9‖h‖）；Qwen layer 8 最后 prompt token 范数实测 36.2（SD 0.4，20 条），ρ 按相对比例并扫 {0.25,0.5,0.75,1.0,1.25}×‖h‖。

## 3.2 数据划分
- val70：70 个 HarmBench behavior，PAIR 攻击经 Llama α=0 判官筛选成功；主表主集。
- 合法集：400 条（ord/sens/long/roleplay 各 100），过拒分母：Llama 388（基线已答）；Qwen 392（基线已答，Qwen 基线拒答 8/400=2.0%，这是基线拒答率而非"新增"）。
- 训练输入：12 条 fit 攻击（attacks_fit12.json，sha256 5b8886a6…；重训 seed3 cos=0.99994 验证）+ 60 条 keep。
- b8_train_strat：97 条，与 val70 交集 0。
- WJB：adversarial_harmful 82,728 行，抽 300（wjb300.json，971d8b3d…），behavior 用 vanilla。
- 候选池：479 组 → 去版权 98 → 去 contextual 93 → 161 → 去 train_strat 97 → 64；v5.1 抽 29（04c8dc94…），本文未使用。

## 3.3 判官与拒答规则
HarmBench 13B：HF（node01）与 vLLM（innet）；同后端两次 34 条逐位一致；跨后端 1746 条 P>0.5 翻转 2 条、mid 0.0602、gate 未过 → 主表单后端。判分全文；>1900 token 分块重叠 200，取最大 P(Yes)，INVALID 计入分母。规则 v2：B1a 合法侧 0/30、Qwen α=0 合法侧 0/30 漏判。严格 ASR=P(Yes)>0.5；宽松口径需第二评审（暂缓，只进附录）。Guard-3 与 StrongREJECT 作交叉判官；StrongREJECT 为第三方合并检查点，等价性未验证。

## 3.4 预注册与外部时间戳
判据在数据产生前写入 docs/230–242 与 PREREG_LOG.txt。自 2026-11-06 00:34 JST 起推送 GitHub 私有仓库 Elxay/defense 提供外部时间戳；更早状态（39d8a26a/22f319e0/de611fe3）仅服务器日志自证。统一表述 "pre-specified in a versioned log"。

## 3.5 可复现性
生成脚本记录模型快照、injection_count、rho_runtime；关键清单与 sha256 存档；训练脚本写入 data_hash（由 attacks_fit12 事件新增的规范）。