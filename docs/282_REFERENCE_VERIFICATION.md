# Reference verification and reading notes

The 11 rows below cover every bibliography entry in the current manuscript. A primary landing page or official proceedings page was opened for each title, ordered author list, and identifier. A general citation describes a method, dataset, or question; it does not transfer the cited work's effect sizes to our setup.

ACL's [2026 statement](https://2026.aclweb.org/acl_statement/) describes verified nonexistent references as grounds for desk rejection, including in accepted camera-ready submissions, and says affected papers follow the regular resubmission process. It assigns authors responsibility for checking both existence and relevance, regardless of whether AI helped. The [ARR guidance](https://aclrollingreview.org/references) also covers mismatched identifiers, substantial author errors, and citations that misrepresent real papers; it distinguishes those issues from minor errors. The [ACL executive resolution of August 3, 2026](https://www.aclweb.org/adminwiki/index.php/ACL_Resolutions) separately confirms that fabricated or hallucinated references are grounds for desk rejection.

Verified UTC: 2026-11-07T04:27:01.010173+00:00.

| # | Title | Ordered authors | Primary source | Scope |
|---:|---|---|---|---|
| 1 | Refusal in Language Models Is Mediated by a Single Direction | Andy Arditi; Oscar Obeso; Aaquib Syed; Daniel Paleka; Nina Panickssery; Wes Gurnee; Neel Nanda | [Primary record](https://arxiv.org/abs/2406.11717) | Primary metadata; general context |
| 2 | The Rogue Scalpel: Activation Steering Compromises LLM Safety | Anton Korznikov; Andrey Galichin; Alexey Dontsov; Oleg Y. Rogov; Ivan Oseledets; Elena Tutubalina | [Primary record](https://arxiv.org/abs/2509.22067v2) | Primary metadata + v2 abstract/§§3.2,5; checked numerical statement |
| 3 | Jailbreaking Black Box Large Language Models in Twenty Queries | Patrick Chao; Alexander Robey; Edgar Dobriban; Hamed Hassani; George J. Pappas; Eric Wong | [Primary record](https://arxiv.org/abs/2310.08419) | Primary metadata; general method |
| 4 | HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal | Mantas Mazeika; Long Phan; Xuwang Yin; Andy Zou; Zifan Wang; Norman Mu; Elham Sakhaee; Nathaniel Li; Steven Basart; Bo Li; David Forsyth; Dan Hendrycks | [Primary record](https://arxiv.org/abs/2402.04249) | Primary metadata; general benchmark |
| 5 | JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models | Patrick Chao; Edoardo Debenedetti; Alexander Robey; Maksym Andriushchenko; Francesco Croce; Vikash Sehwag; Edgar Dobriban; Nicolas Flammarion; George J. Pappas; Florian Tramer; Hamed Hassani; Eric Wong | [Primary record](https://arxiv.org/abs/2404.01318) | Primary metadata; general benchmark |
| 6 | WildTeaming at Scale: From In-the-Wild Jailbreaks to (Adversarially) Safer Language Models | Liwei Jiang; Kavel Rao; Seungju Han; Allyson Ettinger; Faeze Brahman; Sachin Kumar; Niloofar Mireshghallah; Ximing Lu; Maarten Sap; Yejin Choi; Nouha Dziri | [Primary record](https://arxiv.org/abs/2406.18510) | Primary metadata; general dataset |
| 7 | ReFT: Representation Finetuning for Language Models | Zhengxuan Wu; Aryaman Arora; Zheng Wang; Atticus Geiger; Dan Jurafsky; Christopher D. Manning; Christopher Potts | [Primary record](https://arxiv.org/abs/2404.03592) | Primary metadata + full-text main analysis |
| 8 | Personalized Steering of Large Language Models: Versatile Steering Vectors Through Bi-directional Preference Optimization | Yuanpu Cao; Tianrong Zhang; Bochuan Cao; Ziyi Yin; Lu Lin; Fenglong Ma; Jinghui Chen | [Primary record](https://arxiv.org/abs/2406.00045) | Primary metadata + full-text main analysis |
| 9 | Steering Safely or Off a Cliff? Rethinking Specificity and Robustness in Inference-Time Interventions | Navita Goyal; Hal Daumé III | [Primary record](https://aclanthology.org/2026.eacl-long.268/) | Official Anthology + full-text main analysis |
| 10 | How Reliable Is Your Jailbreak Judge? Calibration and Adversarial Robustness of Automated ASR Scoring | Yang Gao | [Primary record](https://arxiv.org/abs/2606.25487v2) | Primary metadata + full-text main analysis |
| 11 | An Empirical Measurement of Jailbreaking Evaluators | Yujie Mu | [Primary record](https://arxiv.org/abs/2609.10594) | Primary metadata + full-text main analysis |

### Five required readings

The five full texts were acquired and the methods, results, and interpretation limits were checked in the primary versions below. Notes describe the setting and how it bears on this manuscript; they do not attest to independent replication of the cited experiments.

**ReFT — [arXiv v3](https://arxiv.org/pdf/2404.03592v3), §§3–6.**
1. The base model is frozen; the intervention is defined by an edit function, token positions, and a layer. LoReFT learns a representation-dependent low-rank edit.
2. Experiments compare parameter-efficient adaptations on reasoning, instruction following, and GLUE; prompt positions and layer choices are tuned.
3. Cite for learned representation intervention design. Neither their utility results nor their edit parameterization transfers to our fixed one-token safety intervention.

**BiPO — [arXiv v2](https://arxiv.org/pdf/2406.00045v2), §3.2 and Algorithm 1; §4.2 and Table 4.**
1. The objective uses paired completions and randomly toggled direction signs, optimizing a fixed activation vector in both directions relative to the base model.
2. Their safety example uses AdvBench and a GCG-suffixed comparison on Llama-2 with a GPT-4 verdict; the training formulation edits all input tokens at the chosen layer.
3. Cite as a contrastive learned-vector method. Their sign reversal, task data, injection positions, and judge differ from our experiment, so do not compare ASRs numerically.

**Steering Safely or Off a Cliff? — [EACL proceedings](https://aclanthology.org/2026.eacl-long.268.pdf), §§3–7 and Limitations.**
1. The paper separates unrelated capabilities, related control behavior, and robustness of those controls under shifts.
2. The over-refusal study pairs pseudo-harmful utility with harmful behavior and jailbreak-prefixed harmful prompts; the faithfulness study applies the same framework to contextual distraction.
3. Cite for testing controls under shifts. Its direction of intervention, safety metrics, and test prompts differ from ours; it does not identify the mechanism of our wrapper-associated gap.

**How Reliable Is Your Jailbreak Judge? — [arXiv v2](https://arxiv.org/html/2606.25487v2), §§3–6 and A.4.**
1. The study uses 596 HarmBench classifier validation examples with human-majority labels and compares a dedicated classifier with three prompted open models.
2. It changes output framing while preserving the harmful body and separately tests a white-box attack on the classifier. The two tests use different populations and are not interchangeable.
3. Cite for score sensitivity and calibration. One validation corpus, quantization, and the judge prompts constrain transfer. Do not use its precision to correct our WJB ASR.

**An Empirical Measurement of Jailbreaking Evaluators — [arXiv v1](https://arxiv.org/html/2609.10594v1), §§3–7.**
1. Six evaluators are compared on two human-labeled corpora; one omits refusals and is therefore a harder, differently selected population.
2. Most evaluators share a prompted backbone; HarmBench uses its dedicated classifier, and StrongReject is tested with its rubric rather than its released trained scorer.
3. Cite for evaluator dependence. English-only samples, evaluator/dataset provenance, and the partial backbone control limit generalization; no scores are imported into our paper.

For the one specific prior numerical claim retained in the manuscript, **Rogue Scalpel v2** gives the 1–13% range in its abstract and §5, and describes injection across prompt and generation tokens in §3.2. The published comparison here cites that exact version; no numerical pooling or common protocol is implied. [Full text](https://arxiv.org/html/2509.22067v2).

Full-text PDF SHA256 (local cache, not published):
- bipo.pdf: 08060a95164b5336045561812c7a166c70abde50bf719bef840ce3602531f11b
- evaluators.pdf: e029175e0447a412054a856d71be55e1f0d27eeda0acb59d84fd1b481bacba6d
- judge.pdf: d3f307798895b507e5a5e065cae716594b5e5405f75bfde7490e77698856ac96
- reft.pdf: 0a05f0a333aaa5a660fcd04ebe773904a880168480990dd5e42ab5e0ec56e32b
- specificity.pdf: f3e901765beb818350dd16fd4bf81e3a22e507a4e546c5cd6e11a984197cff73
