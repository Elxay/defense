# 255 · Refusal model audit and public alpha0 counts

The substantive mapped judge reading is deferred until November 8 at 08:00 JST. Only stage metadata has been inspected. Scoring completion UTC is 2026-11-07 11:23:44.248564. Automated aggregation already read classifier files. Reads by other people are not independently audited.

The GPT/Codex assistant read the 80 full stored outputs without cohort or judge labels displayed. Labels are model annotations without human calibration.

| v2 sample | R | RA | W | C |
|---|---:|---:|---:|---:|
| positive | 39 | 1 | 0 | 0 |
| negative | 0 | 0 | 23 | 17 |

R means refusal, RA refusal plus alternative, W substantive response with warning, C direct or creative response. Refusal labels do not indicate harmfulness. Precision against this model review is 40/40, Wilson 95% interval 91.2–100%. The v2-negative sample has 0/40 explicit refusals, Wilson interval 0–8.8%. One negative is truncation-uncertain. The population-weighted recall point estimate is 100%, but cannot establish perfect recall. Counting that uncertain negative as a missed refusal changes the point estimate to about 94.9%. This 2400-token harmful-output audit does not validate recall for 120-token public benign outputs.

| Dataset | Completed/planned | v2 | v2 union saved v3 | V_b |
|---|---:|---:|---:|---:|
| xstest_safe | 250/250 | 17 | 17 | 17 |
| xstest_unsafe | 200/200 | 192 | 192 | 192 |
| or_hard | 1319/1319 | 374 | 377 | 374 |
| wildjailbreak_benign | 210/210 | 3 | 3 | 3 |

All four datasets have 100% coverage. XSTest unsafe stays outside benign over-refusal counts. Keep60-unseen denominators are 238, 200, 1301 and 210 respectively. Unseen v2 counts are 17, 192, 373 and 3. OR-Bench-Hard unseen union count is 376. V_b is the previously reconstructed implementation, not a newly calibrated classifier.

Sampling metadata SHA-256 f532a409fcb41966872b4ad54c05eaf49e29f9603a5ffbfa31941c32c42088a7.
Label table SHA-256 4df1755760234bbda036475b93e3f4351ffc1966cfbcef2d8c595e4fe98dad32.
Public-rule summary SHA-256 ef5cfb7198ba848544787eee07162c876712c5e40b8a654fd173576a3768a8be.
