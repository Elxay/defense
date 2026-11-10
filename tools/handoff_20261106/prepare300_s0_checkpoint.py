from pathlib import Path
import datetime, hashlib, json, random

R = Path('/data/HZX/Def')
U = R / 'results/audit/unified300'
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, obj):
    assert not p.exists(), p
    p.write_text(json.dumps(obj, indent=2) + '\n')
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
rows = json.loads((U / 'calibration700.private.json').read_text())
rng = random.Random(20261241)
panels = {}
for kind, n in [('adversarial_harmful', 50), ('adversarial_benign', 25), ('vanilla_benign', 25)]:
    population = sorted(r['id'] for r in rows if r['kind'] == kind)
    panels[kind] = rng.sample(population, n)
ids100 = sum(panels.values(), [])
ids32 = panels['adversarial_harmful'][:16] + panels['adversarial_benign'][:8] + panels['vanilla_benign'][:8]
assert len(set(ids100)) == 100 and len(set(ids32)) == 32
qwen = json.loads((R / 'results/audit/crossmodel287/protocol.json').read_text())['models']['qwen']
models = {
    'llama': {'path': '/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659', 'layer': 9},
    'qwen': {'path': '/data/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/' + qwen['revision'], 'layer': 8},
}
for spec in models.values():
    p = Path(spec['path'])
    assert (p / 'config.json').exists()
    spec['asset_interface_sha256'] = {x.name: sha(x) for x in p.iterdir() if x.name in [
        'config.json', 'generation_config.json', 'tokenizer_config.json', 'tokenizer.json', 'model.safetensors.index.json']}
plan = {
    'utc_frozen': now, 'stage': 'S0 engineering, not final S1',
    'seed': 20261241, 'calibration_sha256': sha(U / 'calibration700.private.json'),
    'panel100_by_type': panels, 'acceptance_ids100': ids100, 'engineering_ids32': ids32,
    'tie_break_hash': {k: hashlib.sha256(('20261240:' + k).encode()).hexdigest() for k in ids32},
    'models': models, 'batch_grid': [1, 4, 8, 16, 32], 'caps': [120, 2400],
    'condition': 'alpha0 engineering only', 'attention_backend': 'sdpa for Llama/Qwen, all B identical',
    'candidate_selection': 'smallest >=80% best tokens/s with conservative >=3GiB headroom, provisional until 100x3 labels',
    'frozen_new_engineering_outputs': 0, 'test_generation_allowed': False,
    'worker_sha256': sha(R / 'tools/handoff_20261106/unified300_throughput.py'),
    'batch_core_sha256': sha(R / 'tools/handoff_20261106/batched_injection300.py'),
    'legacy_core_sha256': sha(R / 'src/gen/common.py'),
    'outputs_private': True, 'only_counts_hashes_and_timing_public': True,
}
save(U / 'throughput_plan.json', plan)
doc = R / 'docs/300_UNIFIED_PROTOCOL.md'
text = doc.read_text()
text = text.replace('- [ ] 三判官human test成绩及各20门。', '- [x] 三判官human test4400成绩及各20门；结果只报告，不改措辞规则。')
text = text.replace('- [ ] 两个效用集200题ID、ARC token与GSM解析验收。', '- [x] 两个效用集200题ID及四模型ARC单token编码已固定；未作模型前向。\n- [ ] GSM执行解析与ARC注入前向验收。')
text = text.replace('人工三判官仍运行中、尚未汇总。', '补入keep60后并集仍为19行；700校准保留全部行，归一化基础请求为697组。')
text += '\nS0执行补齐（' + now + '）：human test4400已按预冻读取脚本汇总：SORRY accuracy=91.7045%、κ=0.808166；HB accuracy=88.8636%、κ=0.711797；WG accuracy下界=74.8864%、κ(valid)=0.383000，回复有害/回复拒答各4个INVALID。SORRY/HB完成于06:26:33/06:22:03UTC，WG最后分片06:35:38UTC；读取晚于全部完成，结果SHA `36d106561e8ba1f79b2e18a08fa9e9e6b005c02d57afeca35393b63fd4d92b94`。WG有害与人工履行是不同构念，不据一致率剔除或替换。\n'
text += '\n批吞吐工程面板使用校准源固定100行（50有害、25包装良性、25vanilla良性），种子20261241；其中16+8+8的32行用于B1/4/8/16/32、120/2400两上限实测。当前只alpha0、仅工程，尚不能放行正式批生成。Llama/Qwen本轮工程后端统一HF bf16 SDPA；批次接口在版本化独立文件，不改旧单条函数。单条零向量20门、历史同批复现及100×3标签门分别记账，不相互替代。面板及worker/core SHA见throughput_plan.json，生成前冻结。\n'
doc.write_text(text)
active = json.loads((U / 'active_protocol.json').read_text())
active.update(utc=now, master_candidate_sha256=sha(doc), S1_frozen=False,
              new_test_generation_allowed=False, pending=['batch throughput and 100x3 label admission', 'search adapters and zero20 gates', 'executable utility admission'])
(U / 'active_protocol.json').write_text(json.dumps(active, indent=2) + '\n')
record = {'utc': now, 'human_result_sha256': sha(U / 'human_agreement_results.json'),
    'human_summary_assembly_utc': json.loads((U / 'human_agreement_results.json').read_text())['utc'],
    'scope': 'S0 reference only; no new target test effect',
    'overlap_complete_sha256': sha(U / 'overlap_flags_complete.json'),
    'calibration_groups_sha256': sha(U / 'calibration_request_groups.json'),
    'utility_manifest_sha256': sha(U / 'utility200_manifest.json'),
    'throughput_plan_sha256': sha(U / 'throughput_plan.json'),
    'master_candidate_sha256': sha(doc), 'S1_frozen': False}
save(U / 'S0_checkpoint_20261110T0930.json', record)
line = now + ' unified300 S0 human reference read after all three complete/gates; result=' + record['human_result_sha256'] + '; SORRY acc=.917045 kappa=.808166 HB acc=.888636 kappa=.711797 WG acc_lower=.748864 valid_kappa=.383000 INVALID=4. No judge dropped. Throughput panel frozen with zero engineering outputs; final S1/test lock remains closed; candidate=' + sha(doc) + '\n'
for name in ['OPS_LOG', 'PREREG_LOG.txt']:
    with (R / 'docs' / name).open('a') as f:
        f.write(line)
print(json.dumps(record, indent=2))
