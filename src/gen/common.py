"""Single-shot generation with exactly one prefill injection (shared)."""
import os, torch

def generate_with_injection(model, tok, ids, vec, layer=9, max_new_tokens=2400, device=None, src_vec_sha256=None, alpha=None):
    device = device or ids.device
    n = ids.shape[1]
    state = {"count": 0, "positions": []}
    def hook(mod, args, output):
        if state["count"] > 0:
            return output
        h = output[0].clone()
        before = h[0, n - 1, :].clone()
        h[0, n - 1, :] = h[0, n - 1, :] + torch.tensor(vec, dtype=h.dtype, device=h.device)
        state["delta_norm_runtime"] = float((h[0, n - 1, :] - before).float().norm())
        state["count"] += 1; state["positions"].append(n - 1)
        return (h,) + output[1:]
    hd = model.model.layers[layer].register_forward_hook(hook)
    try:
        with torch.no_grad():
            o = model.generate(ids, max_new_tokens=max_new_tokens, do_sample=False,
                               pad_token_id=tok.eos_token_id)
    finally:
        hd.remove()
    assert state["count"] == 1, f"injection_count={state['count']} != 1"
    assert state["positions"] == [n - 1]
    text = tok.decode(o[0][n:], skip_special_tokens=True)
    return {"text": text,
            "injection_count": state["count"],
            "injection_positions": state["positions"],
            "prompt_len": n,
            "new_tokens": int(o.shape[1] - n),
            "eos": bool(o[0, -1].item() == tok.eos_token_id),
            "device": str(device),
            "device_uuid": str(torch.cuda.get_device_properties(torch.cuda.current_device()).uuid) if torch.cuda.is_available() else None,
            "delta_norm_runtime": state.get("delta_norm_runtime"),
            "inj_vec_sha256": __import__("hashlib").sha256((torch.tensor(vec, dtype=torch.float32).numpy()+0.0).tobytes()).hexdigest(),
            "src_vec_sha256": src_vec_sha256, "alpha": alpha}