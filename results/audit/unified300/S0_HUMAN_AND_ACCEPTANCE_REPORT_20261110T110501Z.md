# S0 human-reference and acceptance review

UTC snapshot: 2026-11-10T11:03:43.362557+00:00; S1 and formal testing remain locked.

## External-human comparison

Matrix is [[human0/model0, human0/model1], [human1/model0, human1/model1]]. Human0=nonfulfillment (3111), human1=fulfillment (1289). Accuracy counts INVALID as incorrect; kappa uses valid pairs. Recall denominators retain INVALID.

| Judge field | Accuracy % | Kappa | Matrix | Recall human0 % | Recall human1 % | INVALID |
|---|---:|---:|---|---:|---:|---:|
| SORRY | 91.70 | 0.808166 | [[2832, 279], [86, 1203]] | 91.03 | 93.33 | 0 |
| HB | 88.86 | 0.711797 | [[3014, 97], [393, 896]] | 96.88 | 69.51 | 0 |
| WG_harmful | 74.89 | 0.383000 | [[2602, 505], [596, 693]] | 83.64 | 53.76 | 4 |
| WG_1_minus_refusal | 80.68 | 0.605834 | [[2292, 815], [31, 1258]] | 73.67 | 97.60 | 4 |

Inverse-refusal accuracy gain=5.795455pp, paired440-instruction95% CI=[3.976704545454547, 7.681818181818178]; kappa gain=0.222834, CI=[0.17960543756929678, 0.2667570144765326]. Selected field=1-minus-Response-refusal. External-human labels used for this choice; no new target-test effect used.

## Response signal strata

Operational model/rule/lexical proxies, not independent four-type semantic annotations. WG is used to define strata, so conditional error profiles do not establish a steering mechanism or transport to new responses.

| Operational type proxy | N | SORRY errors % | HB errors % | WG inverse-refusal errors % | WG harmful errors % |
|---|---:|---:|---:|---:|---:|
| front_anchored_refusal_signal | 1861 | 0.97 | 0.97 | 0.97 | 0.97 |
| WG_only_refusal_signal | 462 | 6.06 | 3.03 | 2.81 | 2.81 |
| warning_nonrefusal_candidate | 616 | 19.48 | 24.84 | 23.70 | 39.77 |
| unwarned_nonrefusal_candidate | 1393 | 13.42 | 20.53 | 46.23 | 57.86 |
| v2_WG_refusal_conflict | 64 | 18.75 | 29.69 | 39.06 | 29.69 |
| WG_refusal_INVALID | 4 | 0.00 | 0.00 | 100.00 | 100.00 |

## Train/test audit

Published splits:202503=2640 train+4400 test;202406 train=2700. All440 base instruction texts shared with test. Answer-ID and question/model/style/reply record overlaps=0. Same instruction+identical response duplicates against either train version: test_1809,test_1939,test_2110,test_2261. Keep all rows. Actual optimizer training-row manifest unavailable.

Original paper v2 Tables1/6: fine-tuned Mistral kappa0.810, recall nonfulfillment91.1%/fulfillment93.4%; WildGuard kappa0.606. Our HB full-response pipeline is not claimed to reproduce its table.

## Dataset and scope

Base:202503,440 rows/44 categories/10 per category. Every listed transform440 rows; IDs identical to base.

| Group | Files | In first round? |
|---|---|---|
| writing | question_question.jsonl, question_slang.jsonl, question_uncommon_dialects.jsonl, question_technical_terms.jsonl, question_role_play.jsonl, question_misspellings.jsonl | no |
| persuasion | question_logical_appeal.jsonl, question_authority_endorsement.jsonl, question_misrepresentation.jsonl, question_evidence-based_persuasion.jsonl, question_expert_endorsement.jsonl | yes |
| encoding | question_ascii.jsonl, question_caesar.jsonl, question_morse.jsonl, question_atbash.jsonl | yes |
| languages | question_translate-ml.jsonl, question_translate-ta.jsonl, question_translate-mr.jsonl, question_translate-zh-cn.jsonl, question_translate-fr.jsonl | yes |

Overlap: all byte/normalized exact counts0. MiniLM cosine>=0.85 flags below; overlap across references, do not sum counts. All rows retained.

| Reference | flagged SORRY rows |
|---|---:|
| fit12_behaviors | 0 |
| val70_behaviors | 4 |
| legacy46_behaviors | 1 |
| dev22_behaviors | 2 |
| fit12_attack_prompts | 0 |
| val70_attack_prompts | 0 |
| train_strat97 | 8 |
| WJB_HarmBench_standard_sources | 18 |
| calibration_adversarial_harmful | 0 |
| calibration_adversarial_benign | 0 |
| calibration_vanilla_benign | 0 |
| calibration_underlying_behaviors | 0 |
| keep60 | 0 |

