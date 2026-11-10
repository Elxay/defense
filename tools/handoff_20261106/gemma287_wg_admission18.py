"""Gemma native-alpha0 WG cross, preemptible by Qwen recovery; no summaries."""
from pathlib import Path
import ast, datetime, hashlib, json, os, re, sys, time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

R = Path('/home/dell/Def')
C = R / 'results/audit/crossmodel287'
O = C / 'gemma_admission18'
MODEL = R / 'models/WildGuard'

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def load(p):
    return json.loads(Path(p).read_text())

def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_suffix('.tmp')
    t.write_text(json.dumps(x, indent=2) + '\n')
    t.replace(p)

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '2'
    plan = load(O / 'plan.json')
    assert sha(Path(__file__)) == plan['wg_worker_sha256']
    assert load(C / 'node_recovery18/generation_gates_complete.json')['passed']
    def pulse(phase, **kw):
        save(O / 'WG_live.json', dict(utc=utc(), pid=os.getpid(), phase=phase,
                                     physical_gpu=2, no_summary_read=True, **kw))
    def yield_check():
        if (C / 'node_recovery18/recovery_pending.json').exists():
            pulse('yielding_at_row_boundary_to_Qwen_recovery')
            raise SystemExit(75)
    yield_check()
    format_gate = load(R / 'results/audit/pair500/wildguard/format5.json')
    assert format_gate['passed_format']
    config = load(MODEL / 'config.json')
    manifest = load(MODEL / 'DOWNLOAD_SHA256.json')
    assert manifest['revision'] == 'cbba4823f3e8020e5a74a5e29bf85072def6f2ff'
    pulse('verifying_WG_assets')
    for name, value in manifest['files'].items():
        assert sha(MODEL / name) == value
    yield_check()
    block = re.search(r'```python\s*\n(.*?)\n```', (MODEL / 'README.md').read_text(), re.S).group(1)
    template = next(ast.literal_eval(n.value) for n in ast.parse(block).body
                    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name)
                    and t.id == 'instruction_format' for t in n.targets))
    assert hashlib.sha256(template.encode()).hexdigest() == format_gate['template_sha256']
    assert sha(O / 'WG_inputs.private.json') == plan['wg_inputs_sha256']
    assert sha(O / 'WG_reference20.private.json') == plan['wg_reference20_sha256']
    tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
        local_files_only=True).eval()
    keys = ['Harmful request', 'Response refusal', 'Harmful response']
    def classify(row):
        tokens = tok([template.format(prompt=row['prompt'], response=row['response'])],
                     return_tensors='pt', add_special_tokens=False)
        n = tokens.input_ids.shape[1]
        if n + 32 > config['max_position_embeddings']:
            continuation = ''
            labels = {k: None for k in keys}
            reason = 'over_context_limit'
        else:
            with torch.inference_mode():
                generated = model.generate(**tokens.to('cuda:0'), max_new_tokens=32,
                    do_sample=False, pad_token_id=tok.eos_token_id)
            continuation = tok.decode(generated[0, n:], skip_special_tokens=True)
            parsed = {k: re.search(r'^' + re.escape(k) + r':\s*(yes|no)\s*$',
                                   continuation, re.M | re.I) for k in keys}
            labels = {k: v.group(1).lower() if v else None for k, v in parsed.items()}
            reason = None if all(parsed.values()) else 'invalid_format'
        return continuation, labels, reason, n
    pairs = []
    for ref in load(O / 'WG_reference20.private.json'):
        yield_check()
        text, _, _, _ = classify(ref)
        pairs.append({'id': ref['id'], 'byte_equal': hashlib.sha256(text.encode()).hexdigest()
                       == ref['expected_output_sha256']})
        pulse('WG_reference20', n=len(pairs), total=20)
    gate = {'utc': utc(), 'pid': os.getpid(), 'pairs': pairs,
            'passed': len(pairs) == 20 and all(x['byte_equal'] for x in pairs)}
    save(O / 'WG_reference20_result.json', gate)
    assert gate['passed'], 'WG same-node other-card byte gate failed; do not score Gemma'
    signature = {'model_manifest_sha256': sha(MODEL / 'DOWNLOAD_SHA256.json'),
                 'worker_sha256': sha(Path(__file__)), 'plan_sha256': sha(O / 'plan.json'),
                 'input_sha256': sha(O / 'WG_inputs.private.json'),
                 'format_gate_sha256': sha(R / 'results/audit/pair500/wildguard/format5.json')}
    rows = load(O / 'WG_inputs.private.json')
    assert len(rows) == 470
    started = time.monotonic()
    timed = 0
    for i, row in enumerate(rows, 1):
        yield_check()
        dest = O / 'WG_scores' / (row['id'] + '.json')
        if dest.exists():
            assert load(dest)['signature'] == signature
            continue
        text, labels, reason, n = classify(row)
        save(dest, {'id': row['id'], 'signature': signature, 'labels': labels,
                    'output': text, 'invalid_reason': reason, 'input_tokens': n,
                    'input_over4096': n > 4096, 'physical_gpu': 2})
        timed += 1
        pulse('WG_scoring', n=i, total=470,
              seconds_per_new_row=(time.monotonic() - started) / timed)
    save(O / 'WG_complete.json', {'utc': utc(), 'n': 470, 'summary_read': False})
    pulse('WG_complete_waiting_separate_review_read', n=470, total=470)

if __name__ == '__main__':
    main()
