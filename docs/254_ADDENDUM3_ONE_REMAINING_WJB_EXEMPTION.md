# PAIR handoff addendum3: at most one unfinished WJB condition

Frozen UTC: 2026-11-08T13:56:45.165094+00:00; actual PAIR 286/500, below480, canonical generation0.
This user-requested fallback supersedes the unconditional pause only; the
>=480 trigger, source stop11/11 24:00 JST, fixed sequence and read locks stay.
No conditional WG effects were read to choose this rule.

At the trigger, count unfinished WJB tail conditions among s7,s0,systemA,B.
A condition is complete ONLY when all2000 target generation rows AND all2000
HB top1 score rows exist, with IDs checked against the fixed2000-row manifest.
Use file coverage only; never inspect numerical labels to decide scheduling.
If two or more conditions remain, execute the already frozen pause/checkpoint/
resume rule. If one remains, do not pause it: let its remaining generation AND
HB judge work complete, under the same two-card leases, before canonical PAIR
acquires those cards. If zero remain, no pause is needed. This is a condition
count exception, not a runtime estimate or result-dependent early stop.

The canonical queue waits for the trigger decision and, when exempt, its
completion record. This prevents it from stealing the cards between the last
condition's generation and judge stages. The exemption coordinator may use
the same resumable worker for the single remaining condition; it waits on the
existing leases, verifies cache signatures and never overwrites saved rows.
Log decision UTC, condition names, per-condition coverage, checkpoint hashes,
and completion UTC. Any retained-file hash mismatch stops execution.
No work moves to node01 GPU1/2 or innet GPU0/1. No attack text is published.

For an actual pause (>=2 remaining), verify the recorded checkpoints and log
resume UTC after canonical GPU work completes, then rejoin s7,s0,systemA,B in
order. The last-condition exception may delay canonical launch until that
condition finishes; it is intentionally allowed by the user, without a new
clock deadline or a claimed one-hour duration.

Source checks passed: Python compile, Bash syntax, live node count query and
live ID-constrained per-condition coverage query. Current remaining names
are metadata only: ['SYS_A', 'SYS_B', 'old_s0', 'old_s7'].

- tools/handoff_20261106/pair500_priority480.py: f90bdae881300f1e06c0f7c6649477351b84c32ad376ac5b383a6a93d0a53927
- tools/handoff_20261106/wjb_tail_resume_queue.sh: 4634c8cec95683d14caf6ba632a387da543771b910ccec97eeadd9a284777011
- tools/handoff_20261106/pair500_eval254_queue.sh: c70a31ea52056a306ff2b3a3d6dd170617350cbb8e379213b6b49a94a57ccbca
