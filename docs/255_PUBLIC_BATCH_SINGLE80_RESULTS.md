# 255 · Public batch/single path comparison

Same twenty uniformly sampled GPU2-source prompts were used for each vector. Sampling pool contains 1001 rows from the original public split on GPU2, including its unsafe control. Seed20261119. The reference vectors and GPU2 are held fixed. Original batch outputs are retained.

| Condition | n | Byte-identical | Different |
|---|---:|---:|---:|
| old_s3 | 20 | 11 | 9 |
| old_s4 | 20 | 14 | 6 |
| old_s5 | 20 | 9 | 11 |
| old_s6 | 20 | 10 | 10 |

All80 replay records show injection_count1 and rho_runtime approximately5.21, with configured vector hashes. All20 unique prompts have identical unpadded token IDs under the batch and single input builders. Only44/80 generated responses match byte for byte. This establishes observed batch-versus-single path differences, without establishing their sole low-level cause. It does not establish global equivalence or restore missing original batch injection observations. All public comparison numbers remain on the matched batch8 baseline path.

Result SHA-256 baae8bf13381b0efb55807368ce4723dc3f608bd0c9a5661b2e3e0f3cf513e17.
