# WJB official evaluation: frozen four-condition read

Generated UTC: 2026-11-08T01:25:35.486602+00:00

Analysis plan SHA256: `8128efd0504f62649b6e0f85471331580f45120d27bcdbc9da11f5129e93625f`.
Baseline table source: `results/audit/pair500/public255/alpha0_reference_directional.json` SHA256 `047db362c25cc4017b163bf1ccbf419f0d6bfad20a74f76970153eac93885a72`.
Four-condition source: `results/audit/pair500/public255/four_condition_analysis.json` SHA256 `74bd73a25322f592e92321efc99412bfcfff4331416500c602cd74e7d62d0c2e`.

| Layer | n | Top1 yes | Top2 yes | yes-to-no | no-to-yes | both-no | both-yes |
|---|---:|---:|---:|---:|---:|---:|---:|
| all | 2000 | 993 | 304 | 711 | 22 | 985 | 282 |
| high | 1689 | 874 | 251 | 628 | 5 | 810 | 246 |
| low | 311 | 119 | 53 | 83 | 17 | 175 | 36 |
| small_margin | 270 | 103 | 52 | 68 | 17 | 150 | 35 |

Random-reference 200 rows: top1 mean pair-normalized P(Yes) 52.2868%, random mean 1.9261%. Greedy-label ASR is separately 101/200 versus 2/200. These are distinct statistics.

| Reference/layer | Learned-minus-random pp | Row bootstrap95 | Assigned-behavior bootstrap95 |
|---|---:|---|---|
| top1/all | -22.1750 | [-24.025, -20.375] | [-24.365186369543842, -19.999877330716387] |
| top1/high | -23.3866 | [-25.400384843102426, -21.40245707519242] | [-25.679715718843102, -21.16867135715088] |
| top1/low | -15.5949 | [-19.774919614147908, -11.571543408360114] | [-20.89000893018629, -10.97953115733288] |

pending top2 and strata sensitivity; abstract unchanged

All rows are retained. Top1 assigned groups are inferred and imperfect. Item/group bootstrap intervals condition on two learned seeds and two fixed random directions; they are not seed-population intervals. Top2 and Guard sensitivity are post-alpha0 decisions.

The alpha0 top1/top2 and random-reference contrasts establish sensitivity to the supplied behavior. Whether mapping mistakes attenuate or reverse a defense contrast remains untested; sign preservation is not guaranteed. 49.65% lies below the frozen 50% check, which is not validation.

The original docs230 independent-test and second-model-alpha-scan clause remains unchanged. The methods-only abstract remains unchanged.
