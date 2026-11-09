# Vicuna norm attempt: loading blocked before measurement

RecordedUTC 2026-11-09T14:57:13.923271+00:00; attempt ended by controllerUTC 2026-11-09T14:50:49.699088+00:00. Official v1.5 revision c8327bf999adbd2efe2e75f6509fa01436100dc2 copied to node01 for two24GB cards. Three .bin shards matched the frozen official hashes. All60 native prompt input hashes matched the innet renderer before GPU model inference.

Node runtime torch=2.5.1+cu124,transformers=4.52.4. Model loading raised ValueError because this Transformers loader requires torch>=2.6 for .bin loading. No norm forward occurred (0/60), so no median or rho is reported. This is a software admission failure, not a failed numerical norm or a model result. No guard was overridden, no8-bit/quantized model introduced, no shared environment modified and no external process signalled. A supported isolated runtime or an independently verified equivalent safetensors serialization is needed for a new attempt, with a new execution manifest. Today's failed attempt is preserved rather than rewritten.

FailureSHA256 `dbf5f91deedf4814aa8f5e8d462040f24264eddcacee9244ee21286236aeabb2`. ExecutionSHA256 `ed5b517b5614016d18ce02d23ad0a2a3682ea18d3360f43a686ce8be113a937f`. No alpha0 outputs or trained Vicuna vector exist from this attempt.
