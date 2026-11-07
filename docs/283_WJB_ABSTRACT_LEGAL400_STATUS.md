# 283: WJB abstract, legal follow-up, and same-alpha queue
Server date -u: 2026-11-07T04:32:57Z; JST: 2026-11-07T13:32:57+09:00.
合法护栏已先读，主判据与 WJB 护栏尚未读取。原两臂的判官等最后的 node01 生成缓存、同步与两张卡共同空闲。所有第三臂向量已完成，原判官先取 innet 2/3 双锁并逐卡通过 2 GiB 门禁。双卡锁无法全取就释放，训练不持有原判官所需锁。
After original scoring releases both leases, plain grid generation may start. Its judge, alpha freeze and holdout still wait for the original unified analysis. Original aggregation opens no earlier than 2026-11-08 00:00 JST; the legacy controller readiness record is not that read.
Same-alpha s3 uses node01 GPU0 and respects the existing seed3-B queue; s5 uses node01 GPU2 after original generation. Both completions and the original unified read are required for secondary aggregation. The original alpha selection and primary criterion stay frozen.
The 8 selected 400-token rereads all reproduce the original 120-token text and reach substantive content, with zero explicit refusals. This does not validate recall outside the sampled outputs.
WJB judge ASR changes: random -4 to +1 pp; learned drops 11.3 to 20.0 pp. The 2-direction result remains 3/5 failed, the 4-direction supplement is 5/5, exploratory exact U=0, two-sided p=2/126.

| Job | Host/GPU | PID | Phase | Progress | Heartbeat age s |
|---|---|---:|---|---|---:|
| original_s3 | node01/0 | 1888265 | complete | 1800/1800 | 536.1 |
| original_s4 | node01/1 | 1837851 | pairs600 | 367/600 | 0.3 |
| original_s5 | node01/2 | 1837855 | pairs600 | 427/600 | 1.0 |
| original_s6 | innet/2 | 2303482 | complete | 1800/1800 | 9502.2 |
| original_s7 | innet/3 | 2241120 | complete | 1800/1800 | 7799.9 |
| same_alpha_s3 | node01/0 | 1886489 | waiting_seed3_B_priority | 0/600 | 7.3 |
| same_alpha_s5 | node01/2 | 1886490 | waiting_original_generation | 0/600 | 7.3 |
| noise_B | node01/0 | 1888514 | wjb300 | 26/300 | 3.1 |
| legal400 | innet/2 | 2467154 | complete | 8/8 | 831.8 |
| original_controller | innet/CPU | 2224284 | generating_full |  | 7.2 |
| plain_controller | innet/CPU | 2484943 | waiting_original_2arm_before_plain_grid | 5/5 vectors done; grid 0 | 6.0 |
| same_alpha_analysis | innet/CPU | 2481325 | waiting_both600_and_original_read |  | 27.6 |

Hashes:
- docs/252_ADDENDUM5_SAME_ALPHA_PAIRS.md SHA256 1d9422f8f86ca463b8e222bf064126aa986eb5d36650d1128da90ba5e9552749
- docs/282_REFERENCE_VERIFICATION.md SHA256 eb7ebbe2f2da0c4a1a347bc592fa0b36d07649cd024d6dccb806adf15f3b5f5f
- paper/CLAIM_EVIDENCE.json SHA256 6096dc46ed548c49c093053441bfada4ee77c36f012f5a4e46a1e8cf008403af
- paper/manuscript.pdf SHA256 48bfc0b9668da1238724d647cf35c1a462a3724152413048ff14d07ac189e9d4
- results/audit/handoff_round12/legal400_review_summary.json SHA256 a6db0e17a3a7c302540be707f0c173945bfcfbe8e9c43aca79cbd80d64315135
- results/audit/handoff_round12/flip51_rule_metrics.json SHA256 aac42c1122cabf14089b2cf7f8bdacbc22e10f757c084900852049eba6264330
- results/audit/handoff_round12/status_published_snapshot.json SHA256 30741f50478123181dd85ad80a53b1bd21b054474868c7bba009e3d37152d6a8
