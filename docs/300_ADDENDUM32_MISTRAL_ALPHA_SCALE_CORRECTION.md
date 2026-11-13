# 追加32：Mistral校准alpha实际缩放修复

仅用源代码和生成元数据诊断：/tmp/mcal_B8.py对各alpha均传V[s]*1.0，而generate_batch_with_injection的alpha参数仅记录元数据，不缩放向量。已完成s3七个alpha的700行回复逐字节相同，rho均约2.3307449；s4/s5已有配对亦700/700相同。不是非单调或目标不可达证据，这批B8不能用于选alpha。

在修复版任何输出前冻结：实际传入vec=alpha*V[s]，alpha参数继续仅作元数据；模型、模板、层9、B8、120上限、700行/顺序、三个seed和七点网格均不变。每行写expected/runtime rho和1%容差、new_tokens/EOS/输入ID哈希、完整result与plan哈希。原校准目标、5pp良性上限、WG主/v2并列不变，不加训练步数。main2400批门仍未完成，不冒称主评测放行。

旧B16生成与对应WG目录在deprecated_B16保存；此次B8未缩放目录在deprecated_B8_unscaled保存。隔离前后逐文件SHA核验，不删旧数据。只停止已核身份的本项目旧Mcal进程，保留最新原子检查点；此为无效任务修复，非日历截止动作，不触碰其他项目。

修复版先对alpha0、s3真alpha1各选前20行，以完整B8批比较历史参考，逐字节通过后才全22条件重生成。旧alpha0和真alpha1仅作工程参考，不把其他错误alpha当新数据。新输出不混入旧B16/B8或其WG分数，完成、评分与选择另记，当前不读取选择统计。
