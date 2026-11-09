# Fixed U1 target cache: one Llama seed3 retrain

FrozenUTC 2026-11-09T14:29:21.991604+00:00, before this fresh training run or cosine. Same historical trainer, initialization, frozen model/revision, layer9, norm5.21,40Adam steps,lr0.005,12fixed U1 fit targets and60cached native Llama keep continuations at0.075. Only the on-the-fly target-generation stage is replaced by the signed existing cache. New output directory prevents overwriting historical vectors or metadata. No new attacks, val70 or test inference.

Report raw signed cosine in float64 and vector difference L2 to the frozen seed3. User's >=0.999 is a descriptive closeness reference, not an empirically calibrated equivalence margin. Even a high cosine cannot establish byte identity of unavailable historical targets, general target equivalence, or a training-variance distribution from one run. A discrepancy remains a discrepancy, with no target editing or re-search to pass.

Use registered launch_job, shared GPU2 lock, unchanged memory gate and atomic optimizer/vector/receipt files. Checkpoint after every step and preserve RNG state. If allocation ends at15:00UTC, stop at a step boundary and preserve the checkpoint; no silent use beyond the allocation. New-model vector training awaits this comparison and each model's addendum4 refusal admission. No historical criterion or main Llama result is revised.

PlanSHA256 `b6a53c8a58072da274acff1f00b5cacb6ce3c2bdfaa8eb6d513d4955df1bf23f`. WorkerSHA256 `78de95565c1c7f6fe4d3562b9fe16b1b7476c5a5c6a3d07864b4b878bdfe13f1`. TargetCacheSHA256 `31ef70b9cf0fd334edb12d373659fcbafb8b1510dcc577448df869ec278ef9d0`.
