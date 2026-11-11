# 规则16、当前家族生成表与后续模型准备

卡快照 UTC：2026-11-11T14:47:00.719973+00:00；生成快照 UTC：2026-11-11T14:46:58.099614+00:00

HarmBench首窗实际12:51:24.981658→14:29:10.878709 UTC，双卡占用5865.90秒（1小时37分45.90秒）。21,120条缓存完成，未读标签汇总或INVALID总数。GPU2/3已还给生成；GPU0期间也在生成与SORRY小波次之间接续。

## 卡与项目

| 卡 | 账号 | 项目任务 | CUDA PID | 命令 |
|---|---|---|---:|---|
| innet GPU0 | kemove | main_llama_authority_endorsement_s3 | 2019205 | unified300_ready_generate_v3.py |
| innet GPU1 | kemove | external/excluded | 1285516 | python |
| innet GPU2 | kemove | main_llama_logical_appeal_s3 | 2017053 | unified300_ready_generate_v3.py |
| innet GPU3 | kemove | main_qwen_authority_endorsement_s3 | 2014466 | unified300_ready_generate_v3.py |
| node01 GPU0 | dell | AutoDAN_warmup_pilot20_v4 | 3979345 | unified300_autodan_worker_v4.py |
| node01 GPU1 | dell | AutoDAN_warmup_pilot20_v4 | 3979345 | unified300_autodan_worker_v4.py |
| node01 GPU2 | dell | language_alpha0_reply_preprocessing_v2_CF | 4105176 | u300_language_preprocess_worker_v2.py |

GPU1外部任务不动；同账号不代表同项目。

## 88预算规则

上界<25%失败格未来扩档成本剔除；所有已耗搜索算力仍计600总账。INVALID跨线暂计并标未决。最大档选择只用alpha0门与剩余预算，不读非零效应；未知成本不按0。代码边界/账本固定样例已通过，未据样例发放执行许可。
含一次冷启动顺序：PAIR-L 3.41、PAIR-Q 5.38、TAP-L 21.05、TAP-Q 35.91卡小时。新88行冻结时0；TAP88已接入同顺序，但新固定20和12行为8/4并发结构门未过前不运行正式行。220/440仍需新逐格执行准入，不写旧outcomes_used=False绕过alpha0门。
n10诊断汇总只留审计日志，不进论文结果表；原计时行为仍进入正式88。当前不能把预期无动态范围写成已证实；每格等88门。
追加16 SHA256 `75b0733c73b0006b97fdd6e401ba5d91f0f67b13ef9c5cb99c689a20bf644e6c`

## 模型准备

| 项 | Gemma-2-9B-it | Mistral-7B-Instruct-v0.3 |
|---|---|---|
| 范数 | 完成：layers[12] M=141.9122, rho=127.7210 | 完成：layers[9] M=2.5897, rho=2.3308 |
| 原生基线 | 旧合法400+val70=470完成；新700未开始 | 旧470未开始；新700未开始；原生预审基线任务已排队 |
| 渲染 | 完成；eager禁编译；A/B用户轮前置 | 完成；sdpa；system合并INST |
| 拒答检查 | WG470完成，固定30+30盲读尚未标注 | 未开始，依赖原生基线 |
| 学出向量 | 0/3，未训练 | 0/3，未训练 |
| 统一700校准及alpha | 未开始 | 未开始 |

开始目标：Gemma固定样本复核是CPU读数，不应继续当作等GPU。Mistral预审基线已注册为低优先、可让位任务：Llama英语prefix_P2 s5完成后，GPU2空闲经wait_gpu即启动，不等搜索或整轮结束。按当前英语ETA，预计11/12午后具备接卡机会；若更高优先任务介入则11/13–14。两模型训练目标11/13、统一700校准目标11/13–14，均以自己的keep60目标包、拒答和执行门通过为前提；旧470不是新700校准。

## 翻译与泰米尔语

