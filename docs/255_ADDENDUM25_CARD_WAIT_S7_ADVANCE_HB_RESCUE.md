# Addendum25: occupied GPU3, authorized s7 advance and delayed HB rescue

Frozen UTC: 2026-11-08T14:30:34.633768+00:00. PAIR actual 291/500 (<480); canonical0; s7
outputs0. No conditional WG effects were read. The user explicitly approved
"append an exception, generate s7 first" after being shown the old rule.
This is resource-driven scheduling after alpha0/interim HB reads, not an
outcome-driven change. Keep all estimands, conditions, vectors, alpha, row
sets, generated-token cap and both-judge final read lock.

## Ownership, waiting and the actual old sequence

Read-only process inspection, rendered in UTC:
kemove   Sun Nov 8 13:17:17 2026   python
Script name: train_KPConv_Urb3DCDV2.py. It is an Urban3D project, not identified
as MTA, and is not marked as this project. A shared Unix UID does not prove
personal/project ownership. Do not stop it or change its environment.
GPU3 was observed at6273MiB used, including6250MiB for PID592686.
Gate remains <=2000MiB; no model quantization/offload or threshold bypass.
Record card waiting from rand3 generation completion13:56:42UTC, current
occupancy and first score time; report elapsed until first score separately
from pure waiting because model loading/reference checks are included.

The original protocol/addendum4 fixes condition order but the execution
state machine docs/255_STATE_MACHINE_AND_ZERO20_RESULTS.md line9 explicitly
says "Generate each harmful condition ... then score it before advancing."
Thus the previously implemented serial rule was real, not merely an informal
suggestion. Preserve that text; this user-approved exception supersedes it
only while GPU3 blocks the rand3 judge window.

## Authorized single-card exception

Use innet GPU2 ONLY, its existing lease, wait_gpu and launch_job, to generate
old_s7 at fixed alpha1.0, unchanged vector/model,2400 cap and the same
single-row generate_with_injection. Run shard0 and shard1 sequentially on
physical GPU2, retaining original IDs/order within each shard, source hashes,
device UUID and all injection metadata. No target generation moves to node01
or innetGPU0/1. No other condition is advanced by this exception.
HarmBench continues waiting for two free innet cards. It cannot load on GPU2
while s7 holds that lease. The old queue may later score rand3, validate/skip
cached s7 outputs and score s7; do not regenerate/overwrite cached rows.
WG rand3 needs only completed target outputs, not HB scores, and runs on
node01GPU0 after s6. WG s7 waits all2000 s7 target rows. GPU1/2 on node01 stay
exclusive to PAIR until its search releases them. No effect read is enabled.

## Strict final read gate and delayed-HB fallback

Final nine-unit effects require BOTH HB top1 and WG for ALL nine2000-row
units, with WG completion manifests. Read status, then alpha0, then main
contrast, then robustness/attribution, each with UTC and SHA. WG finishing
first does not permit an early WG-only effect read. The coverage-only
wjb_nine_read_gate.py --require-ready refuses incomplete sets. Top2 and
three-way WG/v2/v2unionv3 attribution remain required for their frozen
robustness interpretations; INVALID stays per field with ID lists.

At 2026-11-09 03:00UTC (12:00JST), if HB is still incomplete, record the
pending conditions/coverage and evaluate rescue resources. First keep waiting
on the existing innet memory gate without disturbing the other job.
The 13B judge requires TWO cards on ONE machine; never split innet+node01.
On node01 there are only GPU0,1,2: WG freeingGPU0 alone leaves no second
PAIR-external card while PAIR holds1/2. Therefore do not take either PAIR
card, do not place WG on1/2, and do not pretend GPU0 alone suffices.
If no genuinely free same-node pair exists, wait PAIR search completion,
then acquire node01GPU1/2 through their existing leases and <=2GB gates.
Target generation remains innet; transfer only private generations/reference
metadata over SSH/rsync, never to Git. Missing target outputs must still be
completed before either judge's final unit read.

Before rescue scoring, verify identical13B weight/tokenizer/template hashes,
BF16, greedy one-token decision, original standard prompt and512-token clip.
Run the existing fixed20 reference gate with >=8 PYes in[0.05,0.95], require
max absolute probability difference <0.001 and report label agreement.
Failure stops rescue; do not relax the gate or change classifier/denominator.
Use backend tag hf_node01_rescue, never hf_innet. Preserve all existing
innet scores. To avoid a condition/backend confound, an activated rescue
scores alpha0 AND all nine primary units on the same node01 backend; keep
innet results as separately identified diagnostics, not a favorable subset.
Freeze the selected backend manifest before those rescue outcomes are read.
Top2 robustness is scored on the same backend as its reported contrast.
Both judge result sets must be complete before the ordered read; no appeal
to delay permits dropping HB. The fallback decision/gates are frozen here;
this does not claim that a node01 rescue model has already been launched.

## Resume-entry correction and immutable WJB runtime config

The earlier new tail-resume wrapper overlooked the original worker's
unconditional PAIR-snapshot stop. Correct only this operational check:
normal workers still yield to the snapshot; post_pair mode requires canonical
full_queue phase=complete; last_condition mode requires the frozen exemption
marker for that exact single condition. No unrestricted bypass is added.
Also separate WJB's immutable runtime config from mutable PAIR scheduling
metadata, which had been imported via CFG. All condition/model values are
asserted identical at adoption; prior records keep their original config
hashes without rewriting. s7 starts only after this freeze. This prevents
future PAIR plan edits from invalidating WJB partial-cache signatures.
Runtime config SHA256: ff59424129efa47df4fa0201e6998a9d4d7cdbc4230fbcdb1adc0450be8f2a0c

Tests before launch: Python/Bash syntax; snapshot absent/default-preempt;
post_pair rejected while PAIR running and accepted only after completion;
last_condition accepted for its exact exempt name and rejects another;
joint read gate rejects the currently incomplete set; numerical condition
settings unchanged. No existing output was overwritten by these checks.

Sources:
- tools/handoff_20261106/wjb_eval255_run.py: d12a7a5d59f175863e586db4182f4277a2741414fabe83fcd24cac2933399bb0
- tools/handoff_20261106/wjb_tail_resume_queue.sh: a82fbeb7abd908018c21f76d309e1bcd9f55f4f801edeba44ac7afd1978171d0
- tools/handoff_20261106/wjb_s7_single_gpu2_queue.sh: 1348f3e00c34e03f31c59aece890891dfc5aac4133461bcdffa23887c2fe5f7d
- tools/handoff_20261106/wjb_nine_read_gate.py: 12811f8a19aae662fddfed3d89fb63d8843f75b45b1809546eabb875e0284faa
- tools/handoff_20261106/wjb_hb_delay_watch.py: 4daea971e25086b817ff14ff8732571f3b92e7a4dfaf2f89ea476455914ff1f1
