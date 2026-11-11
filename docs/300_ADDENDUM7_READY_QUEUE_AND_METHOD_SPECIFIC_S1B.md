# 300 追加7：空闲卡监视、就绪租约与分方法S1b

冻结UTC：2026-11-11T03:58:15.117321+00:00

每30秒读取7卡的compute上下文、显存和已登记租约。非外部卡无compute、显存<2GB且无有效租约才计空闲；连续15分钟写alerts.jsonl并输出控制器告警，每15分钟重复。低利用率不等于空闲。innet GPU1排除调度与空闲告警。告警当前落本地日志，不冒充外部推送。

任务目录含blocked候选，但ready集合只包含前置元数据门齐全者；只按冻结优先级经共享flock、wait_gpu和launch_job领卡，不读取判官标签。任务退出/断言资源失败后保留文件、记failed，不阻塞独立任务；不自动缩批或重跑失败条件。PID与命令身份核验防止死租约长占；进程仍持CUDA上下文则不误派。高优先级PAIR双卡窗口在当前生成批次完整落盘后让位，暂停输出哈希与续跑UTC由租约目录保存。

语言只迁移尚无输出的Llama四家族：ta node01 GPU1、mr node01 GPU0、zh-cn innet GPU2、fr node01 GPU2；各先本卡模型20门及该家族zero20，六条件在家族内固定home节点。原Qwen语言队列不抢取重复行，Llama ml已保存440但资源门失败，排除自动续跑。模板、batch成员、B8/B4、2400、alpha和seed不变，UUID逐行保存。跨节点生成标记节点，保留仅innet敏感性口径。

英语20单元SORRY alpha0闸门已按追加6读取、均活跃，非零按已冻顺序s3/第一随机/s4/第二随机/s5依赖前项完成；只生成缓存，不读效应。显存3GiB断言仍是硬门。基向量ρ在调用前显式乘所选alpha，核心alpha参数只作记录，准备的scaled向量SHA固定，避免漏乘/重复乘。

S1b拆为逐方法：PAIR正式解析器/目标零20/8行为两顺序控制器门全部过后，先Llama10行计时；不等TAP、AutoDAN。10计时行保留正式集合。角色及库配置不由新输出决定；AutoDAN规模另由AutoDAN_build_scale_frozen.json固定（300热身、每请求最多150迭代、1次总结及JSON包装、k5、先20热身计时，库冻结后测试不更新）。

队列SHA 470019bc68e6cf87de4cea78038e3bad7ffc7c5d72892fa279cbb5e04927464a；生成计划SHA f39e140e9eab4df0debddf213099082f1b68eb0b9d6065bd7a06d630f00830ce。
