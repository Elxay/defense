# 241 — 论文提纲（2026-11-06）

每节列出要引用的证据文件与哈希；未完成项标 [TODO]。

## 1. 引言
- 问题：过拒受控前沿上，学出的 prefill 转向向量比零训练基线多买到什么；有效性来自哪里；评测怎样被误导。
- 贡献：零线（同范数随机方向）、LMI 分解、风格效应剂量响应、零训练基线持平、评测陷阱清单（15 条）。

## 2. 相关工作（待核对全文/摘要状态）
- 转向向量与可解释性：PrOSV、ReFT、BiPO、AlphaSteer/AdaSteer、Steering Safely or Off a Cliff、TRYLOCK、Jailbreak Antidote、Topological Steering、Residual-norm normalization、Calibrating activation vectors。
- 判官可靠性：How Reliable Is Your Jailbreak Judge、An Empirical Measurement of Jailbreaking Evaluators、TamperBench、Where Do Reasoning Models Refuse、LLM-Safety Evaluations Lack Robustness。
- 攻击：PAIR/TAP、HarmBench、WildJailbreak、StrongREJECT。
- 状态：已检索约 20 篇；全文精读 [TODO 列表]。

## 3. 方法与设置
- 模型：Llama-3.1-8B-Instruct（rev 0e9e39f2），Qwen2.5-7B-Instruct。
- 注入：layer 9（Llama）/ layer 8（Qwen），最后 prompt token，单次，`generate_with_injection`，injection_count 断言。
- 数据：val70（PAIR，Llama 优化）、legal 400（388 基线已答）、WJB 300（adversarial_harmful）、候选池 v5.1（29/64，未用）。
- 判官：HarmBench 13B（HF node01 / vLLM innet）、Llama-Guard-3、StrongREJECT（第三方合并权重，未验证等价）。
- 规则：v2 拒答规则；严格/宽松双口径（宽松只进附录）。
- 预注册与外部时间戳：`docs/230–240` + `PREREG_LOG.txt`，GitHub 私有仓库 commit（首次 2026-11-06 00:34 JST）；更早状态仅服务器日志自证。

## 4. 结果
### 4.1 零线（`docs/236` v2）
- 11 个同范数随机方向：rand 3 个 68.6–80.0%，init-only 8 个 70.0–85.7%，合并 mean 75.7 SD 4.6；学出向量 8 seed 18.6–30.0%。
### 4.2 LMI 分解
- cond1 30.0% vs α=0.75 31.4%（McNemar 4/3，p=1.00）；cond2 17.1% vs 18.6%（7/6，p=1.00）；cond2 五 seed 配对差 +3/+1/−4/−4/+4，合并 0.0pp CI [−5.7,5.7]。
### 4.3 风格效应与剂量响应
- 旧训练器 5/5：+3.4–8.2pp（区间排除 0）；新训练器 α=1.0 4/4 为正。
- 剂量：s5 +32.4（α=1.0）→ +9.9（0.75，OR 8.5%）→ +2.4pp（0.5，OR 2.8%）。
- 匹配过拒：新两点（6.4/8.5%）vs 旧五点，差 +3.31pp CI [0.80,5.82]，未达 ±3 等价（新侧 n=2）。
- 合法过拒：α=0.75 各 seed 6.4–16.8%，α=0.5 2.1–4.6%（分母 388）。
### 4.4 零训练基线（Llama）
- system prompt A（35.7%,1.0%）、输出侧 Guard（18.6%,5.2%）、组合（5.7%,7.2%）vs 学出 α=1.0（18.6%,4.9%）。
### 4.5 第二模型（Qwen）[TODO]
- α=0：512 上限 62.9%（44/70）、2400 上限 57.1%（40/70）；fit12 10/12 合规；合法基线 8/400（2.0%）。
- 四条件 A/B（replace/append）[运行中]；Guard [TODO]；向量训练 [TODO]。
### 4.6 WJB（非 PAIR 攻击族）[TODO]
- 300 条，α=0 ASR 39.3%（闸门通过）；处理组待做（需零向量 20 条检验）。

## 5. 评测陷阱
- 即 `docs/240_EVAL_TRAPS_PROSE.md`（15 条 + 未解决问题）。

## 6. 局限
- 人工评审暂缓；StrongREJECT 未验证等价；WJB 判官口径未验证；Llama 独立 test 缺失（PAIR 未运行）+ val 攻击对 Llama 优化偏差；Qwen 未训练向量；候选池未使用；C2 匹配新侧 n=2。

## 7. 附录
- 复现性：`attacks_fit12.json`（5b8886a6…）、`pool_clean64.json`（df9f0f75…）、`test_pool v5.1`（04c8dc94…）、WJB300（971d8b3d…）。
- 同账号进程安全：safe_kill + PID 登记表。
EOF