# Addendum26: external GPU3 observations and next judge startup evidence

Recorded UTC: 2026-11-08T14:52:00.952692+00:00. Operations only; no conditional WG/HB effect was read.
The immutable WJB runtime config and all numerical generation/judge settings
remain unchanged. No quantization, 8-bit, memory-gate relaxation, cross-machine
model split or WG-only final read is introduced.

GPU3 PID592686 runs as shared UID kemove, started13:17:17UTC November8,
script train_KPConv_Urb3DCDV2.py. The actual human operator cannot be established
from this account alone. It is not registered as this project's work and is
treated as external. No ownership inference from a filename authorizes killing
it; no contact to another person or process alteration is authorized/performed.
Record its presence, elapsed runtime and GPU3 total memory every30minutes,
starting now, in gpu3_external_30m.jsonl. Compare /proc start_ticks to prevent
PID reuse from being mislabeled as persistence of the same job. Never read or
publish its environment; stop the observer when this same process exits.
An observer heartbeat is separate from the30-minute observations.

At November9 12:00JST the already frozen addendum25 fallback remains: record
HB missing coverage, keep waiting, and use node01 only when a same-node card
pair outside active PAIR is genuinely available. In practice GPU0 alone is
insufficient while PAIR holds1/2; wait their release, then verify the backend
gate. No schedule or read rule is changed by waiting duration.

Expected tail accounting: s0,systemA,systemB are expected to be supplemented
after canonical PAIR evaluation if current contention persists. They never
enter the five-learned/four-random nine-unit primary test, and the abstract
does not depend on them. Their final coverage is reported separately.

Next innet judge window is NOT started at this record. It still requires
both leases and <=2000MiB per card. After acquisition, verify the current
pinned model-file manifest BEFORE model loading. Manifest SHA256:
35df6528783271ff63b0dd44537f50c4d09c022b9fdb786cd1de0c574e43af99
This captures current bytes after earlier alpha0/interim reads, not proof of
historical byte identity. The manifest contains file names, sizes and hashes;
no weights are published. Rehash every listed file at every new window;
a mismatch stops before loading. Model/template/probability code is unchanged.

After loading, rerun the existing20-row hf_innet reference gate, including
>=8 midrange PYes values and max absolute difference <0.001. Save started,
model_preflight, judge20_gate and ready records in a unique UTC+PID directory
public255/judge_launches/. Any gate failure is saved and re-raised; never mark
a ready record before it passes. The current pointer is not a replacement for
these separate per-launch records. Later signatures retain generation hashes.

The older docs225 node01-versus-vLLM gate failed and remains a failure record.
The proposed delayed rescue does not claim it passed; it requires the new
current-reference gate before adopting hf_node01_rescue. docs224's8-bit option
remains unadopted. No node01 rescue job has been launched.

Validation: Python compile; small known-byte manifest accepted; modified-byte
fixture refused before model loading; reference20 is not marked passed by
model hashing alone; real joint nine-unit read gate remains closed. Actual
reference20 is pending the next real judge window.

- tools/handoff_20261106/external_gpu3_watch30m.py: 30c3b16a95a28a7d30e11ace40b68f941f1ca145a9bbce1ec396dbb45736e638
- tools/handoff_20261106/hb_judge_preflight.py: 8cf383dd33d60aa29ea61a24f5a08a9b222fd30820b2ef1bf027a74bf86a1914
- tools/handoff_20261106/wjb_eval255_run.py: abc609fbbd20dae80668669674853dbf793bf8f3996031231dd8c7f210ae597e
