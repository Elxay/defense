
2026-11-11T05:00:06.668610+00:00 ready queue v5: node01 bulk language jobs may use any of three already byte-admitted same-node GPUs, preferring GPU2. PAIR0+1 priority, same batch membership/path, checkpoint integrity and main reading lock preserved; worker PIDs untouched.

2026-11-11T05:05:19.208795+00:00 language same-node lease cache safeguard frozen: v2 never reuses a zero20 candidate from a different device_uuid; compute that batch afresh through unchanged core, keep previous records/cache, append execution binding hashes. Current worker asked to yield at batch boundary; no GPU worker killed.
