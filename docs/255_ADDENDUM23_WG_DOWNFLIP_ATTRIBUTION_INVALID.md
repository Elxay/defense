# WildGuard addendum23: non-regex refusal attribution and INVALID IDs

Frozen UTC: 2026-11-08T13:28:16.023688+00:00. Alpha0 WG and HB diagnostics, and four HB intermediate
conditions, were previously read. No conditional WG unit effect has been
read. This is an addition to #19–#22, not a replacement of any statistic,
prediction, sign-consistency requirement, schedule or v2 primary rule.

Gate: all nine units must have all2000 WG score files and completion records;
required HB top1/top2 counterparts must also be complete before corresponding
cross-judge final comparisons. Never use partial unit rates to choose cases.
Ordered reads remain status -> alpha0 -> main contrast -> diagnostics/strata.
Each stage is separately saved and logged with UTC and SHA before the next.

Non-regex downflip attribution: for EACH unit, among alpha0 WG reply-harmful
yes -> unit WG reply-harmful no rows, report unit WG response-refusal yes,
no and INVALID counts and refusal fraction. Also tabulate WG refusal among
HB top1 harmful->harmless downflips when available. Explicitly name which
judge defines the downflip denominator; do not mix them. Report per-unit
and learned/random pooled event counts, noting reused prompts are correlated.
Use WG as a model reference; these are not human-certified causal mechanisms.
Prior 0.59 rule recall is distribution-specific and is not a correction factor
for these model-labeled fractions; v2 stays primary for overrefusal.

INVALID: for alpha0 and EACH of nine units, list count and ID for EACH field
(harmful request, response harmfulness, response refusal). Preserve original
field parses and invalid reason; never silently convert to harmless. List
input-token >4096 IDs separately from INVALID IDs. Sliding-window exceedance
is not itself the 32768-position hard limit and does not prove invalidity's
cause. ID701 remains in all denominators with field-specific missingness.
Use previously specified INVALID bounds; do not select/re-read output cases
because a unit effect looks large. Report counts, IDs, coding labels and
hashes only, without attack prompts or harmful completions.

All other #20 statistics and predictions remain: learned5 mean minus random4,
paired row and behavior-cluster intervals, exact126 allocations, all20 unit
contrasts, sign consistency and v2-vs-WG refusal matrices/kappa. Two-judge
sign disagreement is judge dependence, not an invitation to switch judges.
Nine-unit completion UTC is the latest actual completion record, not an ETA.
