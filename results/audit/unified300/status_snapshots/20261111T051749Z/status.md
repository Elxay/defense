# 当前运行快照

date -u: 2026-11-11 05:17:48 UTC；node01: 2026-11-11 05:17:49 UTC

只读PID、进度、资源及门检元数据；未读取主测试标签或效应。

| 节点/卡 | 显存 MiB | 利用率 | 计算PID | 项目/任务 |
|---|---:|---:|---|---|
| innet/0 | 15061/24564 | 86% | 1333963 | qwen/base/61001/generating |
| innet/1 | 11441/24564 | 72% | 1285516 | 外部项目；排除调度 |
| innet/2 | 16271/24564 | 85% | 1316343 | llama/base/s4/generating |
| innet/3 | 15761/24564 | 95% | 1046820 | qwen/translate-mr/generating_alpha0 |
| node01/0 | 17530/24564 | 53% | 3673815 | llama/translate-ta/alpha0/generating |
| node01/1 | 29/24564 | 0% | — | 空闲/无compute上下文 |
| node01/2 | 17583/24564 | 49% | 3668058 | llama/translate-mr/alpha0/generating |

## 保存行数（按生成home节点，镜像不重复计数）

| 节点 | 缓存 | 已保存 | 正常完成标记 |
|---|---|---:|---|
| innet | language_alpha0/llama/translate-ml | 440/440 | 无 |
| innet | language_alpha0/qwen/translate-ml | 440/440 | 有 |
| innet | language_alpha0/qwen/translate-mr | 100/440 | 无 |
| innet | language_alpha0/qwen/translate-ta | 440/440 | 有 |
| innet | ready_generated/llama/base/rand0 | 440/440 | 有 |
| innet | ready_generated/llama/base/s3 | 440/440 | 有 |
| innet | ready_generated/llama/base/s4 | 416/440 | 无 |
| innet | ready_generated/llama/translate-zh-cn/alpha0 | 440/440 | 有 |
| innet | ready_generated/qwen/base/61000 | 440/440 | 有 |
| innet | ready_generated/qwen/base/61001 | 44/440 | 无 |
| innet | ready_generated/qwen/base/s3 | 440/440 | 有 |
| innet | ready_generated/qwen/base/s4 | 440/440 | 有 |
| innet | static_alpha0/llama/authority_endorsement | 440/440 | 有 |
| innet | static_alpha0/llama/base | 440/440 | 有 |
| innet | static_alpha0/llama/deepinception | 440/440 | 有 |
| innet | static_alpha0/llama/evidence-based_persuasion | 440/440 | 有 |
| innet | static_alpha0/llama/expert_endorsement | 440/440 | 有 |
| innet | static_alpha0/llama/logical_appeal | 440/440 | 有 |
| innet | static_alpha0/llama/misrepresentation | 440/440 | 有 |
| innet | static_alpha0/llama/prefix_P1 | 440/440 | 有 |
| innet | static_alpha0/llama/prefix_P2 | 440/440 | 有 |
| innet | static_alpha0/llama/refusal_suppression | 440/440 | 有 |
| innet | static_alpha0/qwen/authority_endorsement | 440/440 | 有 |
| innet | static_alpha0/qwen/base | 440/440 | 有 |
| innet | static_alpha0/qwen/deepinception | 440/440 | 有 |
| innet | static_alpha0/qwen/evidence-based_persuasion | 440/440 | 有 |
| innet | static_alpha0/qwen/expert_endorsement | 440/440 | 有 |
| innet | static_alpha0/qwen/logical_appeal | 440/440 | 有 |
| innet | static_alpha0/qwen/misrepresentation | 440/440 | 有 |
| innet | static_alpha0/qwen/prefix_P1 | 440/440 | 有 |
| innet | static_alpha0/qwen/prefix_P2 | 440/440 | 有 |
| innet | static_alpha0/qwen/refusal_suppression | 440/440 | 有 |
| node01 | ready_generated/llama/translate-fr/alpha0 | 440/440 | 有 |
| node01 | ready_generated/llama/translate-mr/alpha0 | 128/440 | 无 |
| node01 | ready_generated/llama/translate-ta/alpha0 | 96/440 | 无 |

Llama translate-ml 已存440但3GiB资源断言失败，保留为阻塞，不计正常完成。node01 ta/mr在PAIR双卡高优先级窗口按批边界暂停，检查点SHA与续跑核对记录由队列保存。

队列PID 1321386；就绪任务 18；外部innet GPU1不参与。

桌面通知被Windows脚本策略阻止；远端15分钟告警日志/控制台有效，未绕过策略。
