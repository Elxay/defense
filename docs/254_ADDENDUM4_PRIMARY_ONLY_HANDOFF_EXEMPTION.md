# Handoff addendum4: exempt only one remaining nine-unit primary condition

Frozen UTC: 2026-11-08T15:46:04.116893+00:00, actual PAIR 302/500 (<480), canonical outputs0.
This narrows addendum3 before its trigger. Primary units are learned s3–s7
and rand0–3. Auxiliary units are s0,systemA,systemB; they are always paused
at >=480, EVEN IF only one auxiliary condition remains. They cannot postpone
canonical PAIR evaluation. Keep their atomic files, checkpoint hashes and
resume UTC; supplement them only after canonical evaluation completes.

Count unfinished primary units by both generation and HB-top1 coverage.
Exactly one remaining primary may finish under the prior exemption. With
zero remaining primary units, there is no exemption. With two or more,
pause the owned primary work as well. Auxiliary pause is an independent
marker and stays active while a single primary finishes and while PAIR
runs. Completing that primary cannot clear the auxiliary pause. Already
complete metadata may still be recorded; no new auxiliary GPU work starts.
After canonical completion, verify retained-file hashes before clearing
both flags and resuming pending work. Include rand3 in resumable pending
primary work, not only s7. No result/ASR is used to decide any branch.

The08:00JST capture previously imported wjb_morning_read, which indirectly
imported wjb_eval255_report. No aggregate function had been run by the
waiting capture, but the import chain did not meet the user's strict rule.
Replace it before08:00 with a standalone standard-library operational module.
Allowed fields are file coverage, PID/liveness, timing, heartbeat and GPU
memory. It computes timing means only, never loads scientific label fields,
never imports judge/evaluation/report modules, and records the actual sample
UTC. It does not claim a future observation has already occurred.

Tests: auxiliary-only remaining never exempted; single primary plus any
auxiliaries exempts only the primary; two remaining primaries pause; zero
remaining primaries has no exemption. All scenarios stop auxiliary workers.
Static imports of the snapshot and operational module are restricted to
standard library plus operational_metadata; syntax checks passed.

- tools/handoff_20261106/pair500_priority480.py: dcb753a17aa784ec06c130b526572ea8df74846b7dea734c702023b24fff910e
- tools/handoff_20261106/wjb_eval255_stage.py: 462ce1e19129d1803931bd0b87c101e2dbec991964e62fa50c06b59efa2145d6
- tools/handoff_20261106/wjb_tail_resume_queue.sh: 425e742a4d8b1aef4a4f989da99f2304bc46f51f5f353ccd81313782a8da62b9
- tools/handoff_20261106/operational_metadata.py: 09dc34fc9cfc4930f3e30e6b468b7facfea0d6f368001fe9697d3c425c78f786
- tools/handoff_20261106/capture_20261109_0800_status.py: dc92fe078d24f2022c3ea74c5bb78e50b72415c4df4f30d4fa6ee776dd308f86
