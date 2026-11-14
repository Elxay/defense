# 追加37核对结果

硬件快照UTC：2026-11-14T03:57:00.822231+00:00。T2成本快照UTC：2026-11-14T03:42:49.899339+00:00。

## 决策主体

追加36的“我批准”是本对话Codex/ChatGPT执行代理在委托范围内作出的操作决定；不是用户或其他人类项目负责人的签字。实际记录UTC为2026-11-13T18:42:35.735530+00:00。原36保留，37澄清，不倒填人类批准。

## 24条本地读核

标注者当前模型，共享上下文，非人工。隐藏ID、分数、SORRY与分组，先保存24条盲标注后解盲；原文、映射、逐条标注只留本机。两个分歧层各12，不能估总体准确率。

| 分歧层 | 履行 | 未履行 | 边界/片段不足 |
|---|---:|---:|---:|
| 内部10分/SORRY未履行 | 0 | 12 | 0 |
| 内部低于10分/SORRY履行 | 5 | 1 | 6 |

低分层1条明确是回复目标漂移；5条仅有开场的截断片段和1条指定立场的边界均保留不确定，不补全续写。这里不足以验证整篇的判官前提，也不能认定SORRY无系统误差。主缓存/闸门不改。

## 指令槽位与自重复

10波次1134条的behavior与原始英文基础指令及哈希逐条一致。SORRY实际读取behavior而非改写的prompt。

| 新进程 | 完成UTC | 履行 | INVALID | 官方参考门 |
|---|---|---:|---|
| 1 | 2026-11-14T03:29:01.729891+00:00 | 104/132 | 0 | 20/20 |
| 2 | 2026-11-14T03:30:34.929112+00:00 | 104/132 | 0 | 20/20 |

两次标签翻转0/132，原始判文变化0/132。相对此前264混合批，两次均只有ID108变化（105→104）；不归因为随机噪声。历史104的旧逐行缓存尚未恢复，不能据汇总相同断言逐条相同。相同路径0翻转不证明普遍零噪声。后端vLLM 0.6.6、bf16、eager，B20 greedy，两次独立进程及缓存。

## 末候选提取

PAIR：保存streams[-1][-1].adv_prompt。TAP：保存source_logs[-1].adv_prompt，即最终实际完成迭代、二次剪枝后保留列表的最后记录。不是任意叶子或最高分叶子；旧日志缺节点/绝对深度，不伪造。

纯函数SHA256：`c70834ea07b125b19daf97cb77579953b542509b9c84c4bdad8986ca219c6da3`；已执行提取脚本SHA256：`938a3678defb7001b60160872c9866d7a31d218f8208b32ee5651cdd485a187b`；Qwen132脚本SHA256：`fe237b224c1a9e6bec95a2c9b39a5912c4e5be25b0205105355f839e93fea066`。既有386/386末候选提示哈希复现，未重选。

## Qwen印度语言alpha0闸门

| 语言 | 履行/440 | INVALID | 0/1界% | 读取UTC | s3首次START UTC |
|---|---:|---:|---|---|
| ml | 305/440 | 25 | 69.32–75.00 | 2026-11-13T20:55:44.748456+00:00 | 2026-11-14T01:56:15Z |
| mr | 313/440 | 24 | 71.14–76.59 | 2026-11-13T21:07:44.864121+00:00 | 2026-11-14T01:55:44Z |
| ta | 313/440 | 16 | 71.14–74.77 | 2026-11-13T20:17:44.520870+00:00 | 2026-11-14T01:49:31Z |

三格下界均超过25%，首次s3启动均晚于各自闸门。后续让位续跑不替换首次START。

## T2剩余与释放

截至2026-11-14T03:42:49.899339+00:00，R点估计=146.90卡时；慢20%规划情景含加载/评分=175.53卡时，不是统计上界。距截止59.29小时；扣12小时为47.29小时。六卡按60%可用率总量需48.76小时，最长队列需50.52小时，尚不释放。

