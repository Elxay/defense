# 追加39：GPU1 事件记录、rc=81 让卡成本与重派

（事实记录；不含任何签字或授权声明）

## 1. GPU1 事件（innet GPU1，UUID 11714cb4）

- 时间：2026-11-14 06:40–06:55Z。
- 内容：闸门 B1+B8 与 B4 在 innet GPU1 手动启动（外部卡，未在白名单）。
- 占用：17.9–21.7 GB。
- 数据影响：对全部已处理翻译行扫描 device_uuid，含 11714cb4 的行数 = 0。该事件未产生任何翻译行，无数据污染（闸门作业不写 translation 行）。
- 处置：night/require_gpu.sh 加 UUID 白名单（innet 仅 ef899e48/25c58d52/16fea00b；node01 仅 a1b43a24/51b0921d/dcaca421），GPU1 innet 已置 REFUSE；规则改为"受管卡手动启动须先停队列，否则走队列"。
- 外部项目告知：决定告知；告知文本已备，待联系方式转交。

## 2. rc=81 让卡成本（两个 failed 格）

- llama_translate-ta_s3（node01 GPU2）：05:33 起 → 06:26 rc=75（让卡 yield）→ 06:27 起 → 06:39 rc=75（再让卡）→ 06:39 重试 runner 未出现 → 06:41 rc=81（控制器标 failed，禁止自动重试）。存 142 行。
- llama_translate-mr_s3（node01 GPU0）：04:59 起 → 06:26 rc=75（让卡）→ 06:26 重试 runner 未出现 → 06:28 rc=81。存 104 行。
- 根因：闸门尝试期间让卡（rc=75）+ 控制器 ssh 瞬时故障（重试 runner 未起）。数据无损坏。
- 重派：08:13Z 建两个 supersedes 任务 T2translate37_llama_translate-{ta,mr}_s3（续写；worker 跳过已存行并校验 source_generation_sha256，不覆盖）。已入控制器 ready。

## 3. 编号

本追加编号 39（34 号被占用两次，冲突沿用 ≥39）。
