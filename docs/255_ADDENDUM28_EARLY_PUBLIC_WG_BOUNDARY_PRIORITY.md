# Addendum28: public WildGuard sensitivity during the harmful-queue idle gap

Frozen UTC: 2026-11-08T15:19:00.165204+00:00, before any public WG classification; zero cached local
public WG score rows. Scheduling only. The eight completed harmful units
are integrity-checked by input/summary hashes without reading outcomes.
They are skipped on coordinator resume, not reclassified.

Start public WG now on node01GPU0 only, same classifier source/model/template,
1979 rows per condition, ten conditions in existing order (19790 calls).
Per-row writes remain atomic and resumable. At each CONDITION boundary,
check ready higher-priority harmful and canonical-PAIR conditions. If ready,
public waits. Harmful dispatch publishes a node01 priority request before
acquiring the sameGPU0 lease; public checks these requests after lock
acquisition and yields before loading. A running public condition is allowed
to finish, so s7 can wait for that condition's remaining runtime. No mid-row
kill or model mutation is used. Public is always lowest priority.

When s7 target generation reaches2000 rows, its harmful WG job takes priority
at the next boundary. Afterward, public resumes remaining work as resources
permit. Its priority request is cleared on job exit; unexpected failure does
not authorize reading partial outcomes or bypassing a memory gate.
All GPU launches still use launch_job, <=2GB guard and GPU0 lease; node01GPU1/2
remain PAIR-only. Harmful WG scoring does NOT depend on HarmBench scores.

No analysis rule changes: v2 stays public primary, WG is sensitivity only;
keep the original strata, source manifests,120-token qualification, INVALID
handling and existing public-result read locks (including #15/#22). Do not
infer that public results have no read gate. No output/condition outcome is
read in this scheduling amendment. The joint harmful-nine lock also stays.

- tools/handoff_20261106/wildguard_public_queue.py: de554345ccc282bcdbb595c12e33a90bb1fa6d7719ba56042a4652f2c6ec63bd
- tools/handoff_20261106/wildguard_conditions_queue.py: e35e646a8923acbc67afabd4ff9c8d535fee7b9ba956af90ee22185c90e6416f
