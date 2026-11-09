# U1 fixed-cache Llama seed3 result

RecordedUTC 2026-11-09T14:57:57Z. Frozen before training in planSHA `b6a53c8a58072da274acff1f00b5cacb6ce3c2bdfaa8eb6d513d4955df1bf23f`. TrainingUTC 2026-11-09T14:31:06.579741+00:00 through 2026-11-09T14:34:41.601552+00:00,40steps,elapsed215.046967s. Same frozen seed3 initialization, native Llama block9/norm5.21, original trainer and fixed U1 attack/keep target cache. No new val70 or test outputs generated; historical results not replaced.

Cosine to frozen same-seed vector (float64 calculation): **0.999930750201**.
Difference L2: **0.061314328710**.
New/reference norms: 5.209999898896 / 5.210000054615.

This meets the user's suggested0.999 descriptive closeness reference. It is one observed fixed-cache reconstruction, not target-byte identity, a proof of target equivalence, or a quantified distribution of training nondeterminism. Future descriptions can report the cosine instead of only saying 'not verified', while retaining that limit. No threshold was loosened or target rewritten to achieve it.

ResultJSON SHA256 `7cf25d57c2d921aab6b5979d8068e21312a89badc6c9b98bb636fbbd42c82c63`; new vectorSHA256 `49e527abf3566815a48539c3fc42493adba4f0bdab9c72dde231fcbad80555fe`; frozen vectorSHA256 `033c4189b40642d3b800e90f9e5c1ba0dad61aacaa6e3a80304974cfea5a3eee`. Vector/checkpoint contents stay private. New-model training remains subject to individual frozen refusal audits; this cosine alone does not unlock it.
