from u300_schedule_prepare import *
import fcntl
worker=T/'u300_new_model_short_gate17.py';worker.write_text(worker.read_text(encoding='utf-8-sig').replace("elif not expected.get('nonzero'):assert not where,where","else:assert not where,where").rstrip()+'\n');compile(worker.read_text(),str(worker),'exec')
O=R/'results/audit/crossmodel287';sys=__import__('sys');sys.path.insert(0,str(T));from crossmodel287_assets_and_render import model_path
p=U/'model_gate_schedule_rule17.json';assert not p.exists()
plan=dict(utc_frozen=utc(),worker_sha256=H(worker),batch_core_sha256=H(T/'batched_injection300.py'),engineering_source_sha256=H(U/'calibration700.private.json'),engineering20_IDs=L(U/'acceptance_generation_plan_v5.json')['IDs100'][:20],fixed_texts_sha256=H(U/'fixed_texts.private.json'),new_test_outputs=False,
 models=dict(gemma=dict(path=str(model_path('gemma')),layer=12,rho=127.72100143432617,attention='eager'),mistral=dict(path=L(O/'mistral/assets_verified_actual_path.json')['model_path'],layer=9,rho=2.3307554125785828,attention='sdpa')),
 short_gate=dict(cap32_zero_reference20=True,variants=['native','P1','P2'],zero_nohook_bytes_equal=True,canonical_diagnostic_vector='first coordinate = 0.01rho; remaining zero; cap1',position_hook_assertion='only declared prefill position changes, exactly once; decode positions unchanged',reference_scope='prospective B1 only, not historical same-batch nor long label admission'),
 remaining_DAG=['native alpha0 470 and blind refusal review','own keep60 and fixed U1 target binding','train seeds3,4,5 with existing fixed rules','trained-s3/random/alpha0 cap2400 100-prompt B8 -> B4 -> B1 label screen plus throughput/headroom','freeze accepted batch path, then independent engineering20 same-batch reference/reload check','700 calibration, WG score, alpha selection','family-specific long generation gates before tests'],
 schedule=dict(short_gates='innetGPU0 after current SORRY wave, Gemma then Mistral; wait_gpu and shared locks; no need to wait whole English/search round',remaining='native review/targets/training Nov12-13; label gate and calibration target Nov13-14, estimates contingent on passed gates',batch_gate_time_basis='at least 300 B1 cap2400 engineering outputs per model; old Qwen244 rows/hour =>1.23GPUh for B1 reference alone, plus candidate and judging; not a minutes-only gate'),
 Gemma_uncompiled_baseline=dict(complete_utc=L(O/'gemma_uncompiled_selection_complete.json')['utc'],signature=L(O/'gemma_uncompiled_selection_complete.json')['signature'],sha256=H(O/'gemma_uncompiled_selection_complete.json'),scope='470 prereview, not unified700; old automatic outputs isolated'),formal_generation_allowed=False)
save(p,plan)
commit=publish([worker,p,Path(__file__)],'Queue short Gemma/Mistral position gates and record acyclic long-gate preparation schedule')
with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json');ids={t['id'] for t in cat['tasks']}
 for n,key in enumerate(['gemma','mistral']):
  tid='prep_'+key+'_short_position_gate17';assert tid not in ids
  req=[dict(path='results/audit/unified300/rule17_publication.json',key='published',value=True)]
  if n:req.append(dict(path='results/audit/unified300/new_model_short_gates_rule17/gemma/complete.json'))
  cat['tasks'].append(dict(id=tid,priority=18+n,site='innet',gpus=[0],kind='engineering_forward_position_gate',yieldable=False,argv=['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/u300_new_model_short_gate17.py',key],requires=req))
 save(U/'ready_queue_catalog.json',cat)
save(U/'model_gate_schedule_rule17_publication.json',dict(utc=utc(),commit=commit,plan_sha256=H(p),short_gates_enqueued=True,long_label_gates_not_claimed_passed=True))
print(json.dumps(L(U/'model_gate_schedule_rule17_publication.json')))
