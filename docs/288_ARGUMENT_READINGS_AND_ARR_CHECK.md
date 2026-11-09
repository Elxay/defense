# Narrative argument, readings and official submission requirements

UTC 2026-11-09T10:09:12.922100+00:00. Editorial revision after completed WJB/public reads; PAIR-500 labels remain unopened. Numeric prose macros come from argument_numeric_receipt.json, SHA256 39dd2242eaca8e8fac6993bbf7ca2b11616ae6a430ee5308d0cf9dc157994d53. Harmful additional19--23pp is learned-minus-random. Public9pp and0.4pp in the introduction are explicitly learned-minus-alpha0; OR is5.883pp against alpha0 and3.950pp against random. Most-refusal association is post-hoc and is not causal attribution. The abstract remains method-only until the all13/two-judge PAIR read.

## Introduction and contributions

Activation steering is often proposed as a lightweight way to alter refusal behavior: a vector is added to the residual stream, and safety is assessed through the resulting automated attack success rate (ASR) . A lower ASR alone does not establish a better defense. In our own pipeline, verdicts depend on output truncation and the behavior text supplied to the judge, while decoding paths and retraining variation also change measured outcomes. Without a benign control, additional refusals can look like a safety improvement. We ask how much of a learned vector's ASR reduction survives two controls: norm-matched random vectors and benign requests carrying comparable adversarial packaging.

We study one learned vector added once at the final prompt token of Llama-3.1-8B-Instruct. On a success-filtered prompt set, norm-matched random vectors already lower judged ASR by up to 21 percentage points; on the official WildJailbreak evaluation, their decreases are about 1--5 points. Learned vectors lower ASR a further 19--23 points relative to those random directions under our two model judges. A post-hoc decomposition associates most of this additional decrease with added refusals. Relative to the unmodified model, benign refusal rises by about 9 points on wrapped WildJailbreak requests, versus 0.4 points on XSTest safe, where the interval includes zero. Paired original--wrapper tests reproduce a wrapper-associated refusal gap. These observations motivate reporting a harmfulness score together with its random reference, benign cost, and measurement protocol.

The scope is this single-position, prefill-only additive intervention. The historical selection set is distinguished from subsequent fixed-prompt evaluations, and rows with prior training or selection exposure remain marked rather than removed. Qwen2.5-7B-Instruct currently supplies supplementary zero-training baselines; model ports without completed evaluations do not increase the model count in our claims. We make three contributions:

- **Controls.** Norm-matched random vectors account for up to 21 judged-ASR points on success-filtered prompts but at most about 5 on the official WildJailbreak evaluation. Learned vectors exceed that sampled reference by 19--23 points there under both judges.
- **Costs.** We pair the harmfulness score with public and wrapper-paired benign refusal tests. In a post-hoc decomposition, most of the additional ASR decrease accompanies added refusals, and benign costs are concentrated on wrapped requests in the paired tests.
- **Measurement.** We measure how truncation, baseline-set mismatch, decoding path, refusal rules, and retraining variation shift reported quantities in our own pipeline, and distill a reporting checklist.



## Current directory

1 Introduction; 2 Related Work; 3 Experimental Setup (models/intervention, samples/exposure, outcomes/judges, statistics/log chronology); 4 Results (random controls, refusal association, wrapper-associated costs, zero-training baselines); 5 Measurement Audit and Reporting Checklist; 6 Limitations; unnumbered Ethical Considerations; references. Appendices retain initialization/decomposition, exposure and closed incomplete data composition, detailed measurement audit, provenance/chronology and auxiliary frontier sensitivity. The duplicate main results4.4 audit was merged into section5. The original eight detailed audit subsections remain in the appendix; the main text has one six-row checklist table and four prose explanations.

## Five required readings: evidence and comparison

The existing docs282 already records the five primary full texts, version identifiers, three-line notes and PDF hashes. This update reopens the following primary method/result/limitation sections, rather than claiming that only one paper had previously been read. No cited effect size is imported as calibration of our output distribution.

**ReFT, v3, §§3--6** https://arxiv.org/html/2404.03592v3
1. It learns representation-dependent low-rank edits with the base weights frozen and specified prompt positions/layers.
2. It informs our setup section; our constant one-position vector is a restricted, differently trained intervention.
3. No direct conflict: task-adaptation performance does not establish jailbreak-defense safety or our random/benign contrasts.

