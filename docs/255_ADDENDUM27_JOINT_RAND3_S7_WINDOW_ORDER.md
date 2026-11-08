# Addendum27: joint rand3/s7 judge window after generation and two-card availability

Frozen UTC: 2026-11-08T15:19:00.165204+00:00. Operations-only amendment before this window, with no
conditional effects read. Earlier serial queue is replaced by an owned CPU
coordinator; the existing single-GPU2 s7 generator is not restarted.

Prerequisites: rand3 all2000 target rows AND s7 all2000 target rows, fixed IDs
verified, then both innetGPU2/3 leases and <=2000MiB memory gate. A clock ETA
such as04:15JST is not permission to start. If GPU3's external job persists,
continue waiting even after GPU2 is free. No other job is stopped; no 8-bit,
quantization, offload, cross-node model split or memory-threshold change.

One window: rehash the pinned model artifacts, load the same BF16 classifier,
run the fresh20-row hf_innet reference gate, then score rand3 followed by s7
in ONE model session. Preserve per-launch started/preflight/gate/ready records
and require the existing midrange/delta checks. Validate both2000-row score
sets before writing their completion manifests. Missing rows from snapshot
preemption/failure remain incomplete; do not label them complete.
Release both leases, then resume normal tail generation s0,systemA,systemB.
Their exact completion remains resource-dependent, with the frozen>=480
handoff, <=1-remaining exemption and post-PAIR resumability unchanged. Main
nine-unit effects remain locked until BOTH judges finish all nine units.

A metadata-only08:00JST snapshot is scheduled for November9 (23:00UTC Nov8).
Its actual sample time is recorded; it does not pretend to provide future
observations now and never loads response/judge labels. Methods text only
corrects the pilot-before-freeze chronology; abstract and outcome tables
remain unchanged. Existing methods and pitfalls bodies are retained.

Contact record: shared-UID process and tmux metadata do not identify an hzx
operator. No unique hzx session/contact route is known and no question has
been delivered; owner, expected duration and permission for a one-hour gap
remain unanswered. Treat persistent GPU3 occupancy as the baseline scenario.
Only a correctly identified recipient may be contacted; no unknown pane gets
keystrokes/messages, and no environment or pane text was inspected.

- tools/handoff_20261106/wjb_eval255_stage.py: 6ceb8258d1dfff3d2c01839be757d51de6b3c89be89557286d50f4f7b2c7474a
- tools/handoff_20261106/wjb_tail_resume_queue.sh: 249798fb61de7717b2062b4fea682ca1e65d32be0fe9bba7d889628d988e2140
- tools/handoff_20261106/wjb_generation_coverage.py: e700f461729b7e81caf006df2d7951fb8eb7032156a799b75378a1f8ecb58ab5
- tools/handoff_20261106/wjb_joint_judge_then_tail.sh: 8f059d4d727b39d9eaa3475fddd688fdef8ef634f11867c50a1b0503d79d5605
- tools/handoff_20261106/capture_20261109_0800_status.py: fdfd16d1b55f126193f4efb9f0e49141afc6d58dc29e8b88c024a2fae046292a
