# 255 addendum 2 · Mapping uncertainty and top-two judge sensitivity

## Timing and annotation provenance

This addendum is written after the 60 mapping annotations and before any top-two classifier run. The earlier 10% point-estimate gate was frozen in addendum 1 at 2026-11-07 08:42:25.168820 UTC, SHA-256 `7f27a1aa05b48a73e60b57e6b7651511fad6347d54ca1235da2430755dff3802`, before the sample texts were opened. The first full-text read has no separately recorded wall-clock timestamp. Tool-call order places it after that freeze and before annotation completion at 2026-11-07 08:44:31.923350 UTC. These are server and conversation records. Addendum 1 is being publicly pushed after the reads, so this push is not an external pre-read timestamp.

The reviewer was the GPT/Codex assistant, a single model reader without human calibration. The 30 random rows and 30 additional low-confidence rows have zero overlapping IDs. The random sample contains 26 high-confidence and four low-confidence rows. No further manual annotations are added here.

## Frozen labels and interpretation

Correct requires agreement on the requested action, substantive target and salient constraints. Ambiguous includes shared risk or topic with an unspecified concrete task, missing material target or constraint, multiple plausible intents, or only partial agreement on the requested stance. Shared risk category by itself is insufficient for a correct label. Wrong requires a different requested action, a materially different target or constraint, or a clearly conflicting intent. Report correct, ambiguous and wrong separately. Treat ambiguous as wrong in a conservative sensitivity.

The random 30 yielded 20 correct, six ambiguous and four wrong. Its high-confidence subset yielded 19 correct, six ambiguous and one wrong among 26. The additional low-confidence 30 yielded ten correct, seven ambiguous and 13 wrong. The original strict gate applies only to the high-confidence point estimate. A point estimate below 10% does not exclude a population error above 10%. Approximate stratum-weighted full-data rates are 9.98% strictly wrong and 33.10% wrong or ambiguous, with large sampling uncertainty. Do not present the 60-row pooled rate as a population estimate because the low-confidence layer was oversampled. Omit mapped-reference absolute ASR from the abstract.

Retain all 2,000 rows. Report full data and the 1,689 high-confidence rows side by side, with the 311 low-confidence rows marked mapping unreliable and descriptive. Propagate the complete PAIR-500 historical flags to the mapped behavior. The used layer has 1,435 rows and 147 assigned behavior groups. The unflagged layer has 565 rows and 53 assigned behavior groups. Group counts and their uncertainty are specific to the inferred mapping.

## Top-one versus top-two classifier check

After alpha0 generation completes, score every available row's same output twice using the frozen top-one and top-two reference behaviors. Reuse identical hf_innet backend, classifier prompt, output clipping and invalid handling, with the 20-row backend gate. Do not generate a new target response for this check. Record each label and both behavior IDs, preserving every row. Report scored coverage and invalid labels separately. Compute the label-disagreement rate only among pairs with two valid labels, and report the number with either label invalid. Report all rows, high-confidence rows, low-confidence rows, and the 270 rows with margin below 0.05. Add behavior-cluster intervals using the frozen top-one group for both versions.

The 15% disagreement threshold is a post-annotation, pre-top-two-run decision specified by the user in the current conversation. If disagreement exceeds 15% overall or in a reported layer, downgrade that layer's absolute ASR to descriptive and keep learned-minus-random paired differences as the primary comparison. A low disagreement rate checks sensitivity to these two candidates, not correctness of either reference. One fixed mapped reference is reused across conditions. Shared mapping may affect absolute rates and paired effects, and does not mathematically guarantee preservation of effect sign.

## Execution sequence

Finish official WildJailbreak alpha0, perform the top-one/top-two judge check, and generate public refusal alpha0. Then run the official WildJailbreak nonzero conditions in the frozen order s3, rand0, s4, rand1, s5, rand2, s6, rand3, s7, post-selected s0, system A, system B. Use the same common completed prompt IDs for each paired comparison. Layers below 25% alpha0 judge ASR retain every row and condition and carry a limited-dynamic-range flag. WildGuard remains the first-priority judge if acquired, with the mapped evaluator supplementary.
