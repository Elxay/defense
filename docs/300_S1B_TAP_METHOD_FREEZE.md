# S1b-TAP 分方法冻结

冻结UTC：2026-11-11T06:30:50.113792+00:00。正式TAP输出0。

实际读取HarmBench TAP源码控制器、两阶段prune、AttackLM、TargetLM、OpenSourceJudge含on-topic和score解析；YAML默认1树、depth10、width10、branch4、retry20、500/150/5、cutoff10（不取Python未覆盖默认7）。只换本地角色/原生模板/传输，角色Qwen3-8B一份权重，目标alpha0；外层8行为独立，prune用每行为独立种子的numpy facade，源码函数不改。源码剪枝fallback/错误保留，不自造提示。

实际门：同实例无补丁对零钩子20字节；8无害行为、两种顺序，工程面板2树2层branch2/width4/cutoff11，比较会话归属和调用结构，不把面板当正式负载。门过后同固定10行计时并保留；每行为1个最高源码评分提示，首次严格提升更新、平分保持先遇到的；任一评分>=10在本层结束后早停。全部候选/提示私有。

成本按实际双卡窗口一次计费，冷启动另列；不读主判官效应，六格未齐不选档。配置SHA d8eb2c4ad74f1a261d1f7b57e74a35d918fd8350e57ceadbb772be2a374520f0。

路径修复UTC 2026-11-11T07:04:35.747808+00:00：首工程门在调用on-topic时NameError，原因是适配器common/system_prompts残留PAIR路径；正式TAP行0。保留v1/失败日志，v2改为TAP路径并要求所有AST提取文件在冻结清单，6个所需函数CPU命名空间检查过。算法、YAML和工程门标准不改，完整重做零20与8行为两顺序。v2配置SHA b6929695e736598cc3ec2a1f1e6ddfd39a212db85568cf3520c66e7da5914eea。

执行前路径契约UTC 2026-11-11T07:05:59.821794+00:00：v2尚未启动，静态检查发现pilot门依赖仍用旧根目录；保持v2，v3统一实际gate输出和pilot依赖，基于AST表达式的路径契约fixture已过。原失败的v1门保持不变，正式TAP仍0行。配置SHA 9263e007af07c253f631c21236f92f3df14be2a6835e9172862c50f98e48b593。

方法调用契约修复UTC 2026-11-11T07:46:56.071684+00:00：v3工程门执行到调用计数断言，仍误用PAIR每2步scorer2次；TAP源码每层topic与rating各1次，应为4次。v4按源码公式depth/2depth/depth×branch至×retry验证，并在断言前落盘所有实际计数，双顺序结构相等要求不变，不改算法/超参或放宽标签线。v3失败保留，正式TAP行仍0。配置SHA d66388567ea3659fba2657c5b6cc6df2c50f68b771c39eea70b5baac318916e2。
