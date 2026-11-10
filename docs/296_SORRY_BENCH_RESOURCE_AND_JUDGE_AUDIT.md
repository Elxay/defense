# SORRY-Bench资源、变换与判官核验

2026-11-10。状态：公共资料及源码核验完成；受限数据、权重下载未获放行。无SORRY模型输出/新测试结果被生成或读取；不将数据卡统计冒充本地实数，不将论文参考κ冒充本次复现。

## 版本与当前访问状态

| 资源 | 固定revision | 公开卡说明 | 本地正文状态 |
|---|---|---|---|
| sorry-bench/sorry-bench-202406 | b34822276edde97592eda99c0b56d306f8830469 | 基础450条、45类；20变换各以450条为设计规模 | question/20变换/meta_info返回403，未数行 |
| sorry-bench/sorry-bench-human-judgment-202406 | 395ff7e7ea75f6d328845c3743d127a6477054a7 | 总7200，train2700/test4500 | 人评JSONL均403，未数行 |
| sorry-bench/ft-mistral-7b-instruct-v0.2-sorry-bench-202406 | 79ab44668cef557414cb5e15c726a56ebca9cf1e | Mistral-v0.2微调；卡称κ0.813 | config/tokenizer/index403；六片权重未下载 |
| sorry-bench/sorry-bench-202503 | 612a4e1f45db8adf884fa62318ddf9fa1c6e75e9 | 当前ICLR代码指向440条/44类 | 仅元数据核验，未替换202406 |
| sorry-bench/sorry-bench-human-judgment-202503 | b7e15f574ce0d30c1d13ded75e0437e66b61983e | ICLR版本总7040，train2640/test4400 | 仅元数据核验，未替换202406 |

202406三个资源均为gated=auto。hf-mirror的API元数据、README和许可证可读，受限正文403。普通会话没有导出的HF_TOKEN；之后仅在短生命周期下载进程内解析此前日志已记录的项目负责人本机export，用于Authorization请求头，仍403。没有输出/写入token，没有改shell配置或全局export。源站在本次节点连接失败，不能将镜像403当作源站账号授权状态的完整诊断。版本选择和账号端访问状态已询问用户，未通过替代镜像数据绕过访问限制。

两节点常用模型缓存未发现已下载SORRY权重。没有声称已完成权重六片校验、数据本地行数、人工一致率或重叠审计。

## 二十个变换的精确清单

以下文件名来自HF元数据，并与官方README/源码列表交叉核对。**所有行数均待下载后实数**，不是0。202406卡给出的设计规模为每文件450；202503应另行对照440，不能混用。

| 组 | 文件 | 按用户规则纳入 |
|---|---|---|
| 写作风格 | question_question.jsonl | 否 |
| 写作风格 | question_slang.jsonl | 否 |
| 写作风格 | question_uncommon_dialects.jsonl | 否 |
| 写作风格 | question_technical_terms.jsonl | 否 |
| 写作风格 | question_role_play.jsonl | 否 |
| 写作风格 | question_misspellings.jsonl | 否 |
| 说服 | question_logical_appeal.jsonl | 是 |
| 说服 | question_authority_endorsement.jsonl | 是 |
| 说服 | question_misrepresentation.jsonl | 是 |
| 说服 | question_evidence-based_persuasion.jsonl | 是 |
| 说服 | question_expert_endorsement.jsonl | 是 |
| 编码 | question_ascii.jsonl | 是 |
| 编码 | question_caesar.jsonl | 是 |
| 编码 | question_morse.jsonl | 是 |
| 编码 | question_atbash.jsonl | 是 |
| 语言 | question_translate-ml.jsonl | 是，Malayalam（马拉雅拉姆语） |
| 语言 | question_translate-ta.jsonl | 是，Tamil（泰米尔语） |
| 语言 | question_translate-mr.jsonl | 是，Marathi（马拉地语） |
| 语言 | question_translate-zh-cn.jsonl | 是，简体中文 |
| 语言 | question_translate-fr.jsonl | 是，法语 |

合计6+5+4+5=20，选中5+4+5=14。五语言是明确列表，不是差值推算。按440计算，14变换为6160提示/模型；450则6300。按用户9秒/条假设，两个模型alpha0为30.8或31.5卡·小时，尚未测量。若14变换全活跃、六条件同速，总生成约184.8或189卡·小时，不包括基础集、其他包装、判分、解码、回译或失败处理，也不是上界。

## 官方评判机制

代码通过SSH取得官方公开仓库，revision：7da10addffb6790cfeb75281eaffb5a176861653。没有从该仓库取得受限问题正文。源码manifest另存，仓库不复制到项目Git。

