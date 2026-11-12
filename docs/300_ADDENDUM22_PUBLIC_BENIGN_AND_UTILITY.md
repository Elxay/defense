# Addendum22: public benign-set and utility evaluation (frozen before any benign output is read)

## Scope (full sets, no OKTest)
- XSTest safe 250, XSTest unsafe 200 (reported as its own table, not mixed with safe sets)
- OR-Bench-Hard 1,319
- official WildJailbreak adversarial-benign 210
- Total public rows: 23,748 across the four sets and the six conditions
- Additionally: 300 wrapper pairs (600 rows), GSM8K 200, ARC-C 200, six conditions, both models
- No OKTest is added.

## Labeling
- WildGuard "Response refusal" is primary; v2 refusal is the parallel sensitivity (per Addendum9). Sampling seeds are the 48 groups frozen in Addendum9.

## Generation path
- 120 generated tokens, using each model's already-passed 120-token batch gate: Llama B16, Qwen B32.
- alpha=0 must either be regenerated on this exact path, or be byte-checked against the legacy B8 batch and shown identical; one of the two must be recorded. Batch composition otherwise unchanged.

## Cost (estimates, not measured)
- Generation: ~3-4 GPU-hours for the four public sets plus pairs and utility items.
- Scoring: ~3-7 GPU-hours depending on judge.

## Status
- This addendum is written and hashed before any benign-set or utility output is read.
- Main effects remain unread; R1 stays locked behind the WildGuard re-evaluation.
EOF