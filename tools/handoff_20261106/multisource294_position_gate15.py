"""Benign native-prefill position gate only; no attack/refusal label reads."""
from pathlib import Path
import datetime, hashlib, json, os, sys

R = Path('/home/dell/Def')
D = R / 'results/audit/multisource294'
O = D / 'prefix15'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p):
    return json.loads(Path(p).read_text())

def save(p, x):
    q = p.with_name(p.name + '.tmp')
    q.write_text(json.dumps(x, indent=2) + '\n')
    q.replace(p)

def main():
    import numpy as np
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '2'
    plan = load(O / 'position_gate_execution.json')
    assert sha(Path(__file__)) == plan['worker_sha256']
    assert sha(O / 'gate_inputs.private.json') == plan['inputs_sha256']
    sys.path.insert(0, str(R / 'tools/handoff_20261106'))
    from prefix_support import verify_role
    verify_role('target')
    from positioned_injection294 import generate_with_positioned_injection
    sys.path.insert(0, str(R / 'src'))
    from gen.common import generate_with_injection
    assert sha(R / 'src/gen/common.py') == plan['legacy_core_sha256']
    assert sha(R / 'tools/handoff_20261106/positioned_injection294.py') == plan['position_helper_sha256']
    vpath = R / plan['vector_file']
    assert sha(vpath) == plan['vector_file_sha256']
    v = np.load(vpath).astype(np.float32)
    tok = AutoTokenizer.from_pretrained(plan['target'], local_files_only=True)
    mdl = AutoModelForCausalLM.from_pretrained(
        plan['target'], local_files_only=True, torch_dtype=torch.bfloat16,
        device_map={'': 'cuda:0'}).eval()
    mdl.generation_config.disable_compile = True
    state = {'pid': os.getpid(), 'physical_gpu': 2, 'plan_sha256': sha(O / 'position_gate_execution.json'),
             'rows': [], 'no_labels_read': True, 'only_benign_technical_fixtures': True}
    for row in load(O / 'gate_inputs.private.json'):
        base = tok.apply_chat_template([{'role': 'user', 'content': row['text']}],
                                       add_generation_prompt=True)
        pref = tok('Sure, here is', add_special_tokens=False)['input_ids']
        ids = torch.tensor([base + pref], device='cuda:0')
        old = generate_with_injection(mdl, tok, ids, v, layer=9,
                                      max_new_tokens=120, device='cuda:0', alpha=1)
        p1 = generate_with_positioned_injection(mdl, tok, ids, v, layer=9,
             position=ids.shape[1]-1, max_new_tokens=120, assistant_prefill_ids=pref, alpha=1)
        p2 = generate_with_positioned_injection(mdl, tok, ids, v, layer=9,
             position=len(base)-1, max_new_tokens=120, assistant_prefill_ids=pref, alpha=1)
        assert p1['injection_positions'] == [ids.shape[1]-1]
        assert p2['injection_positions'] == [len(base)-1]
        equal = old['text'] == p1['text']
        state['rows'].append({'id': row['id'], 'P1_legacy_byte_equal': equal,
                              'P1_position': p1['injection_positions'][0],
                              'P2_position': p2['injection_positions'][0],
                              'P1_delta_norm': p1['delta_norm_runtime'],
                              'P2_delta_norm': p2['delta_norm_runtime'],
                              'P2_count': p2['injection_count']})
        state.update(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     completed=len(state['rows']))
        save(O / 'position_gate_live.json', state)
        if not equal:
            state['passed'] = False
            save(O / 'position_gate_result.json', state)
            raise RuntimeError('P1 legacy byte gate failed; prefix remains paused')
    assert len(state['rows']) == 20
    state['passed'] = True
    save(O / 'position_gate_result.json', state)
    # Release is deliberately separate: successful engineering tests do not
    # automatically start attack-family calibration or read effect labels.

if __name__ == '__main__':
    main()
