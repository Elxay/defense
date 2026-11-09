# PAIR read chronology and numeric reconciliation

RecordedUTC 2026-11-09T14:34:43.054372+00:00. Per the user's correction, addendum10 enumerates8 steps, not9; all8 were completed. The historical '9' count was an enumeration mistake, not a missing computation. Immutable read receipts remain unchanged.

## End of scoring and start of reading

HB classifier completeUTC 2026-11-09T12:02:50.846128+00:00; MinHash completeUTC 2026-11-09T12:05:01.378555+00:00; WG all13 completeUTC 2026-11-09T12:23:32.611501+00:00. WG's last score-file mtimeUTC 2026-11-09T12:23:29.291918+00:00; the completion marker follows it. All13 routes contain6500 row files each before admission.

The step1 status receipt was savedUTC 2026-11-09T13:32:27.404615+00:00, after both routes were complete. That is a receipt time, not a separately recorded invocation-entry timestamp. Step2 alpha0 receiptUTC 2026-11-09T13:33:02.846427+00:00. The first alpha!=0 numerical access was in step4, after step3 receiptUTC 2026-11-09T13:33:20.785542+00:00 and no later than step4 receiptUTC 2026-11-09T13:35:18.510728+00:00. Do not invent a more precise start time.

Read-scope declaration: within this assistant session and registered audited project code paths, no formal PAIR500 alpha!=0 outcome labels or effects were selected for display or aggregation before step4. Model workers wrote signed per-row caches; coverage/signature audits selected metadata only. This is not an independently proven claim that no unobserved shared-account user ever opened a file. It also does not describe earlier results from other datasets. A cached JSON parsed to select its signature is not claimed never to have contained label bytes in process memory.

The earlier report gave effect values without their already-existing receipt hashes. The source for those values remains step4SHA `a27d3a15a4e6bae2e6997c0b252175805d17fb37bef6112d9b34a40e87bf34e2`; it was not regenerated after the user's request. Subsequent report export and manuscript edits are after that read, not extra prior plan freezes. The entire generation-to-read interval was not a continuous judge window.

## Fixed step4 values, pp (learned minus random)

|Layer|Retained rows / WG complete rows|HB row|WG row|HB behavior equal|WG behavior equal|
|---|---:|---:|---:|---:|---:|
|standard|200 / 197|-33.025000|-26.928934|-33.025000|-26.928934|
|contextual|100 / 100|-31.750000|-27.300000|-30.035842|-24.982079|
|JBB|100 / 100|-21.250000|-15.800000|-21.250000|-15.800000|
|All harmfulness rows|400 / 397|-29.762500|-24.219144|-29.542870|-23.586861|
|HarmBench harm strata|300 / 297|-32.600000|-27.053872|-32.076223|-26.304598|

WG full400 retained-row identification bound is[-24.725,-24.350]pp, whereas its397-row complete-case point is-24.219144pp. These use different denominators and are not interchangeable. The bounds are not a95% CI. The corresponding retained behavior bound is[-24.122922,-23.729221]pp; the378-complete-group point is-23.586861pp. Rows remain in the dataset; no INVALID is silently assigned a safe label. The400 harmfulness rows contain381 source behavior groups; WG complete-case rows contain378. Standard, contextual and JBB remain separate, and100copyright rows are retained under MinHash without entering these harmfulness means.

The current manuscript table is copied verbatim below. No numeric cell or its Python two-decimal formatting was changed during this reconciliation. It is a complete-case table with conditional group-cluster confidence intervals, not a table of full-denominator identified point values. CSV includes both estimands and both sets of CIs. Caption rows300/400 refer to retained applicable rows; WG complete-case denominators are297/397 respectively (standard197, contextual100,JBB100).

```latex
% Generated from primary.csv; complete-case estimates and group-cluster intervals.
\begin{table*}[t]
\centering\small
\begin{tabular}{lrr}
\toprule
Layer & HarmBench judge & WildGuard \\
\midrule
All harmfulness rows (400) & -29.76 [-33.76, -25.80] & -24.22 [-27.97, -20.72] \\
HarmBench harm strata (300) & -32.60 [-37.54, -27.90] & -27.05 [-31.57, -22.70] \\
Standard (200) & -33.02 [-38.83, -27.27] & -26.93 [-32.23, -21.70] \\
Contextual (100) & -31.75 [-40.20, -23.30] & -27.30 [-35.25, -19.34] \\
JBB-Behaviors (100) & -21.25 [-28.35, -14.35] & -15.80 [-21.65, -10.20] \\
\bottomrule
\end{tabular}
\caption{PAIR-style fixed prompts: learned minus random harmfulness rate (pp), with 95\% behavior-cluster intervals conditional on the nine vectors. Rows remain in the dataset. WildGuard estimates for the standard and pooled rows use the 197 and 397 complete nine-unit rows, respectively; full-denominator bounds are reported in the text. Copyright (100 rows) is evaluated separately by MinHash.}
\label{tab:pair500-primary}
\end{table*}
```

CSV SHA256 `54e4796050ddb6815bef0b7af8caa557fe625f0c5ca1f97e661b96e9a00735ab`. Verbatim tableSHA256 `0c254dcc9bbdf116938a85dcf7c1a3239ff1ccc1c263dbd499ee174dfc42f1b1`. Chronology scopeJSON SHA256 `977318936fb20e12376bc6b4ffccb6c094ff16670e48814ed0f9ba9ab6e3f2f0`. The abstract written in the previous pass is an unverified draft; it is not treated as user-approved or finalized. No abstract refinement or new results wording is made during this reconciliation.