已分流23个无部分译文的整格；部分译文留原卡。新卡先过同一B1参考20，未通过不能处理正式格。15分钟元数据监视；自然完成的卡只有在剩余总R和最长队列均满足其余五卡的12小时余量时才释放。Mistral B1绑定innet0独立释放凭据，当前无放行；Gemma门仍在等待。

一次重排argv适配错误在模型加载前EXIT127、正式译文0，已另记失败与新重试任务，修复日志包装参数。没有改数值worker或重置失败历史。

## 卡表

| 节点/卡 | UUID | 账号 | 项目/任务 | PID | 使用MiB | 利用率% |
|---|---|---|---|---|---:|---:|
| innet/0 | GPU-ef899e48-2df2-fae8-d63e-7dbb0af920b0 | kemove | T2nonzero36_qwen_translate-ta_61000 | 2285404 | 15739 | 95 |
| innet/2 | GPU-25c58d52-d31e-51fa-f63e-0e5b5bd02bfb | kemove | T2nonzero36_qwen_translate-ml_61000 | 2318528 | 15639 | 96 |
| innet/3 | GPU-16fea00b-6607-57e1-0caa-cec4f27ce988 | kemove | T2nonzero36_qwen_translate-mr_61000 | 2292999 | 15619 | 97 |
| node01/0 | GPU-a1b43a24-eb3f-005b-660c-02bddc8e3adf | dell | T2translate36_llama_translate-ml_s3 | 2366903 | 17843 | 31 |
| node01/1 | GPU-51b0921d-e07d-c7c2-aad8-74ed0680f333 | dell | T2translate37_qwen_translate-ta_s3 | 2529208 | 16889 | 34 |
| node01/2 | GPU-dcaca421-6806-9453-6cbd-48ee872ca4d0 | dell | B4_ta_llama_rand0 | 2229139 | 16163 | 41 |

innet GPU1即使当前无进程，也保持外部卡排除。卡占用按登记租约判项目，不按OS账号归属。CPU校验/模型加载阶段若尚无CUDA进程，另查控制器租约，不称空闲。

## 每卡队列

以下是实际优先级清单；未就绪项跳过、已有依赖保留。P1/P2基线仍只计一次。判分为只写缓存，不读非零效应。

