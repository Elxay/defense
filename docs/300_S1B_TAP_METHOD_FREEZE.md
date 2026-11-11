# S1b-TAP 分方法冻结

冻结UTC：2026-11-11T06:30:50.113792+00:00。正式TAP输出0。

实际读取HarmBench TAP源码控制器、两阶段prune、AttackLM、TargetLM、OpenSourceJudge含on-topic和score解析；YAML默认1树、depth10、width10、branch4、retry20、500/150/5、cutoff10（不取Python未覆盖默认7）。只换本地角色/原生模板/传输，角色Qwen3-8B一份权重，目标alpha0；外层8行为独立，prune用每行为独立种子的numpy facade，源码函数不改。源码剪枝fallback/错误保留，不自造提示。

实际门：同实例无补丁对零钩子20字节；8无害行为、两种顺序，工程面板2树2层branch2/width4/cutoff11，比较会话归属和调用结构，不把面板当正式负载。门过后同固定10行计时并保留；每行为1个最高源码评分提示，首次严格提升更新、平分保持先遇到的；任一评分>=10在本层结束后早停。全部候选/提示私有。

成本按实际双卡窗口一次计费，冷启动另列；不读主判官效应，六格未齐不选档。配置SHA d8eb2c4ad74f1a261d1f7b57e74a35d918fd8350e57ceadbb772be2a374520f0。