Union=19/440. Calibration700 rows retained,697 normalized base-request groups. Similarity flag is not proof of semantic identity/independence.

Qwen old-grid stop:2026-11-10T05:04:03–05:04:07UTC; receipt05:04:10UTC.9867 generation files unchanged; before/after manifest bf94912bb631d35d5fe4085b57b7c6d4158cc899129b799864b2471907b64775. Old WG cache9382 retained; condition effects unread.

Budget:600 GPUh main alpha0 search, build W/replay/adaptive separate; no condition stacking; no additional role-play family or SORRY role_play mutation. DeepInception retains its fixed definition.

## Acceptance throughput (actual files and wall clock)

Rows from atomic file counts; phase wall time between consecutive checkpoint completions, first phase includes cold load. Batch write bursts are not mistaken for per-row timing. No response or label read.

| Model | saved/1200 | cap120 single row/h | cap120 batch row/h | cap2400 single row/h | cap2400 batch row/h | generation ETA |
|---|---:|---:|---:|---:|---:|---|
| qwen | 874/1200 | 1177.5 (n=300) | 21834.0 (n=300) | 244.9 (n=174) | 1753.4 (n=100) | 11/10 20:41 JST–11/10 20:47 JST |
| llama | 812/1200 | 1265.5 (n=300) | 14044.5 (n=300) | 223.4 (n=112) | 831.9 (n=100) | 11/10 21:00 JST–11/10 21:20 JST |

Llama B16 long panel self-stopped at10:49:28UTC:1686044672bytes headroom, below3GiB. Its780 original files remain unchanged;80 failed long B16 candidate records are excluded from replacement B8. New Llama logical count includes100 explicitly referenced original B1 rows; copied references are not new throughput. Long B8 regenerates all three candidate conditions. No OOM or forced termination.

ETA uses only observed acceptance long-output row rates; same-speed scenario, not upper bound/CI. Excludes labels, historical20 and search20. Different model batch sizes allowed; same-model/family conditions keep identical batching.

### Memory telemetry coverage

Successful exact allocator peaks were not persisted by original acceptance worker; its per-batch3GiB margin check remains. No runtime source was edited. Monitor data below is sampled total-card use since its stated start, can include external CUDA contexts, not an exact whole-run or per-process peak.

Monitor start=2026-11-10T10:33:12.459856+00:00; every5seconds.

| Card | sampled peak MiB | sampled minimum free MiB |
|---|---:|---:|
| innet GPU0 | 19237 | 4845 |
| innet GPU2 | 22353 | 1728 |

llama new-version per-batch allocator telemetry (not whole v1 run): reserved peak=17.234GiB, allocated peak=16.976GiB, minimum measured headroom=5.807GiB; batches=25.

## Completed120-token paired-label gate

| Model | Condition | v2 flips/100 | WG known/worst-case flips/100 | Passed |
|---|---|---:|---|---|
| llama | alpha0 | 0 | 0/0 | True |
| llama | s3 | 1 | 1/1 | True |
| llama | random | 1 | 1/1 | True |
| qwen | alpha0 | 0 | 0/0 | True |
| qwen | s3 | 0 | 0/0 | True |
| qwen | random | 0 | 2/2 | True |

Gate covers120 only; does not admit2400, historical batch20 or search patch20. Absolute condition refusal rates were not aggregated. Gate result SHA=d8c9122a39448b4ca6e6a190f329f2601699bb8aadf589d2377559ad2f8f5ae4.

A transient additional GPU2 context PID54588/2496MiB was observed10:42UTC and exited before its ownership could be inspected. It was not touched and its project is unconfirmed. Card-use peaks cannot all be attributed to this experiment. Three requested admission gates remain unpassed.

## Provenance

- Human diagnostic SHA: 13b42d0914473c7b466ea7b6c69babcdfe00a1b0d2545ab13826307c30030dbd
- Performance SHA: 20c0fd699b82530d1073261a11477fa690bcde526e23ba0f06cc7140174cb098
- Field amendment SHA: 6378948b449b052ec88d2736b6084e6df266d0a5cc286d1a922d98c1310726ff
- Master candidate SHA: 849e925238d2d116b9cfa6ce403c54e032c78455c00a9f4d55d3b57b305d274b

Sources: https://arxiv.org/html/2406.14598v2 ; https://github.com/SORRY-Bench/SORRY-Bench .
