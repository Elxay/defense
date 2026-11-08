# WG read addendum24: three refusal attributions on identical downflip rows

Frozen UTC: 2026-11-08T13:56:45.165094+00:00, before any conditional WG numerical read. Nine-unit
completion remains required; #19–#23 sequence and main statistics are unchanged.
For each unit and each previously specified downflip denominator (WG-defined,
and HB-top1-defined when complete), report on EXACTLY the same downflip IDs:
(1) WG Response refusal yes/no/field INVALID;
(2) v2 refusal;
(3) v2 OR saved-v3 refusal.
Each has a numerator and the same named denominator. Preserve v2 as the
primary overrefusal rule and WG as a model reference, not human ground truth.
Pooled event counts reuse prompts and are not independent observations.

Reuse the v3 function AST from tools/handoff_20261106/audit.py, identical to
wjb_interim_diagnostics.py; do not import its executable analysis body or
change refusal wording/windows. Record full source hashes in the read output.
v2 source SHA256: 498dfd485d3dce6b05551784d698cc9716016f4a2614d06738261e96f5323948
v3 source SHA256: cd5b40df5069783bd439c63d1dd3e9d9e30c8846cb83d3fde670a6d22da587a3

Keep the per-field INVALID counts and ID lists from #23. Report actual full
formatted input_tokens >4096 separately; this includes the template, prompt
and response. Do not assume that exceeding4096 itself causes INVALID, or
that shorter outputs rule out format failures. No silent truncation, dropping
or default-harmless coding; no output-case reading selected by effect size.
State explicitly when nine units are still incomplete and do not invent an
actual completion time from an ETA. WG stays node01 GPU0 only.