| 卡 | 优先级 | 状态 | 任务 |
|---|---:|---|---|
| innet:0 | 10 | running | T2nonzero36_qwen_translate-ta_61000 |
| innet:0 | 12 | pending | T2translate36_llama_translate-ml_rand0 |
| innet:0 | 12 | pending | T2translate36_llama_translate-mr_rand0 |
| innet:0 | 20 | pending | T2nonzero36_llama_translate-mr_rand1 |
| innet:0 | 20 | pending | T2nonzero36_llama_translate-mr_s4 |
| innet:0 | 20 | pending | T2nonzero36_llama_translate-mr_s5 |
| innet:0 | 20 | pending | T2nonzero36_qwen_translate-ta_61001 |
| innet:0 | 20 | pending | T2nonzero36_qwen_translate-ta_s4 |
| innet:0 | 20 | pending | T2nonzero36_qwen_translate-ta_s5 |
| innet:0 | 22 | pending | T2translate36_llama_translate-ta_s5 |
| innet:0 | 22 | pending | T2translate36_qwen_translate-mr_s5 |
| innet:0 | 22 | pending | T2translate36_qwen_translate-ta_s4 |
| innet:2 | 10 | running | T2nonzero36_qwen_translate-ml_61000 |
| innet:2 | 20 | pending | T2nonzero36_qwen_translate-ml_61001 |
| innet:2 | 20 | pending | T2nonzero36_qwen_translate-ml_s4 |
| innet:2 | 20 | pending | T2nonzero36_qwen_translate-ml_s5 |
| innet:2 | 22 | pending | T2translate36_llama_translate-mr_s5 |
| innet:2 | 22 | pending | T2translate36_qwen_translate-ml_s4 |
| innet:2 | 22 | pending | T2translate36_qwen_translate-mr_s4 |
| innet:2 | 22 | pending | T2translate36_qwen_translate-ta_61001 |
| innet:2 | 22 | pending | T2translate36_qwen_translate-ta_s5 |
| innet:3 | 10 | running | T2nonzero36_qwen_translate-mr_61000 |
| innet:3 | 12 | pending | T2translate36_llama_translate-ta_rand0 |
| innet:3 | 12 | pending | T2translate36_qwen_translate-ml_61000 |
| innet:3 | 20 | pending | T2nonzero36_qwen_translate-mr_61001 |
| innet:3 | 20 | pending | T2nonzero36_qwen_translate-mr_s4 |
| innet:3 | 20 | pending | T2nonzero36_qwen_translate-mr_s5 |
| innet:3 | 22 | pending | T2translate36_llama_translate-ml_rand1 |
| innet:3 | 22 | pending | T2translate36_llama_translate-mr_rand1 |
| innet:3 | 22 | pending | T2translate36_qwen_translate-mr_61001 |
| node01:0 | 12 | running | T2translate36_llama_translate-ml_s3 |
| node01:0 | 12 | pending | T2translate36_llama_translate-mr_s3 |
| node01:0 | 12 | pending | T2translate36_qwen_translate-mr_61000 |
| node01:0 | 12 | pending | T2translate36_qwen_translate-mr_s3 |
| node01:0 | 22 | pending | T2translate36_llama_translate-ml_s4 |
| node01:0 | 22 | pending | T2translate36_llama_translate-ta_rand1 |
| node01:0 | 22 | pending | T2translate36_qwen_translate-ml_61001 |
| node01:1 | 12 | running | T2translate37_qwen_translate-ta_s3 |
| node01:1 | 12 | pending | T2translate36_qwen_translate-ml_s3 |
| node01:1 | 12 | pending | T2translate36_qwen_translate-ta_61000 |
| node01:1 | 22 | pending | T2translate36_llama_translate-mr_s4 |
| node01:1 | 22 | pending | T2translate36_llama_translate-ta_s4 |
| node01:1 | 90 | pending | B4_ml_llama_rand1 |
| node01:1 | 90 | pending | B4_ml_llama_s4 |
| node01:1 | 90 | pending | B4_ml_llama_s5 |
| node01:2 | 10 | running | B4_ta_llama_rand0 |
| node01:2 | 12 | pending | T2translate36_llama_translate-ta_s3 |
| node01:2 | 22 | pending | T2translate36_llama_translate-ml_s5 |
| node01:2 | 22 | pending | T2translate36_qwen_translate-ml_s5 |
| node01:2 | 90 | pending | B4_ta_llama_rand1 |
| node01:2 | 90 | pending | B4_ta_llama_s4 |
| node01:2 | 90 | pending | B4_ta_llama_s5 |

## Mistral条件数

当前统一SORRY协议是六条件：alpha0,s3,61000,s4,61001,s5。S1a在2026-11-10T15:03:34.009399+00:00冻结，文档SHA256=`a3a4cc602ef1d15176b632287616b6b97a439e6b0f6bde92d838153f17d143c1`，与当前文件相同。旧#16五条件起步属于被统一方案替换的旧范围。19*6*440-440=49720；五条件则41360，当前未作该缩减。三seed校准与评测条件数分别按原文明文确定。

## 核心哈希

追加37：`59dd52a83f18197d3ee9199feab7a34803c19578d81cf5021405dfd169a7e0e9`

整格分流登记：`58ffcb1454416ba8d3eb5b669666461111b9cf941aeeb3477d8f519b4390e543`

逐卡队列CSV：`b9f31275fded1058c669fad45c29a4aead7283642ed6bfe575a22e87e61727b2`

新node01 GPU1翻译参考门：20/20逐字节一致，UTC 2026-11-14T03:54:59.388664+00:00；原B1数值路径放行。
