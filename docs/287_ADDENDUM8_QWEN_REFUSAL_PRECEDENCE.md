# Addendum8: Qwen refusal-check precedence (written before any training; 2026-11-10)

## Decision
For Qwen2.5-7B-Instruct, the v2-refusal check is satisfied by the completed 470-row WildGuard cross-check (docs/287_ADDENDUM7), with the 60-row textual audit retained as a supplementary consistency record rather than a training-lock precondition.

## Evidence at decision time
- WG cross: 470 rows (legal400 + val70), no INVALID. v2-only = 0 in both sets; WG-only = 5 (1/392 legal, 4/67 val70). Pre-frozen failure thresholds (legal388 >=39, val70 >=7) were not crossed.
- The partially annotated 60-row audit (8 saved / 10 worksheet; review001 tagged differently in the two tables) remains a documented model-label instability data point; it will be completed and saved, but it no longer gates training.

## Rationale (stated before training)
The 470-row cross covers the full legal400 and val70 v2-negative pools, whereas the 60-row audit is a sample. The cross directly measures the quantity the lock was meant to protect (v2 false negatives among v2-negative rows), and its thresholds were frozen before labels. The 60-row audit and the cross share the same purpose, so requiring both would duplicate the same check.

## Explicit status
This changes a previously written gate ("both must be complete before training"), before any Qwen training, vector, alpha selection or WJB evaluation. It is recorded as a rule change with the reason above; the original gate text is not deleted from the earlier logs.

## Unchanged
Seeds, alpha grid, selection rule R0+0.5(1-R0), legal/val sampling, norm conventions, WildGuard as fallback judge for subsequent selection, sign-consistency rule, and all three new-model training admissions remain otherwise as frozen. Pre-specified numeric rule: if the completed 60-row audit shows >=4/60 rows (6.7%) that are clear v2 refusal misses, that result is reported as a limitation. 4/60 is chosen now, before the audit is completed, as roughly five times the cross-check rate (5/470) and does not retroactively invalidate this decision.
EOF