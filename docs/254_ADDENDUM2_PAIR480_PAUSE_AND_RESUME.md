# PAIR evaluation operational addendum 2: row-count trigger and resume

Frozen UTC: 2026-11-08T13:28:16.023688+00:00. User-requested before any canonical PAIR generation
(0 files); actual search count 282/500. No conditional WG effects
were read. This supersedes only the clock-based 2026-11-09 18:00 JST pause
in addendum1; old text/config/publication remain archived. Search configuration
and source stop 2026-11-11 15:00 UTC (11/11 24:00 JST) are unchanged.

Trigger: query actual atomically saved node01 PAIR .json rows every30s;
verify unique permitted row IDs and unchanged search config hash9e46b2e7...;
pause WJB tails when completed rows >=480. A finalized cutoff prompt snapshot
also triggers handoff even if <480; failed progress queries cause no action.
There is no 18:00/19:30 clock trigger. At ~380s/row, the final20 rows still
take ~2.1h, not one hour; do not claim this rule eliminates all idle time.

Before handoff, only owned and launch_job-registered WJB tail generation/judge
workers old_s7,old_s0,SYS_A,SYS_B may receive TERM. Stage entry checks the
active trigger marker and refuses new tail work. Do not alter PAIR workers,
other users' jobs, node01 GPU1/2 or innet GPU0/1. Atomically saved rows remain;
at most one unfinished row per worker is discarded. Record trigger UTC,
actual count/ID-list hash, stopped PIDs, and post-stop file hashes in
pair_priority_checkpoint.json. No response text enters these records.

Resume: wait canonical full_queue_live.phase=complete, meaning target
generation, HB/MinHash scoring and Guard have released innet GPU2/3. Verify
EVERY retained checkpoint hash before clearing the trigger; log resume UTC
and checked file count, then re-enter tails in order s7,s0,systemA,systemB.
Use the same workers/config, GPU leases, <=2GB memory gate and launch_job;
workers validate cached signatures and generate only missing rows. Resume
does not require reading any result. Any mismatch/failure stops, keeps
checkpoints and requires diagnosis; no automatic overwrite or gate relaxation.

PAIR WG waits ready WJB primary WG work first. If WJB is waiting for an
incomplete target paused by this marker, it is not a circular prerequisite
of PAIR WG. Public WG remains sensitivity, v2 remains primary by user choice.
This is scheduling only; no change to either main contrast, judge, row set,
condition order, denominator, read lock or abstract rule.

Operational checks: 479 does not trigger;480 does; finalized cutoff300 does;
live SSH count query succeeded; Python compilation/Bash syntax passed.

Sources:
- tools/handoff_20261106/pair500_priority480.py: 42c564f0e4741772bb76becff9169ca50b583e0ef94acf45611487ae836bdf31
- tools/handoff_20261106/wjb_tail_resume_queue.sh: 8bf9a177ce5a460d4efecbf5737c6ab01879f70d2ffef3ce5a3c0c429ca034ec
- tools/handoff_20261106/wjb_eval255_stage.py: 3b03de33450c9bec911f5a16d13d65a8835ed65d895cec39bea3d76c1e78a22d
- tools/handoff_20261106/pair500_wildguard_queue.py: bdc0685d6383000a3cbe4fe4a28ee10f7f3427cbc426e822964d4c2f3403a328
