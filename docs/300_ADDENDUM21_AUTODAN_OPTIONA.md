# Addendum21: AutoDAN-Turbo budget decision (A)

## Decision
Option A: do not run AutoDAN-Turbo further. The 8.0354 GPU-hours already spent are counted once in the 600 GPU-hour total. No iteration-cap variant (B) and no cap-512 retiming (C) are launched under the current budget.

## Evidence used (before this decision)
- Third request: 129 complete iterations, median 83.71 s/iteration, no retries; per-component medians 17.85 s (attacker) + 24.67 s (target) + 36.07 s (scoring) + 0.34 s (extraction), which cannot simply be summed.
- Completed requests: ~2,386 s and ~197 s => about 27 and 2 iterations, i.e. successful requests average roughly 14 iterations.
- Projection: successful request ~1,250 s (~0.7 GPU-h) with two cards; a failed request that exhausts the budget ~13,500 s (~7.5 GPU-h); at one-third failure rate the average is ~2.9 GPU-h per request.
- Therefore warm-up of 150 requests would cost ~440 GPU-h and 75 requests ~220 GPU-h, both far above the 150 GPU-h line; an 88-row test per model would also cost ~255 GPU-h because failing rows still burn the iteration budget.
- Cap-512 retiming is not expected to change this: the measured target-response median (472.5 new tokens) is already below 512, and the 36 s scoring stage is unaffected; the per-iteration floor is ~80 s.
- Reducing the iteration cap would be a deviation from the official setting and would have to be pre-registered (option B), still costing ~160 GPU-h before any learning-rate/comparison claims.

## Consequences
- The paper records AutoDAN-Turbo as attempted but not affordable at the official setting; the 8.04 GPU-h is in the total budget table.
- If the remaining budget after all other search cells is large, option B may be reconsidered only via a new frozen addendum before any new output.

## Unchanged
All other search budgets, frozen gates, read order and R1 lock are unchanged.
EOF