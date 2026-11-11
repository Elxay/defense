from pathlib import Path
import json
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
O=R/'results/audit/crossmodel287';ap=O/'mistral/assets_verified_actual_path.json';ip=O/'native_selection_inputs.private.json'
assert L(ap)['all3_weights_verified'];inputs=L(ip);assert len(inputs['legal400'])==400 and len(inputs['val70'])==70
plan=U/'mistral_prereview_baseline_plan.json';assert not plan.exists()
save(plan,dict(utc_frozen=utc(),worker_sha256=H(T/'u300_mistral_prereview_baseline.py'),assets_relative=str(ap.relative_to(R)),
 assets_sha256=H(ap),inputs_relative=str(ip.relative_to(R)),inputs_sha256=H(ip),layer_zero_based=9,attention='sdpa',dtype='bf16',
 legal_batch=8,legal_cap=120,val_batch=1,val_cap=2400,scope='Training-prerequisite alpha0 only; old val70/legal388 review, not unified700 or main test',
 training_locked_until_review=True,first_native_zero20_gate=True,statistical_results_read=False))
commit=publish([plan,T/'u300_mistral_prereview_baseline.py',Path(__file__),T/'u300_active_search_budget_selector.py'],
 'Prepare missing Mistral native prereview baseline for first released card without changing calibration')
receipt=U/'model_prerequisite_queue_publication.json';save(receipt,dict(utc=utc(),published=True,commit=commit))
C=U/'ready_queue_catalog.json';cat=L(C)
# Lower priority than existing generation and scoring; fixed GPU2 becomes eligible
# once a first model's English static family is complete and the GPU is released.
requires=[dict(path=str(receipt.relative_to(R)),key='published',value=True),
 dict(path='results/audit/unified300/ready_generated/llama/prefix_P2/s5/complete.json')]
cat['tasks'].append(dict(id='prep_mistral_native_baseline_v1',priority=150,site='innet',gpus=[2],kind='model_training_prerequisite',
 yieldable=True,sync_relpath='results/audit/unified300/mistral_native_prereview_v1',
 argv=['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/u300_mistral_prereview_baseline.py'],requires=requires))
save(C,cat)
print(json.dumps(dict(commit=commit,plan_sha256=H(plan),trigger='Llama prefix_P2 s5 complete, GPU2 free and wait_gpu',
 no_training_or_main_calibration_started=True)))
