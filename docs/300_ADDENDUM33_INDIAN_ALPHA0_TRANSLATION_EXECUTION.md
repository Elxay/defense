# 追加33：Indian alpha0闸门优先与B1翻译执行

按用户本轮闸门优先的安排，六个Indian alpha0先做翻译/SORRY，作为是否花费非零生成成本的前置；这不是读取非零效果。随后T1中文/法语全六条件保持同一B1及Unicode+langdetect路径。印度三语非零仍锁定，T2只按日历记录，不中断作业。

B1批工程回退已确定，原始回复保留；固定前20条工程参考在各使用的卡重新翻译，逐字节及状态全一致才放行。CUDA_VISIBLE_DEVICES映射后固定cuda:0，禁止cuda:物理号。inode/目录别名不能造成重复取行。当前按格互斥分工，不同时向两张卡发同一格；每行原子文件核源生成哈希。

每行自首条起保存translation_status、failure_type、输入/输出token数（透传均0，另存原文SHA）、原始/处理后SHA、主判INVALID、站点/卡UUID/plan。翻译溢出、截断、非英语验证失败及异常保留失败原因，不删行、不重采样。有效行仍用原官方SORRY模板/解析器/vLLM0.6.6.post1。上游翻译失败直接缓存INVALID，不能把空字符串送入判官并当成不履行。

每个alpha0格440条完整写缓存后，只按SORRY读25%门（110/440），逐字段INVALID ID和上下界落盘。CF非零效果不由此读取，原CF闸门不重选。node01 GPU0先做B1跨卡20工程门；Gemma门未完成之前不据此声称Gemma准入或运行TA全量。innet GPU3先做Llama ml alpha0，后续格依优先级处理。全部日志首行与EXIT沿统一包装。
