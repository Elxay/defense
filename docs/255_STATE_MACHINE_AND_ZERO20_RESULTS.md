# 255 · State machine and completed checks

The search-after-read and zero20 fallback addendum was frozen at 2026-11-07 09:47:04.607644 UTC and pushed in 7eeca33 before zero20 testing. SHA-256 `e8bac5c48c19e843d9109301aae298fcee54c42d073b575f0886df0da7f7fb8a`.

1. Wait for all 2,000 official alpha0 rows and both innet GPU2/3 leases. Summarize generation counts, v2 refusals, empty outputs, and retokenized >=2390 proxy. Freeze the summary manifest. Missing rows or signature errors stop this stage and retain completed files.
2. Run the fixed zero20 sample on GPU2 while retaining the two-card lease. Freeze its result and file-hash manifest. Twenty matches retain the native baseline. Any mismatch selects full zero-vector regeneration on GPU2/3, preserving superseded originals. Activate a regenerated baseline only after all 2,000 signed files exist. Freeze the active file manifest before judging.
3. Hold both cards for the 20-reference backend gate, then top-one/top-two/random200. Gate failure stops progression. Hash completed sensitivity summaries before advancing. This completed successfully by 11:23:45 UTC.
4. Generate public refusal alpha0 using matched batch-8, 120-token settings. Preserve complete batch checkpoints, and freeze the output manifest on completion.
5. Generate each harmful condition in the frozen interleaved order, then score it before advancing. Hash each generation and score manifest. A failed worker leaves signed checkpoints for resume; signature and judge-gate failures stop the stage.
6. A completed or cutoff PAIR search freezes its prompt-prefix manifest. The innet queue yields at a row/batch boundary and releases its leases for canonical PAIR-500 evaluation. The canonical queue checks its own baseline gate before the remaining conditions. This plan uses no node01-produced WJB condition outputs.

The native baseline completed 2,000/2,000 rows. v2 refusals are 636/2,000 (31.8%), empty outputs zero, and retokenized length >=2390 occurs in 21/2,000 (1.05%). These are generation and refusal/proxy statistics, not harmfulness ASR. Native summary SHA-256 `eb05b337e9f269fe2b6f3f05693464e5296af5f3ecf5d431c1301b26b662b57b`.

The zero20 rerun is byte-identical on 20/20 rows. All twenty are negative under both the >=2390 proxy and the exact 2400-token cap. There are no cap-positive calibration cases, so cap-hit sensitivity cannot be estimated. Nineteen raw-token-minus-retokenized differences are one token, and one is two tokens. The native baseline is active, with no superseding regeneration. Zero20 summary SHA-256 `e4dae79b49ef9766d6f7c0e528db8d5c8d7325f70456d2df803cccc93f0c905b`.

The PAIR first30 summary was read at 2026-11-07 11:30:31.177693 UTC (20:30:31 JST), SHA-256 `cd3c13c484b751108ba088034a8a54bacd82374815efcd64a8b3f67818d56bfa`. All 30 generation seconds have mean 355.16017 and sample SD 116.23281. The 20 post-pilot rows have mean 360.32028 and SD 120.66973. Raw selected-length telemetry covers 20 rows, with 15 cap hits. Decoded/re-tokenized length is >=512 for 23/30. Four rows have a zero-tier winning score, whose exact all-40-refused status is unknown. Fallback count is zero.

At 11:30:32 UTC the search worker PID2024810 is running on node01 GPU1/2 at 42/500, heartbeat age 3.5s. Recovery attempts remain zero. Public refusal alpha0 is running on innet GPU2/3, PIDs2963674/2963676 at 864/1001 and 866/978, about 0.46 seconds per row. No defense output content was read for this report.
