"""Separate single-prefill position-aware hook; does not modify gen/common.py."""
import hashlib
import json
import torch

def generate_with_positioned_injection(model, tok, ids, vec, *, position,
                                      layer=9, max_new_tokens=2400,
                                      assistant_prefill_ids=None,
                                      src_vec_sha256=None, alpha=None):
    assert ids.ndim == 2 and ids.shape[0] == 1
    n = ids.shape[1]
    position = int(position)
    assert 0 <= position < n
    prefix = list(assistant_prefill_ids or [])
    if prefix:
        assert ids[0, -len(prefix):].tolist() == prefix
    state = {'count': 0, 'positions': []}

    def hook(module, args, output):
        if state['count']:
            return output
        h = output[0].clone()
        assert h.shape[0] == 1 and h.shape[1] == n, 'Expected a single complete prefill'
        before = h[0, position, :].clone()
        h[0, position, :] = before + torch.tensor(vec, dtype=h.dtype, device=h.device)
        state['delta_norm_runtime'] = float((h[0, position, :] - before).float().norm())
        state['count'] += 1
        state['positions'].append(position)
        return (h,) + output[1:]

    handle = model.model.layers[layer].register_forward_hook(hook)
    try:
        with torch.no_grad():
            out = model.generate(ids, max_new_tokens=max_new_tokens,
                                 do_sample=False, pad_token_id=tok.eos_token_id)
    finally:
        handle.remove()
    assert state['count'] == 1 and state['positions'] == [position]
    generated = out[0, n:].tolist()
    eos = model.generation_config.eos_token_id
    eos = {eos} if isinstance(eos, int) else set(eos)
    continuation = tok.decode(generated, skip_special_tokens=True)
    # Decode the combined assistant IDs once: SentencePiece boundaries must not
    # be reconstructed by joining two independently decoded text fragments.
    complete_reply = tok.decode(prefix + generated, skip_special_tokens=True)
    return {'text': continuation, 'complete_reply_text': complete_reply,
            'assistant_prefill_tokens': len(prefix),
            'injection_count': state['count'], 'injection_positions': state['positions'],
            'prompt_len': n, 'new_tokens': len(generated),
            'eos': bool(generated and generated[-1] in eos),
            'delta_norm_runtime': state['delta_norm_runtime'],
            'device': str(ids.device),
            'device_uuid': str(torch.cuda.get_device_properties(torch.cuda.current_device()).uuid)
                           if torch.cuda.is_available() else None,
            'inj_vec_sha256': hashlib.sha256((torch.tensor(vec, dtype=torch.float32).numpy() + 0.0).tobytes()).hexdigest(),
            'input_ids_sha256': hashlib.sha256(json.dumps(ids[0].tolist(), separators=(',', ':')).encode()).hexdigest(),
            'src_vec_sha256': src_vec_sha256, 'alpha': alpha}
