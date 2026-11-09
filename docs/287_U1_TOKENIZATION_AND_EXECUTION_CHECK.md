# U1 tokenization and execution binding

CPU checkUTC 2026-11-09T14:19:53.323468+00:00, after addendum5 and before vector training. No model weights loaded and no generation performed. All3 models use the same ordered12 target-text hashes; only their native tokenizer and prompt template differ.

|Model|Targets|Target tokens min / median / max|UNK|Control tokens|Exact decode roundtrip|Whitespace-normalized roundtrip|Canonical full-chat prefix matches|
|---|---:|---|---:|---:|---|---|---|
|qwen|12|7 / 19.0 / 202|0|0|12/12|12/12|12/12|
|gemma|12|8 / 19.5 / 210|0|0|12/12|12/12|12/12|
|vicuna|12|9 / 20.0 / 257|0|0|12/12|12/12|12/12|

The implemented training construction is the historical recipe: rendered native user prompt with assistant-generation prefix, then separately encoded target text with add_special_tokens=False. All36 label masks cover target tokens only and preserve the prefix. No BOS/EOS or role token is inserted inside the target. Full-chat tokenization is a separate boundary diagnostic, not an instruction to alter this frozen sequence. Any whitespace-normalization difference is reported rather than repaired by changing target text.

Qwen alpha0 has2 v2-positive refusals out of12. Against the corresponding two U1 targets, exact text matches are0/2; native target token lengths={'n': 2, 'min': 512, 'median': 512.0, 'max': 512, 'mean': 512}; same-ID U1 lengths={'n': 2, 'min': 8, 'median': 8.0, 'max': 8, 'mean': 8}. The36-row CSV records per-item hashes and codes, not output text. Two examples describe wording differences and do not establish a general style effect or classifier accuracy.

The old Qwen conditional pack is unchanged. A new private U1 pack rebinds its12 fixed Llama targets and60 native Qwen keep targets to the new effective protocol. Neither native fit12 alpha0 replies nor native donor targets enter the attack-target loss. Gemma and Vicuna must supply their own keep60 continuations; none are silently copied from Llama. `U1_active_execution_binding.json` is the effective execution binding, and all3 training_allowed flags remain false pending independent refusal admission. Historical gate failures and old manifests remain in place.

Tokenization JSON SHA256 `c00471b7be81f1562e184569c38f29d5dfd123d5521d624357548e6f46e297fe`. RowsCSV SHA256 `13f1e01ec60de14250b5ee1ed704d2ccf64911e3bc1a50856f0a29b1b5e2c346`. Active bindingSHA256 `7ffbecb0ed5759ab60d38dda8f487cd8e55a5da95087aeada798c65012e731b1`. No raw prompts or targets are included.

## Supplementary cap metadata check

UTC 2026-11-09T14:22:20.675884+00:00. Both native Qwen v2-positive fit12 replies have stored new_tokens=512 and eos=False. The two corresponding U1 targets each encode to8 Qwen tokens. Length and wording comparisons therefore include a truncation limitation and are not a style superiority claim or a full-text refusal validation. SupplementSHA256 `a91d02813b0e5fb04d850c357b6c09f82d4af6fea5b36133e9aef228b9745a99`.