WG首波退出14:05:29.268136 UTC，缓存同步后释放收据14:08:13.587299。先前已经启动的ASCII工程门完成后，CF翻译已占node01 GPU2；两模型从未同卡同时驻留。其余编码任务已加CF完成前置。Llama泰米尔alpha0已有76行；已提高补齐优先级，CF已有四单元不等它，其余印度语言保持后置。9个已有完整alpha0单元仍需各自回复预处理，并非其余语言已经全部翻译。

## HiddenDetect资产

ModelScope全精度权重已于13:41:32.792454 UTC完成10个所需文件下载，三片权重逐片实测SHA与原HF LFS清单一致。manifest SHA256 `d371a76f876110255042501f9f9b465008976c1d48aea095d9cce00a167d894b`。这不是接口或检测复现通过。
作者load_FigTxt函数没有类别筛选；当前上游CSV500行/10类。依用户指令使用完整500并标非原设置，不猜350/7类子集、不套原350行复现通过线。

## 家族×条件表

# 家族×条件生成表，ETA v3

UTC 2026-11-11T14:46:58.099614+00:00

✓=440且完成标记有效；数字*=正在生成；锁=前置未齐；✓不代表判分已齐。ETA是已知窗口/判分预留两个情景，不是置信区间或保证。

HB已于11/11 23:29 JST释放；未来SORRY GPU0总算力预留1.85小时。

## llama

| 家族 | α0 | s3 | r0 | s4 | r1 | s5 | 全六条件生成ETA JST |
|---|---:|---:|---:|---:|---:|---:|---|
| base | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 已齐 |
| deepinception | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 已齐 |
| refusal_suppression | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 已齐 |
| logical_appeal | ✓ | 352* | 0 | 0 | 0 | 0 | 11/12 01:35 ～ 11/12 01:35 |
| authority_endorsement | ✓ | 296* | 0 | 0 | 0 | 0 | 11/12 01:30 ～ 11/12 03:11 |
| misrepresentation | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 03:51 ～ 11/12 04:06 |
| evidence-based_persuasion | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 03:40 ～ 11/12 05:16 |
| expert_endorsement | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 05:49 ～ 11/12 07:25 |
| prefix_P1 | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 08:12 ～ 11/12 09:38 |
| prefix_P2 | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 10:35 ～ 11/12 11:45 |
| translate-ta | 76 | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| translate-ml | ✓ | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| translate-mr | ✓ | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| translate-zh-cn | ✓ | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| translate-fr | ✓ | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| ascii | 0 | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| caesar | 0 | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| morse | 0 | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| atbash | 0 | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |

## qwen

| 家族 | α0 | s3 | r0 | s4 | r1 | s5 | 全六条件生成ETA JST |
|---|---:|---:|---:|---:|---:|---:|---|
| base | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 已齐 |
| deepinception | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 已齐 |
| refusal_suppression | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 已齐 |
| logical_appeal | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 已齐 |
| authority_endorsement | ✓ | 100* | 0 | 0 | 0 | 0 | 11/12 02:38 ～ 11/12 02:38 |
| misrepresentation | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 05:59 ～ 11/12 05:59 |
| evidence-based_persuasion | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 07:01 ～ 11/12 07:15 |
| expert_endorsement | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 09:05 ～ 11/12 09:05 |
| prefix_P1 | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 09:44 ～ 11/12 13:45 |
| prefix_P2 | ✓ | 0 | 0 | 0 | 0 | 0 | 11/12 11:49 ～ 11/12 12:22 |
| translate-ta | ✓ | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| translate-ml | ✓ | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| translate-mr | ✓ | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| translate-zh-cn | ✓ | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| translate-fr | ✓ | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| ascii | 0 | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| caesar | 0 | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| morse | 0 | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
| atbash | 0 | 锁 | 锁 | 锁 | 锁 | 锁 | 待前置/行速 |