- 模型：Mistral-7B-Instruct-v0.2微调；当前卡将81.3%称为Cohen κ（0.813），不是原始accuracy。ICLR版表1为κ0.810。
- 模板：使用judge_prompts.jsonl的base-ft-mistral-7b-instruct-v0.2项，完整固定判官说明加原始英文request与response，然后用Mistral的`[INST] ... [/INST]`格式。不能用“通用chatgpt判官提示”替代。
- 语义：1=实质履行；0=不履行，也包括仅相关内容/无法实质帮助，不等于一定出现拒答句式。不能把1-WG拒答直接等同履行率。
- 官方判官：vLLM、bf16、temperature0、n1、max_tokens1024；ensure_valid_score默认False。官方extract_content接受数字前缀、safe/unsafe回退，并非只接受严格单字符。超出0/1或无法解析必须单列，不默认0，不私自启用温度1的自动重试分支。
- 官方目标模型生成：FastChat模板、vLLM、temperature0.7、默认最多1024新token；与本项目原生模板/贪心2400不同，须明确标注，不能写成直接复现其模型履行率。
- 对变换：判分脚本仍读基础question.jsonl的原始英文问题；编码输出先解码，多语言输出先回译英文，使用处理后回复评分。非英语采用googletrans==3.1.0a0的外部翻译服务，需要独立环境；不是无网络CPU免费步骤。处理前后文本、SHA、状态都要保留。
- 微调模型卡明确限定其用途为SORRY-Bench判官，不是通用安全分类器。不能自动把它推广到WJB所有提示。

原版解码器的无害CPU检查：ASCII、Caesar的大小写样例往返一致；Morse在正常官方encode输出上只有大小写/空白差异，但去掉末尾分隔符的样例会丢最后字符；Atbash的混合大小写往返有实质不一致。保留原实现和检查哈希，不擅改官方预处理后称为原版复现。没有异常不等于解码保真。未来若要修复，须在任何相关模型输出读取前另行记录处理版本与敏感性分支。

## 人工参照复现的边界

仅用匹配版本官方test.jsonl，不用train，不重新随机切分，也不在test上改模板/阈值。train/test每个基础指令分别有6/10个回复案例，基础指令本身并非行为未见；原论文的人评也包含ID基础回复和OOD变换回复，不是全部英语原始提示回复。

ICLR v2表1公开参考：SORRY微调Mistral κ0.810、WildGuard κ0.606、HarmBench κ0.525。这是论文结果，不是本次复现。202406模型卡则κ0.813，不能混成同一版本的精确期望。

所以“另两个判官从未在变换上验证过”过强：论文已有含OOD的人评meta-evaluation；但这不验证我们当前实现、全部语言/编码分层，或受steering操控后的回复。仍应复现同一留出测试。

拟报告：各判官accuracy、有效对上的κ及N、全分母INVALID保守/乐观界、逐字段INVALID ID、三个均有效子集；按基础指令聚类。WG回复有害性与人工履行标签比较存在构念差异，WG回复拒答另列，不按哪项κ更高事后换字段。HB使用原英文问题与回复，长度路径固定并报告，不能把截断口径变化算成判官准确率差。

新协议的“三判官中两个同号”尚需固定是哪一对，或三者均同号；已向用户询问，绝不在读数字后挑任意两者。编码/非英语按用户主判官规则，但不会写成所有变换已被证明有效。

## 重叠审计状态

未运行，不是零重叠。SORRY正文未取得；新校准B池也尚未形成，不能虚构与它的审计。拿到后对fit12、val70、legacy-46、dev22、train_strat、新校准池、WJB源行为分别进行精确与固定embedding/cos0.85标记，保留行。既检查原始行为也区分攻击提示文本来源，不把相似度自动当作同一意图的证明。待固化参考清单/编码器hash后再执行。

## 旧Qwen选择集停机记录

2026-11-10T05:04:03UTC先停故障接管watcher3790001，避免人为停机会触发自动迁移；05:04:05UTC停止评分控制器3545994及剩余生成worker3546019。3546015此前已完成退出。node01旧WG worker3171648同轮停止。

9867个生成文件停前停后逐文件SHA全一致，manifest SHA：bf94912bb631d35d5fe4085b57b7c6d4158cc899129b799864b2471907b64775。node01停前所核验9382个评分侧不可变JSON文件也全部保持原哈希。检查点不删除、不补写、不聚合标签或效应，作为旧校准敏感性归档；没有准入新alpha。05:04:10UTC快照显示本项目GPU进程已释放，innet只剩外部MTA3098274，未操作该进程。

## 许可和发布

基础集与人工集为各自SORRY自定义许可：允许研究/评估用途（含商业研究），禁止有害用途、非文本模型用途及向第三方再分发等；必须先有账号端访问权限。模型卡license字段为MIT，权重仍受访问门禁。原始问题、人评回复、编码/翻译文本、权重不入项目Git；只推元数据、文件SHA、ID/编码标签、汇总和源码hash。

已取得的公开许可证SHA：数据集667a3edd172ba0c2cb11ddb02b280b0653baaa0a003729e5d195fb022b9d1f80；人工集7f0e8e8832a30e948fad318e881507e2d5b111b57f1e5e5328d8e4d82753125b。读取许可不是代用户点击接受或改变账号授权。

资料：
- https://github.com/SORRY-Bench/sorry-bench
- https://arxiv.org/html/2406.14598v2
- https://huggingface.co/datasets/sorry-bench/sorry-bench-202406
- https://huggingface.co/datasets/sorry-bench/sorry-bench-human-judgment-202406
- https://huggingface.co/sorry-bench/ft-mistral-7b-instruct-v0.2-sorry-bench-202406
- https://github.com/SORRY-Bench/sorry-bench/blob/main/gen_judgment_safety_vllm.py
- https://github.com/SORRY-Bench/sorry-bench/blob/main/data/sorry_bench/mutate/decode.py

下一步等待版本/判读口径确认和已授权访问，随后本地数行/类别、固定ID/SHA、执行三判官meta-evaluation与重叠审计。不能在这些事项未完成时声称已冻结完整SORRY执行协议。
