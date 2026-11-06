# 259 — 接手核对与本轮更正

本轮没有读取s5–s7的WJB逐条生成文本或判分效果；只检查落盘数、完成日志、脚本及运行时元数据。两份实际执行脚本只改项目路径与模型缓存路径；模型snapshot及common.py/清单SHA相同。innet输出host字面值仍是node01，保留原字节，实际主机由执行记录与旁证给出。

node01/night/wjb_treat.py sha256=357a1b76337e7b0f03d663c6bc1e80fc76f1acbbd6a5a3ebd23a9e2906f27f55

innet/night/wjb_treat_innet.py sha256=98e955990fa1ab7edc52c9b723b372b22d6973a7ee2b07b1b3443a228c34a61e

```diff
--- node01/night/wjb_treat.py
+++ innet/night/wjb_treat_innet.py
@@ -4,8 +4,8 @@
 from gen.common import generate_with_injection
 from transformers import AutoTokenizer, AutoModelForCausalLM
 import numpy as np, torch
-R="/home/dell/Def"; DEV=sys.argv[1]; SEED=int(sys.argv[2]); ALPHA=float(sys.argv[3]); TAG=sys.argv[4]
-SNAP=glob.glob("/data/ray/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/*")[0]
+R="/data/HZX/Def"; DEV=sys.argv[1]; SEED=int(sys.argv[2]); ALPHA=float(sys.argv[3]); TAG=sys.argv[4]
+SNAP=glob.glob("/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/*")[0]
 tok=AutoTokenizer.from_pretrained(SNAP)
 mdl=AutoModelForCausalLM.from_pretrained(SNAP,torch_dtype=torch.bfloat16,device_map={"":DEV}).eval()
 v=np.load(f'{R}/results/audit/runs/block10_keep60_s{SEED}/v.npy').astype('float32'); v=v/np.linalg.norm(v)*(5.21*ALPHA)
```

## 当前结果与修订

- WJB58条逐行范围与s3/s4未命中全文读数：260_WJB_FLIP_REVIEW.md。类别是GPT模型标签，人工类别留空。
- cosine先前换了口径：原近参考五对删除后为+6.62pp，[3.83,9.76]，不是+6.97；后者是同一对内部cosine最高五对的post-hoc诊断。0.856不违反原跨参考/跨其他pair的阈值定义。
- 两条vanilla拒答形式属实，249682基线已是知识性非回答，说明“已答”只可作v2操作定义；主分析不按处理结果删两对。8对均因α0单侧v2命中（4van/4adv）。
- 历史12条仅确认3条改判、9条未知；后续A_replace ord:13补历史标签无来源。规则选中项与全文模型拒答标签匹配6/12，按条件只写5/5、1/3、0/4，不称真值精度或推广排序。
- Llama B400项配对与两组30条尾部已于21:13 JST完成，保留46–49/388操作范围，满足22:30时间条件；5.3仍无跨模型绝对过拒比较。
- Qwen Guard0.2组合行已核：默认40→9，A_replace26→14（均/70），仅输出输入协议不变；仅描述长度/形式可能敏感，不写机制。
- 自身旧稿错误已更正：88.6%来自vLLM62/70且1INVALID，HF63/70应90.0%；随机下降4–21pp。24/93可由混合vLLM基线与8个HF init-only方向复现，非11方向同HF主表。

## 关键工件哈希

| 文件 | sha256 |
|---|---|
| results/audit/handoff_round5/wjb_s0_flips58.csv | 0a215262ac3d2b5ee7b1f8ebd50fcbd5dd0d41fe405ccf1b1ea8a4252af9ec70 |
| results/audit/handoff_round5/wjb_s3_unhit15.csv | f3dd158aa1c34208072ab831207843716eb58f0e8df4fe8a0a090930979e9c7c |
| results/audit/handoff_round5/wjb_s4_unhit12.csv | 0fbf5e483ed672ba7484f89f6f1a69a9eb18e3b72ff9bd3626c07195001c6909 |
| results/audit/handoff_round5/handoff12_reconciled.csv | 67306e15e5fefcc9304e6325592775364f4dc536415113ab94aba27e352e0009 |
| results/audit/handoff_round5/llama_b_paired400.csv | 669a41545fe9a103ee2cb16bc9ef3887d6b31f8e2eefec0ea01c4b28c933f8cb |
| results/audit/handoff_round5/llama_tail60_review.json | 0804281a810aee5cf784012c6183ae4002467742dafcc3e52f13d1d25f69ef5f |
| results/audit/handoff_round5/qwen_guard_A_replace_check.json | 91dec8663ba37f45092c908fdd1bb493166df10bca1a730d1fa4eebf81890afd |
| results/audit/handoff_round5/cosine_and_exclusions.json | e5e3aa67bb86366772b4e409589e428d24f023e5472af3717e5e04a34d6faa90 |
| results/audit/handoff_round5/vanilla_two_review.json | 366b587b272368ffe36754cb9de1a063e45d5871712a74a014801d4a5961e75c |
| results/audit/handoff_round5/val70_source_reconciliation.json | 30a548ec0d7e4a684e9bee0754e0b64134740aeca8e6fe3e20b34864a748c59d |
| results/audit/handoff_round5/script_provenance.json | 304b5f299fbeab92505fe3d62c2106c716ae5778e1394b3a655895517cc75946 |
| results/audit/handoff_round5/generation_snapshot.json | 6db99cd70ef71cabef415f25dab679363def68889ff4695a68f89d1fe1fa76f7 |

未来判分控制器已登记，等待三份生成全部300且DONE日志齐全后同步；仅在innet物理GPU2/3均通过原wait_gpu（使用≤2000MiB）时加载判官，CUDA隔离0/1，先做固定20条核对，再判三seed，全部完成后一次性应用冻结addendum7。判据为点估计≥10pp且区间排除0，至少4/5，s0不计；不改为下界超过10。Bootstrap条件于现有两个随机方向，不宣称方向稳健。

## 运行快照 2026-11-06T22:13:26.338489+09:00

| 条件 | 主机 | PID | GPU | 落盘数 | 首25条秒/条 | 状态/预计JST |
|---|---|---|---|---|---|---|
| s5 | node01 | 1789174 | 2 | 250/300 | 25.544 | 预计2026-11-06T22:24:30.482489+09:00 至 2026-11-06T22:34:43.538489+09:00 |
| s6 | innet | 1329826 | 2 | 300/300 | 11.832 | 完成于2026-11-06T21:40:14.024557+09:00 |
| s7 | innet | 1329827 | 3 | 300/300 | 10.216 | 完成于2026-11-06T21:43:49.546560+09:00 |

计时不含模型加载，实际每25条写盘；进度可能落后内存中生成0–24条，预计区间仅按首25条速度外推，不是置信区间，也不保证后续输出长度相同。快照sha256=ba92520b5aa3bff11c485425901a827a7de391d17bed2609fe845875645da320。等待控制器PID1382570不占GPU。
