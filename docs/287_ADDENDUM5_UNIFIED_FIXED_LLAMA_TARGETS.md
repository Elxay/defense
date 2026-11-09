# Cross-model addendum5: U1 fixed Llama targets for every new model

FrozenUTC 2026-11-09T14:17:36.905016+00:00. User explicitly superseded the conditional native/donor branch. This amendment is after the known Qwen alpha0 and failed native-donor diagnostics, but before vector training or treated-condition effects for Qwen2.5-7B-Instruct, Gemma-2-9B-it and official Vicuna-13B-v1.5. EvidenceSHA256 792e5008916411ac7765177bf2a5b8dfc71f516660f6a7878eb985055ce1ff7c.

## Effective training target rule

All three new models use exactly the same ordered12 target TEXTS from `results/style_intervention/old_recipe_targets.json`, SHA256 `31ef70b9cf0fd334edb12d373659fcbafb8b1510dcc577448df869ec278ef9d0`; ordered-text-list SHA256 `223085ad8221c3a4b4f0f1d8c6ea432aa7c4eb912ac35d474d36275b8f99a8b9`. Targets are tokenized with each pinned native tokenizer. The fit12 input rows and target-by-ID pairing remain fixed. Each model keeps its own alpha0 keep60 continuations. This is a common Llama-target-transfer protocol for every new model, not a fallback and not a per-item mixture.

The >=3/12 native-refusal gate is no longer used to select or authorize training targets. Preserve its original freeze, failure and addendum3's conditional branch as superseded history; never erase or lower that criterion. Qwen's12 native-donor outputs and native fit12 alpha0 outputs remain diagnostic-only and cannot enter the U1 fit loss. The known Qwen alpha0 v2 counts are2 refusals and10 nonrefusals; the rule alone does not validate that all10 substantively complied or were harmful. Vicuna's text-transfer branch is now default, just as for Qwen and Gemma. No further native-donor generation is required for target selection.

Retain addendum4 unchanged: fresh native alpha0 legal388 and val70 each supply the frozen30 v2-negative samples; clear misses plus uncertainty <=3/30 for both sets admits v2. Otherwise use WildGuard response-refusal for both selection sets under that port's frozen fallback. This audit concerns the labeler, not target provenance. Training remains locked until a hashed review/admission record exists. Existing Qwen alpha0 outputs, sample IDs and their signatures remain valid evidence under addendum4; U1 does not alter those sampling rules or regenerate samples.

All alpha choices, legal limits (19 new refusals/388 per seed), seed counts, layer index conventions, rho=0.9 times native keep60 median norm, training optimizer/loss weights, random-direction rule, judges, row-retention and test read locks remain unchanged. U1 does not make the new models' alpha-selection procedure identical to the historical Llama alpha=1.0 operating point.

## Historical Llama and limitations

Historical Llama scripts generated native donor targets during each training run. The pinned cache is an old-recipe reconstruction (200-token generation, use_cache=False), not a recovered certificate of each historical run's target bytes. Existing Llama results are unchanged and remain historical native-target references. We cannot assert that all historical Llama seeds used byte-identical text to this cache. Strict fixed-text replication of Llama would require a separately labelled retraining run; it is not silently substituted here.

The12 cached targets are nonempty; prior v2 screening marks9/12 as refusal openings. Do not call this cache12 independently validated refusals, filter the other3, or choose new texts after test effects. Tokenization checks report all12 and preserve the fixed texts. For new models this is a Llama-style text transfer; natural refusal wording may differ, and v2 agreement may therefore be favored. Report WildGuard response-refusal beside v2, with the120-token truncation limitation. Model labels are not human calibration.

Gemma's system-prompt baselines remain user-turn prefixes because its native template rejects a system role. This is a model-interface difference; do not force an unsupported role or call the baseline placement identical.

Effective protocolSHA256 `1a91bd203261801912a6b7a276d28b5496904f629dc8d6929d2934aa1f8b8294`. No training has been authorized merely by this target amendment; the independent refusal admission is still pending. This document supersedes target provenance only, preserving every historical record.
