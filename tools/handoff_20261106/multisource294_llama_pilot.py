"""Frozen 20-reference byte gate, then 25 rows per attack family; no label reads."""
from pathlib import Path
import datetime, hashlib, json, os, socket, subprocess, sys, time

R = Path('/home/dell/Def')
D = R / 'results/audit/multisource294'

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def load(p):
    return json.loads(Path(p).read_text())

def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    q = p.with_name(p.name + '.tmp')
    q.write_text(json.dumps(x, indent=2) + '\n')
    q.replace(p)

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '1'
    assert os.environ['DEVICE'] == 'cuda:0'
    plan = load(D / 'plan.json')
    assert sha(Path(__file__)) == plan['pilot_worker_sha256']
    assert sha(R / 'src/gen/common.py') == plan['core_sha256']
    assert sha(R / 'tools/handoff_20261106/prefix_support.py') == plan['prefix_support_sha256']
    assert sha(D / 'prompts.private.json') == plan['private_prompts_sha256']
    assert sha(D / 'gate20.private.json') == plan['private_gate20_sha256']
    sys.path.insert(0, str(R / 'tools/handoff_20261106'))
    from prefix_support import verify_role
    verify_role('target')
    import numpy as np
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    sys.path.insert(0, str(R / 'src'))
    from gen.common import generate_with_injection
    pulses = {'pid': os.getpid(), 'host': socket.gethostname(), 'physical_gpu': 1,
              'plan_sha256': sha(D / 'plan.json'), 'no_labels_read': True}
    def pulse(phase, **kw):
        save(D / 'llama_pilot_live.json', dict(pulses, utc=utc(), phase=phase, **kw))
    pulse('loading')
    path = plan['llama_target_node01']
    tok = AutoTokenizer.from_pretrained(path, local_files_only=True)
    mdl = AutoModelForCausalLM.from_pretrained(
        path, local_files_only=True, torch_dtype=torch.bfloat16,
        device_map={'': 'cuda:0'}).eval()
    mdl.generation_config.disable_compile = True
    vector = np.zeros(4096, dtype=np.float32)
    original = mdl.generate
    last = {}
    def track(*args, **kwargs):
        out = original(*args, **kwargs)
        last['id'] = int(out[0, -1])
        return out
    mdl.generate = track
    eos = mdl.generation_config.eos_token_id
    eos = {eos} if isinstance(eos, int) else set(eos)
    uuid = subprocess.check_output(
        ['nvidia-smi', '--query-gpu=uuid', '--format=csv,noheader', '-i', '1'],
        text=True).strip()
    def generate(row):
        ids = tok.apply_chat_template(
            [{'role': 'user', 'content': row['prompt']}], add_generation_prompt=True)
        prefix = row.get('assistant_prefill', '')
        if prefix:
            ids += tok(prefix, add_special_tokens=False)['input_ids']
        input_hash = hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest()
        started = time.monotonic()
        z = generate_with_injection(
            mdl, tok, torch.tensor([ids], device='cuda:0'), vector,
            layer=9, max_new_tokens=2400, device='cuda:0', alpha=0)
        elapsed = time.monotonic() - started
        assert z['injection_count'] == 1 and z['delta_norm_runtime'] == 0
        z.update(eos=last['id'] in eos, last_token_id=last['id'],
                 rho_runtime=0.0, assistant_prefill=prefix,
                 actual_input_ids_sha256=input_hash,
                 judging_text=prefix + z['text'])
        return z, elapsed
    gate = []
    for row in load(D / 'gate20.private.json'):
        z, _ = generate(row)
        equal = hashlib.sha256(z['text'].encode()).hexdigest() == row['expected_text_sha256']
        gate.append({'id': row['id'], 'byte_equal': equal})
        pulse('reference_gate', completed=len(gate), total=20)
    save(D / 'llama_generation_gate20.json', dict(
        pulses, utc=utc(), pairs=gate, passed=all(x['byte_equal'] for x in gate)))
    assert len(gate) == 20 and all(x['byte_equal'] for x in gate), 'Byte gate failed; stop unchanged'
    rows = {r['id']: r for r in load(D / 'prompts.private.json')}
    timing = {}
    for family in plan['family_order']:
        ids = plan['pilot_ids'][family]
        assert len(ids) == 25
        times = []
        for row_id in ids:
            if (D / 'request_gpu1_for_qwen.json').exists():
                pulse('yield_to_qwen', family=family, completed=len(times))
                return
            row = rows[row_id]
            p = D / 'llama_pilot.private' / (row_id + '.json')
            signature = {'plan_sha256': sha(D / 'plan.json'),
                         'worker_sha256': sha(Path(__file__)),
                         'prompt_sha256': row['prompt_sha256'],
                         'condition': 'alpha0', 'device_uuid': uuid}
            if p.exists():
                old = load(p)
                assert old['signature'] == signature
                seconds = old['elapsed_seconds']
            else:
                z, seconds = generate(row)
                save(p, dict(pulses, id=row_id, signature=signature, utc=utc(),
                             result=z, elapsed_seconds=seconds))
            times.append(seconds)
            pulse('pilot_generation', family=family, completed=len(times), total=25,
                  seconds_per_row=sum(times) / len(times))
        timing[family] = {'n': 25, 'total_seconds': sum(times),
                          'seconds_per_row': sum(times) / len(times)}
        save(D / 'llama_pilot_timing.json', dict(pulses, utc=utc(), by_family=timing))
    save(D / 'llama_pilot_complete.json', dict(pulses, utc=utc(), n=75,
                                               labels_or_effects_read=False))
    pulse('pilot_complete_no_scores_read')

if __name__ == '__main__':
    main()
