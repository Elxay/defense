"""S0 only: official SORRY judge on supplied held-out human responses."""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import socket
import time

R = Path('/data/HZX/Def')
O = R / 'results/audit/sorry296'
U = R / 'results/audit/unified300'

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(16*1024*1024), b''): h.update(b)
    return h.hexdigest()
def load(p): return json.loads(Path(p).read_text())
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    q = p.with_suffix('.tmp'); q.write_text(json.dumps(x, indent=2) + '\n'); q.replace(p)

def main():
    plan = load(U / 'human_reference_plan.json')
    repair = load(U / 'SORRY_worker_geometry_repair.json')
    assert repair['base_plan_sha256'] == sha(U / 'human_reference_plan.json')
    assert sha(Path(__file__)) == repair['worker_sha256']
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '0'
    assert sha(U / 'human_inputs.private.json') == plan['input_sha256']
    assert sha(O / 'official_template_parser.py') == plan['SORRY_parser_sha256']
    assert sha(R / 'repos/SORRY-Bench/data/sorry_bench/judge_prompts.jsonl') == plan['SORRY_prompt_sha256']
    assets = load(O / 'judge_download_complete.json'); modelpath = Path(assets['local_path'])
    assert assets['phase'] == 'complete_verified' and assets['revision'] == plan['SORRY_revision']
    for n, v in assets['files'].items(): assert sha(modelpath / n) == v['sha256']
    spec = importlib.util.spec_from_file_location('s300_official', O / 'official_template_parser.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.json = json  # Standard-library dependency of the exact extracted template function.
    rows = load(U / 'human_inputs.private.json'); assert len(rows) == 4400
    prompts = [{'question_id': i+1, 'turns': [r['prompt']]} for i,r in enumerate(rows)]
    responses = [{'choices': [{'turns': [r['response']]}]} for r in rows]
    dialogs, tag = module.apply_sorry_bench_judge_template(prompts, responses,
                   'ft-mistral-7b-instruct-v0.2', 'base',
                   R / 'repos/SORRY-Bench/data/sorry_bench/judge_prompts.jsonl')
    def pulse(phase, **kw):
        save(U/'SORRY_live.json', dict(utc=utc(), pid=os.getpid(), host=socket.gethostname(),
              physical_gpu=0, backend='vllm_0.6.6_bf16_eager', phase=phase, aggregate_read=False, **kw))
    pulse('loading_verified_assets')
    from vllm import LLM, SamplingParams
    model = LLM(model=str(modelpath), tokenizer=str(modelpath), dtype='bfloat16',
                disable_custom_all_reduce=True, tensor_parallel_size=1,
                enforce_eager=True, gpu_memory_utilization=0.85, hf_overrides={"head_dim": 128})
    params = SamplingParams(temperature=0, n=1, max_tokens=1024)
    def score(texts):
        outputs = model.generate(texts, params, use_tqdm=False)
        return [(v.outputs[0].text.strip(), len(v.prompt_token_ids),
                 len(v.outputs[0].token_ids)) for v in outputs]
    # First20 cases are fixed by test-file order, not chosen by their labels.
    ref = []
    for i,d in enumerate(dialogs[:20]):
        ref.extend(score([d])); pulse('reference_single20', n=i+1, total=20)
    trial = score(dialogs[:20])
    equal = [a[0] == b[0] for a,b in zip(ref,trial)]
    if all(equal): batch=20
    else:
        trial = [score([d])[0] for d in dialogs[:20]]
        assert all(a[0] == b[0] for a,b in zip(ref,trial)), 'Canonical single judge is not reproducible'
        batch=1
    gate = dict(utc=utc(), backend='vllm_0.6.6_bf16_eager', host=socket.gethostname(),
                physical_gpu=0, n=20, batch20_equal=sum(equal), chosen_batch=batch,
                passed=True, interpretation='canonical single-reference vs batch; fallback single repeat if needed',
                cases=[{'id':r['id'], 'reference_sha256':hashlib.sha256(a[0].encode()).hexdigest(),
                        'replay_sha256':hashlib.sha256(b[0].encode()).hexdigest()}
                       for r,a,b in zip(rows[:20],ref,trial)])
    save(U / 'SORRY_gate20.json', gate)
    signature={'plan_sha256':sha(U/'human_reference_plan.json'), 'worker_sha256':sha(Path(__file__)),
               'input_sha256':plan['input_sha256'], 'assets_sha256':sha(O/'judge_download_complete.json'),
               'execution_repair_sha256':sha(U/'SORRY_worker_geometry_repair.json'),
               'batch':batch, 'node':socket.gethostname(), 'backend':'vllm_0.6.6_bf16_eager'}
    started=time.monotonic()
    for begin in range(0,len(rows),batch):
        group=rows[begin:begin+batch];paths=[U/'SORRY_scores'/(r['id']+'.json') for r in group]
        if all(p.exists() for p in paths):
            assert all(load(p)['signature']==signature for p in paths);continue
        values=score(dialogs[begin:begin+batch])
        for r,p,(text,n,nt) in zip(group,paths,values):
            value=module.extract_content(tag,text)
            label=int(value) if value in [0,1] else None
            record=dict(id=r['id'],label=label,raw_parsed=value,output=text,
                        input_tokens=n,new_tokens=nt,signature=signature)
            if p.exists(): assert load(p)==record
            else: save(p,record)
        pulse('scoring_human_test', n=begin+len(group),total=4400,
              seconds_per_case=(time.monotonic()-started)/max(1,begin+len(group)))
    save(U/'SORRY_complete.json',dict(utc=utc(),n=4400,backend=signature['backend'],aggregate_read=False))
    pulse('complete_waiting_other_judges',n=4400,total=4400)

if __name__=='__main__': main()
