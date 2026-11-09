# Argument-first manuscript revision

UTC 2026-11-09T08:58:47.113899+00:00. User-requested editorial change after the completed WJB/public reads, with PAIR outcomes still unread. The central argument is that a lower judged ASR alone does not establish a better defense; random controls and wrapper-paired benign tests change its interpretation. This is a claim about this audited protocol, not a universal mechanism result.

The placeholder-heavy docs284 abstract template is historical and is no longer to be filled. Main.tex retains its interim method-only abstract; the narrative abstract is written last after the locked PAIR read, using a few checked numeric findings and the contrast definitions from the result tables. No new abstract result sentence or PAIR number was inserted. The prose candidates21, about5,19--23 and public9/6/0 are independently recomputed in prose_numeric_candidates_check.json. The public9/6/0 contrast is learned-minus-alpha0, whereas the harmful additional19--23 is learned-minus-random; OR's learned-minus-random value is3.95 rather than5.88. Small uncertain XSTest change is not equivalence. Refusal decomposition is post-hoc and descriptive.

## Current introduction opening

A lower automated attack success rate (ASR) does not by itself establish a better jailbreak defense. The same score can fall because an intervention resists harmful requests, because a perturbation disrupts responses, or because the evaluator reacts to changes in wording. For activation steering, a safety claim therefore needs two comparisons: learned directions against norm-matched random directions, and harmful requests against benign requests with comparable adversarial packaging.

## Contributions

- **Random controls change the reference.** We measure the score changes produced by norm-matched random directions and the learned-vector difference beyond that reference, separating success-filtered attacks from the WildJailbreak evaluations.
- **Safety scores and refusal costs are evaluated together.** We relate judge-score changes to refusal labels in a post-hoc decomposition, report public benign costs, and reproduce a wrapper-associated refusal gap on paired benign samples. These are descriptive findings, not evidence that the vector identifies a particular harmful intent or style mechanism.
- **Measurement choices are part of the result.** We document how baseline membership, refusal rules, reading scope, truncation, decoding paths, and retraining variation change measurements in our own pipeline, and provide a reporting checklist.
- **Zero-training alternatives remain explicit.** We evaluate system prompts and output filtering alongside steering, preserving their generation paths, thresholds, and model-annotation limits instead of inferring a calibrated ranking from ASR alone.

## Actual manuscript directory

```text
1. Introduction
2. Related Work
3. Experimental Setup
   3.1 Models and intervention
   3.2 Prompt samples and historical use
   3.3 Outcomes and model judges
   3.4 Statistics and versioned decisions
4. Results
   4.1 Random controls change the interpretation of lower ASR
   4.2 The additional decline accompanies more refusals
   4.3 Benign costs concentrate on wrapped requests
   4.4 Evaluation choices move the reported quantities
   4.5 Positioning zero-training baselines
5. Evaluation Pitfalls
   5.1 Baseline membership and backend alignment
   5.2 Reading scope, nonanswers, and truncation
   5.3 Judge flips and refusal labels
   5.4 Classifier position and threshold convention
   5.5 Interpolation and unsupported draws
   5.6 Training repeat variation and decoding amplification
   5.7 Missing generation metadata
   5.8 Restart provenance
6. Limitations
References
Appendix A. Initialization and residual decomposition
Appendix B. Exposure strata and closed data-composition evaluation
Appendix C. Provenance and protocol chronology
Appendix D. Auxiliary frontier sensitivity
```

The introduction now has four paragraphs followed by its contribution list. The result chapter is ordered by findings, with the initialization decomposition and incomplete data-composition experiment moved to appendices. Existing numerical statements/tables are preserved, with the primary scope and caveats retained. The editor checked input-file existence and duplicate labels; no TeX engine is installed in the environment, so no rebuilt PDF is claimed.

The supplied judge-reliability example was checked against the primary arXiv abstract/metadata: https://arxiv.org/abs/2606.25487 (v2). It is used here as an organizational reference, without adding unverified full-text numerical claims to the manuscript.

## Operational clarifications retained

The original1144 contextual input audit is88 prompts x13 conditions, not all1300. Addendum12 records the full1300 audit, overflow fallback and all13 admission. The old midpoint +/-200 indices imply400 shared tokens; the frozen contingency and CPU tests make that explicit. Current PAIR numeric sources are not hot-edited and no chunked GPU inference is claimed.

The render audit verifies4000/4000 old input hashes against current Llama rendering: the knowledge/date header stays, and the custom system body follows it. This is not Qwen's four replace/append conditions. Public batch8/120token and harmful single-row/2400token A/B rates remain separate. Original227 prompt bodies are unchanged; effective system/header hashes are in the companion addendum.

Today's18:00 GPU0 cutoff is superseded by the user's later authorization, addendum13. Old release plans are historical; current authorization runs through today's24:00 JST. Existing processes and admission gates remain protected.
