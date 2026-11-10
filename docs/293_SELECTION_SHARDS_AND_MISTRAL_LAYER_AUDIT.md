# Selection shards, measured timing and native Mistral norm audit

UTC 2026-11-10T01:35:17.913615+00:00. No Qwen candidate refusal labels/effects read.

## Qwen set and timing
235 is EACH GPU shard for EACH seed×alpha:200legal+35val70. Together400legal+70val=470; exactly388 pre-fixed legal IDs enter the budget. Preserve whole original batch8 composition, including12 legal rows outside the budget mask. Seven alpha points for EACH of3seeds gives21conditions,9870generated/scored rows,9618selection-eligible rows. No downsample to235 and no replacement of388.

Two complete conditions took 12.155 and 12.123 minutes wall-clock across both GPUs. Linear operational projection uses 12.139 minutes/condition and original seed-major order; this is not a confidence interval, excludes interruptions and may change with alpha-dependent lengths.

| Seed3 alpha | completion JST | status |
|---|---|---|
| 0.1 | 10:16 | actual |
| 0.25 | 10:28 | actual |
| 0.5 | 10:40 | projection |
| 0.75 | 10:52 | projection |
| 1 | 11:04 | projection |
| 1.25 | 11:16 | projection |
| 1.5 | 11:28 | projection |

By this projection seed4 finishes2026-11-10 12:53:48, seed5 finishes2026-11-10 14:18:46. WG is pipelined, first470condition finished about10.7min after generation; all-grid readiness is later than generation and not promised at13:30. No shared alpha is chosen before all21matrices are scored. Keep shared-alpha/19new-WG-refusal cap unchanged.

Random-generation seeds remain61000,61001; add61002 only if the two frozen directions' WJB ASR reductions differ by>5pp, under the original287rule. No new seed chosen after outcomes.

## Mistral native layer and position
The first20keep60 IDs were pinned in planSHA a50cf55d162c82991076e2ec87b23ba5cdfb83ebe69d6049709cdd214bd871bf before independent node01GPU1 bf16/SDPA direct-forward audit. Hooks assert model.layers.9 and model.layers.10 OUTPUT, shape[1,prompt_length,4096], B1/unpadded, position=prompt_length−1; last token is [/INST]. No generation/training or injection is involved. Final-state norm is float32CPU L2.

| hook | mean | median | sample SD(ddof1) | min–max |
|---|---:|---:|---:|---|
| layers[9] | 2.625159 | 2.608325 | 0.096017 | 2.495069–2.872589 |
| layers[10] | 2.929912 | 2.942866 | 0.118985 | 2.727111–3.190852 |

All20layer9values equal the original innet measurements exactly; max absolute difference0. All60originalkeep median2.5897282362, rho2.3307554126 remain unchanged. This checks the stated layer/position and neighboring-layer scale; it does not explain cross-model norm scales or prove all implementations equivalent. ResultSHA e440e730244a93574a0c6e33618b4ff6658de23c0d38779a9b489c053ae7fe81.

Actual pinned-tokenizer benign rendering with a system message is:
```text
<s>[INST] You are a helpful assistant.

Reply with the word ready.[/INST]
```
System text is merged ahead of user text within the INST block, separated by two newlines. This is a harmless fixture; no attack text published.

Node01 lacked disk space. Only three retired-project Vicuna .bin REPLICAS were removed after independent hashes matched retained innet originals; receiptSHA b54c34a10b3dacbadbd95c7bafca0eb8c7c232db3dda4019993963bd580e1279. Other files and projects untouched. Mistral standard shards were copied and hash-verified before the probe.

## Loss and execution wording
Qwen keep NLL stayed approximately constant, with seed5 slightly higher; this does not establish benign behavior retention. Attack NLL decreased24–33percent, was still declining near step40, and convergence was not demonstrated. Absolute tokenizer-specific NLL cannot be compared as equivalent thresholds across models. Loss components alone do not establish which term causally drives downstream defense behavior. Original40steps/lr/vectors remain frozen.

Gemma eager attention was insufficient to prevent HybridCache automatic compile; the failed400+14row run remains historical. Addendum12 records the correction and explicit disable_compile execution, with a runtime guard. No earlier rows are relabeled as uncompiled.