**BiPO, v2, §3.2/Algorithm1, §4.2/Table4 and §4.3** https://arxiv.org/html/2406.00045v2
1. It learns a fixed vector from paired preferences using random positive/negative direction signs and applies steering across tokens.
2. It informs the learned-vector comparison; its safety example uses different data, signs, injection positions and model judge.
3. No numerical replication claim: directional controllability does not contradict our fixed-protocol safety-versus-benign-cost audit.

**Steering Safely or Off a Cliff?, EACL2026, §§3--7 and Limitations** https://aclanthology.org/2026.eacl-long.268/
1. It evaluates general specificity, related control preservation and robustness under distribution shifts.
2. It informs our paired harmful/benign results and limitations; its over-refusal intervention increases benign compliance.
3. The opposite training direction and different safety metrics preclude a common-mechanism claim; efficacy alone being insufficient is compatible with our framing.

**How Reliable Is Your Jailbreak Judge?, v2, §§3--6** https://arxiv.org/html/2606.25487v2
1. It compares judges on596 human-majority HarmBench validation pairs and separates content-preserving framing tests from a classifier attack.
2. It informs the measurement section and our requirement to distinguish a harmfulness flip from refusal labels.
3. Its corpus, quantization and prompted judges differ; we neither transfer its precision nor apply its proposed numeric correction to WJB.

**An Empirical Measurement of Jailbreaking Evaluators, v1, §§3--7** https://arxiv.org/html/2609.10594v1
1. It compares six evaluators on two human-labeled corpora, including a nonrefusal-selected corpus, with a shared backbone where applicable.
2. It informs our cross-judge and sampling-scope discussion; its StrongReject variant is the rubric judge rather than the trained scorer.
3. Evaluator dependence is compatible with our results; its evaluator ranking does not validate our model labels or transfer across distributions.

**Rogue Scalpel, v2, §§3.2/3.4/5** https://arxiv.org/html/2509.22067v2
The v2 text gives1--13% increased compliance and applies a fixed vector across prompt and generated tokens; §3.4 identifies JailbreakBench. We use a once-only final-prompt intervention and observe random-direction judged-ASR decreases. These are different protocols and input selection, not the same measured phenomenon or an explanation established by our experiments.

## Official ACL/ARR check, read today

Primary pages: https://2027.aclweb.org/calls/main/ ; https://aclrollingreview.org/cfp ; https://aclrollingreview.org/authorchecklist ; https://aclrollingreview.org/responsibleNLPresearch/ .

The current ACL2027 call lists ARR submission on2027-01-04,23:59 UTC-12 (AoE), rather than an assumed deadline. ARR long papers allow8 content pages, with required Limitations and optional Ethical Considerations after the conclusion outside that limit, and unlimited references. The current sources have no conclusion section yet; add a concise evidence-bounded conclusion before Limitations in the complete draft. No compiled page count is asserted: no TeX engine is installed here.

The review PDF and supplements/repository links must be anonymized. The post-2024 preprint rule does not remove review-PDF anonymity; a selected no-nonanonymous-preprint commitment is binding. The Responsible NLP checklist is part of the submission form and needs section pointers or explanations, including artifact licenses, annotation and AI assistance. AI writing/coding/research assistance must be disclosed in the applicable checklist/acknowledgment form, with authors responsible for all claims. The sustainable reviewing policy applies fromOctober2026: a qualified service contributor may cover at most2 submissions and must register within48h after the deadline. This check does not perform account registration or claim service eligibility.

No checked rule requires publishing raw attack material. ID/hash-only release is our disclosed choice, with a reproducibility limitation, not an ACL ban. Ethics text covers attack/steering dual use, no raw attacks/harmful outputs in Git, and WildGuard's Apache-2.0 model-card license plus accepted AI2 Responsible Use Guidelines. Source https://huggingface.co/allenai/wildguard . A model license does not license every underlying dataset.

## Remaining states

The data-composition intervention stays closed incomplete, appendix only. New-model ports are not counted as completed evidence. Model annotation/GPT review remains without human calibration; precise historical annotator snapshots are not reconstructed. The12/10 human-review date and token expiry check remain pending. Methods, measurement audit, dataset scope and limitations can be revised before11/12; results, abstract and numeric contributions receive the locked PAIR update only after admission. No new mechanism claim or PAIR result was added.

Source QA checks input existence, duplicate labels and citation keys. New checklist table is regenerated from paper/data/measurement_checklist.csv. No rebuilt PDF or page-count guarantee is claimed.
