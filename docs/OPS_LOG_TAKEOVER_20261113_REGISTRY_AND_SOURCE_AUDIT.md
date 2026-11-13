# 2026-11-13接手记录：以注册格和来源为准

本地工作区docs只到追加13，服务器docs已到追加29，本轮先读服务器更新。追加21_OPTIONA取代AutoDAN重计时，保持不再运行；不复活旧候补任务。编号21同时存在两个不同主题的文件，引用一律给完整文件名和哈希，不能只写编号。

## 逐项更正

1. “ready_generated下Llama fr/zh alpha0为0”错误：两格各440，且早于接手已存在。规范路径和双重前缀是别名；但ready_generated与_CF20不是同inode。旧格登记legacy，主轮CF格独立。
2. “Llama mr未生成”错误：ready_generated下440，旧node01 B8签名与complete可核。不存在独立plan_B4_mr不等于没有mr的旧通用计划；它用ready_generation_plan.json。
3. “Qwen三语全部未生成/无plan”错误：language_alpha0下每格440，由language_alpha0_execution_plan.json生成。只是原查找没覆盖这个输出布局。
4. “Indian36格仅2格完成”错误：生成层面六个alpha0齐、30非零未生成。翻译、闸门和新home的参考门是另一组状态，不因生成齐全而算通过。
5. 编码v1也已有输出，不能写“v1从未执行”。计数保存在v2计划，全部保留；v2另开目录，supersedes指向v1。

## CPU诊断限定

首次分歧对已改变行给1起算token位置；相同输出无有限位置，不当0。全量为保存文本重分词，原始token串只保存哈希，回编码后能匹配的子集另报。批噪声取现存B16/B8可配对80行，不冒称复现之前11/20。提示面板与语言格不同，只描述，不证明机制或强弱。

## PAIR来源纠正

88档主闸门使用最终选中提示在HF主轮2400上限的独立重放；新增132行的pair220_sorry_gate.py取streams[-1][-1]内部回复，上限150。后者仅3/132的adv_prompt等于selected_prompt，不能叫“最终选中提示的回复”。两档同判官不同输入，不可据此比较成功率；440继续暂停。原始计数保留为诊断，不据此重选提示，也不因此执行1.2卡小时交叉搜索。

88档含10条原计时行，保留b22909be计划；其余78和新增132使用3d683a6a计划。两计划formal配置是否一致由审计JSON直接比较。源码Git路径提交可追溯到25dfde86，blob SHA与冻结worker SHA匹配；按运行起点查HEAD不是工作树无改动证明。220起点以complete减cold/window推算，未冒充精确启动收据。SORRY后端为vLLM0.6.6.post1、bf16、eager；目标是独立HF生成路径，分开记录。

## 执行

追加30与五份计划已提交并推送后才入队。编码v2只做alpha0；四份Indian计划沿旧成员与批次，以旧alpha0为不可改写的参考，先过无钩子/零向量/历史同批20门，再等翻译与SORRY闸门。日志包装保存首行主机/UUID/Git/plan和EXIT。状态脚本的缺根非零退出、坏JSON识别已用工程样例验证。
