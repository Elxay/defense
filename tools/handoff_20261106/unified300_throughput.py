"""S0-only fixed calibration engineering benchmark. Never reads test labels."""
from pathlib import Path
import datetime
import gc
import hashlib
import json
import os
import subprocess
import sys
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

R = Path('/data/HZX/Def')
U = R / 'results/audit/unified300'
sys.path.insert(0, str(R / 'tools/handoff_20261106'))
sys.path.insert(0, str(R / 'src'))
from batched_injection300 import generate_batch_with_injection
from gen.common import generate_with_injection


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    q = p.with_suffix(p.suffix + '.tmp')
    q.write_text(json.dumps(x, indent=2) + '\n')
    q.replace(p)


def main():
    key, card = sys.argv[1], int(sys.argv[2])
    assert os.environ['CUDA_VISIBLE_DEVICES'] == str(card)
    plan = load(U / 'throughput_plan.json')
    assert plan['test_generation_allowed'] is False
    assert sha(__file__) == plan['worker_sha256']
    assert sha(R / 'tools/handoff_20261106/batched_injection300.py') == plan['batch_core_sha256']
    assert sha(R / 'src/gen/common.py') == plan['legacy_core_sha256']
    assert sha(U / 'calibration700.private.json') == plan['calibration_sha256']
    rows = {r['id']: r for r in load(U / 'calibration700.private.json')}
    spec = plan['models'][key]
    dest = U / 'throughput' / key
    def pulse(phase, **kw):
        save(dest / 'live.json', {'utc': utc(), 'pid': os.getpid(), 'model': key,
             'physical_gpu': card, 'phase': phase, 'test_effect_read': False, **kw})
    pulse('loading')
    started = time.monotonic()
    tok = AutoTokenizer.from_pretrained(spec['path'], local_files_only=True)
    tok.padding_side = 'left'
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        spec['path'], local_files_only=True, torch_dtype=torch.bfloat16,
        device_map={'': 'cuda:0'}, attn_implementation='sdpa').eval()
    model.config.use_cache = True
    load_seconds = time.monotonic() - started
    rendered = {k: tok.apply_chat_template([{'role': 'user', 'content': rows[k]['prompt']}],
                  add_generation_prompt=True) for k in plan['engineering_ids32']}
    ids = sorted(rendered, key=lambda k: (len(rendered[k]), plan['tie_break_hash'][k]))
    save(dest / 'runtime.json', {'utc': utc(), 'model': key, 'torch': torch.__version__,
        'transformers': __import__('transformers').__version__, 'backend': 'HF_bf16_sdpa',
        'cold_load_seconds': load_seconds, 'plan_sha256': sha(U / 'throughput_plan.json'),
        'rendered_ids_sha256': {k: hashlib.sha256(json.dumps(rendered[k]).encode()).hexdigest() for k in ids},
        'ordered_ids': ids, 'layer_zero_based': spec['layer']})
    zero = torch.zeros(model.config.hidden_size)
    gate_path = dest / 'single_core_gate20.json'
    if not gate_path.exists():
        gate = []
        for key_id in ids[:20]:
            pulse('legacy_single_zero20', completed=len(gate), total=20)
            old = generate_with_injection(model, tok, torch.tensor([rendered[key_id]], device='cuda:0'),
                                          zero, layer=spec['layer'], max_new_tokens=120, alpha=0)
            new = generate_batch_with_injection(model, tok, [rendered[key_id]], zero,
                       layer=spec['layer'], max_new_tokens=120, alpha=0)[0]
            gate.append({'id': key_id, 'text_equal': old['text'].encode() == new['text'].encode(),
                         'rho_runtime': new['rho_runtime'], 'injection_count': new['injection_count']})
        save(gate_path, {'utc': utc(), 'passed': all(x['text_equal'] and x['rho_runtime'] == 0 for x in gate),
             'pairs': gate, 'meaning': 'new B1 core versus legacy B1; not historical B8 reproducibility'})
    assert load(gate_path)['passed'], 'Preserve failure and stop; no gate relaxation'
    for cap in plan['caps']:
        for batch_size in plan['batch_grid']:
            path = dest / f'cap{cap}_B{batch_size}.json'
            if path.exists():
                continue
            pulse('benchmark', max_new_tokens=cap, batch_size=batch_size)
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            outputs, samples = [], []
            tick = time.monotonic()
            try:
                for n in range(0, len(ids), batch_size):
                    members = ids[n:n + batch_size]
                    result = generate_batch_with_injection(model, tok, [rendered[k] for k in members], zero,
                        layer=spec['layer'], max_new_tokens=cap, alpha=0)
                    assert all(r['rho_runtime'] == 0 and r['injection_count'] == 1 for r in result)
                    for k, r in zip(members, result):
                        save(dest / 'generation.private' / f'cap{cap}_B{batch_size}' / (k + '.json'),
                             {'id': k, 'batch_ids': members, 'plan_sha256': sha(U / 'throughput_plan.json'), 'result': r})
                        outputs.append({k2: v for k2, v in r.items() if k2 != 'text'})
                    torch.cuda.synchronize()
                    free, total = torch.cuda.mem_get_info()
                    samples.append({'free_bytes': free, 'total_bytes': total,
                                    'allocated': torch.cuda.memory_allocated(), 'reserved': torch.cuda.memory_reserved()})
                elapsed = time.monotonic() - tick
                peak = torch.cuda.max_memory_reserved()
                # Peak framework reservation plus device use outside this process; conservative at sample times.
                outside = max(x['total_bytes'] - x['free_bytes'] - x['reserved'] for x in samples)
                headroom = min(x['total_bytes'] for x in samples) - outside - peak
                tokens = sum(x['new_tokens'] for x in outputs)
                save(path, {'utc': utc(), 'status': 'complete', 'n': len(outputs), 'max_new_tokens': cap,
                    'batch_size': batch_size, 'seconds': elapsed, 'new_tokens': tokens,
                    'tokens_per_second': tokens / elapsed, 'rows_per_hour': len(outputs) * 3600 / elapsed,
                    'peak_reserved_bytes': peak, 'conservative_headroom_bytes': headroom,
                    'headroom_at_least_3GiB': headroom >= 3 * 1024**3,
                    'outputs_metadata': outputs, 'batch_manifest_sha256': sha(U / 'throughput_plan.json')})
            except torch.cuda.OutOfMemoryError:
                save(path, {'utc': utc(), 'status': 'OOM', 'n_saved': len(outputs),
                     'max_new_tokens': cap, 'batch_size': batch_size, 'seconds': time.monotonic() - tick,
                     'test_data_affected': False})
                gc.collect()
                torch.cuda.empty_cache()
    candidates = {}
    for cap in plan['caps']:
        data = [load(dest / f'cap{cap}_B{b}.json') for b in plan['batch_grid']]
        valid = [x for x in data if x['status'] == 'complete' and x['headroom_at_least_3GiB']]
        best = max((x['tokens_per_second'] for x in valid), default=None)
        candidates[str(cap)] = min((x['batch_size'] for x in valid if x['tokens_per_second'] >= .8 * best), default=None) if best else None
    save(dest / 'throughput_complete.json', {'utc': utc(), 'model': key,
        'candidate_batch_sizes': candidates, 'admitted_for_formal_generation': False,
        'remaining': '100x3 WG/v2 label gate, nonzero injection metadata, historical batch reproduction',
        'no_test_effects_read': True})
    pulse('throughput_complete_only', candidates=candidates)


if __name__ == '__main__':
    main()
