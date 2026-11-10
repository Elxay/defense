"""Versioned fixed-membership HF prefill injection; leaves legacy common.py intact."""
import hashlib
import json
import torch


def ids_sha(ids):
    return hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest()


def generate_batch_with_injection(model, tok, input_ids, vec, *, layer,
                                  max_new_tokens, positions=None,
                                  source_vector_sha256=None, alpha=None):
    assert input_ids and all(len(x) > 0 for x in input_ids)
    assert tok.padding_side == 'left' and tok.pad_token_id is not None
    enc = tok.pad({'input_ids': input_ids}, padding=True, return_tensors='pt')
    device = next(model.parameters()).device
    enc = enc.to(device)
    mask = enc['attention_mask']
    batch, width = enc['input_ids'].shape
    lengths = [len(x) for x in input_ids]
    assert mask.sum(1).tolist() == lengths
    assert torch.all(mask[:, -1] == 1)
    original_positions = [n - 1 for n in lengths] if positions is None else list(positions)
    assert len(original_positions) == batch
    assert all(0 <= p < n for p, n in zip(original_positions, lengths))
    padded_positions = [width - n + p for p, n in zip(original_positions, lengths)]
    vector = torch.as_tensor(vec, dtype=torch.float32)
    assert vector.ndim == 1 and vector.numel() == model.config.hidden_size
    state = {'count': 0}

    def hook(module, args, output):
        if state['count']:
            return output
        h = output[0] if isinstance(output, tuple) else output
        assert h.shape[:2] == (batch, width), 'Injection must occur on full prefill'
        h = h.clone()
        rows = torch.arange(batch, device=h.device)
        pos = torch.tensor(padded_positions, device=h.device)
        before = h[rows, pos].clone()
        h[rows, pos] = before + vector.to(device=h.device, dtype=h.dtype)
        state['runtime_norms'] = (h[rows, pos] - before).float().norm(dim=-1).tolist()
        state['count'] += 1
        return (h,) + output[1:] if isinstance(output, tuple) else h

    handle = model.model.layers[layer].register_forward_hook(hook)
    try:
        with torch.inference_mode():
            out = model.generate(**enc, max_new_tokens=max_new_tokens,
                                 do_sample=False, pad_token_id=tok.pad_token_id)
    finally:
        handle.remove()
    assert state['count'] == 1
    eos = model.generation_config.eos_token_id
    eos = {eos} if isinstance(eos, int) else set(eos or [])
    uuid = str(torch.cuda.get_device_properties(device).uuid) if device.type == 'cuda' else None
    vector_sha = hashlib.sha256((vector.cpu().numpy() + 0.0).tobytes()).hexdigest()
    records = []
    for i in range(batch):
        generated = out[i, width:].tolist()
        cut = next((j + 1 for j, t in enumerate(generated) if t in eos), len(generated))
        generated = generated[:cut]
        records.append({
            'text': tok.decode(generated, skip_special_tokens=True),
            'generated_ids_sha256': ids_sha(generated), 'new_tokens': len(generated),
            'eos': bool(generated and generated[-1] in eos),
            'injection_count': 1, 'injection_position': original_positions[i],
            'padded_injection_position': padded_positions[i],
            'prompt_len': lengths[i], 'batch_width': width, 'batch_size': batch,
            'rho_runtime': state['runtime_norms'][i], 'device_uuid': uuid,
            'input_ids_sha256': ids_sha(input_ids[i]), 'vector_sha256': vector_sha,
            'source_vector_sha256': source_vector_sha256, 'alpha': alpha,
        })
    return records
