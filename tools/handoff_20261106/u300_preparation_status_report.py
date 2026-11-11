from pathlib import Path
import collections,datetime,json,pwd,subprocess
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
O=R/'results/audit/crossmodel287';S=L(U/'ready_queue/state.json');C=L(U/'ready_queue_catalog.json')
metadata={}
for key,rel in [('gemma_norm','gemma_eager_norm.json'),('gemma_base','gemma_uncompiled_selection_complete.json'),
 ('gemma_review','gemma_admission18/plan.json'),('gemma_WG','gemma_admission18/WG_complete.json'),
 ('mistral_norm','mistral/norm_complete.json'),('mistral_render','mistral/assets_verified_actual_path.json')]:
 p=O/rel;metadata[key]=dict(path=str(p.relative_to(R)),sha256=H(p),keys=list(L(p)))
g=L(O/'gemma_eager_norm.json');m=L(O/'mistral/norm_complete.json');review=L(O/'gemma_admission18/plan.json')
assert not review['model_review_labels_collected']
assert not list((U/'ready_generated').glob('gemma/*/*/complete.json'))
assert not list((U/'ready_generated').glob('mistral/*/*/complete.json'))
models=[dict(model='Gemma-2-9B-it',norm=dict(done=True,layer=12,M=g['median'],rho=g['rho']),
 baseline=dict(legacy_legal400=400,legacy_val70=70,legacy_complete_utc=L(O/'gemma_uncompiled_selection_complete.json')['utc'],unified700_complete=False),
 render=dict(done=True,attention='eager, compilation disabled',AB='prepend user turn; native system unsupported'),
 refusal_review=dict(WG_scoring_N=L(O/'gemma_admission18/WG_complete.json')['n'],blind_samples=60,model_review_done=False,human_calibrated=False),
 vectors=dict(trained=0,planned=3,seeds=[3,4,5]),calibration=dict(unified700_started=False,alpha_selected=False)),
 dict(model='Mistral-7B-Instruct-v0.3',norm=dict(done=True,layer=9,M=m['keep60_median'],rho=m['rho']),
 baseline=dict(legacy_470_complete=False,unified700_complete=False,admitted_queue_task='prep_mistral_native_baseline_v1'),
 render=dict(done=True,attention='sdpa',AB='system merged inside INST user instruction',U1_tokenization_checked=True),
 refusal_review=dict(complete=False,samples_pending_baseline=True),
 vectors=dict(trained=0,planned=3,seeds=[3,4,5]),calibration=dict(unified700_started=False,alpha_selected=False))]
timing=dict(meaning='Scheduling targets, not execution promises; gates remain mandatory',
 first_card='After Llama English prefix_P2 s5 complete and innetGPU2 available via wait_gpu. Current ETA scenarios Nov12 midday-afternoon; fallback Nov13-Nov14 if higher-priority jobs intervene.',
 Gemma_review='CPU blind annotation pending; no GPU dependency; priority next preparation step.',
 Mistral_baseline='First admitted released card; task registered, not yet running.',
 vector_training='After fixed U1 plus own keep60 targets and refusal-admission gates; target Nov13.',
 unified700_calibration='After three vectors and per-model execution gates; target Nov13-Nov14, not waiting for searches/whole first round.')
assets=O/'mistral/assets_verified_actual_path.json';a=L(assets)
assert isinstance(a['files'],dict)
assert all(isinstance(v,str) or 'sha256' in v for v in a['files'].values())
assert len([p for p in Path(a['model_path']).glob('model-*.safetensors')])>=3
ex=U/'pilot10_diagnostic_publication_exclusion.json'
save(ex,dict(utc=utc(),scope='n10 independent pilot diagnostic summaries only',
 source_read_receipts=[H(U/'PAIR_alpha0_independent_replay/diagnostic_read_receipt.json'),H(U/'TAP_alpha0_independent_replay/diagnostic_read_receipt.json')],
 paper_result_tables_allowed=False,formal_88_inclusion_of_same_behavior_IDs_retained=True,
 no_early_no_dynamic_range_claim=True,rule16_sha256=H(U/'search_active_cell_budget_rule16.json')))
save(U/'Gemma_Mistral_preparation_status_20261111.json',dict(utc=utc(),models=models,timing=timing,evidence=metadata,
 diagnostic_only_legacy_outputs_not_unified_calibration=True))
# GPU inventory returns only accounts, registered task IDs, PIDs and command
# basenames; never argument strings or environment variables.
probe=T/'u300_gpu_project_inventory.py'
code='''from pathlib import Path
import json,pwd,subprocess
rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().splitlines()
procs=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'],text=True).strip().splitlines();ps=[]
for row in procs:
 if not row.strip():continue
 uuid,pid,mem=map(str.strip,row.split(','));p=Path('/proc')/pid
 try:
  status=p.joinpath('status').read_text();uid=int(next(x for x in status.splitlines() if x.startswith('Uid:')).split()[1]);args=p.joinpath('cmdline').read_bytes().split(bytes([0]));scripts=[Path(x.decode(errors='replace')).name for x in args if x.endswith(b'.py')]
  command=scripts[0] if scripts else p.joinpath('comm').read_text().strip();account=pwd.getpwuid(uid).pw_name
 except OSError:command='exited';account=None
 ps.append(dict(uuid=uuid,pid=int(pid),memory_MiB=mem,account=account,command_basename=command))
out=[]
for row in rows:
 i,uuid,mem,util=map(str.strip,row.split(','));out.append(dict(card=int(i),uuid=uuid,memory_MiB=int(mem),utilization=int(util),processes=[p for p in ps if p['uuid']==uuid]))
print(json.dumps(out))
'''
probe.write_text(code);compile(code,str(probe),'exec')
subprocess.run(['scp',str(probe),'node01:/home/dell/Def/tools/handoff_20261106/'+probe.name],check=True,capture_output=True)
cards=[]
for site in ['innet','node01']:
 cmd=['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(probe)] if site=='innet' else ['ssh','node01','/data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/'+probe.name]
 rows=json.loads(subprocess.check_output(cmd,text=True))
 for row in rows:
  registered=[dict(task=k,runner_pid=v.get('runner_pid')) for k,v in S['tasks'].items() if v['state']=='running' and v['site']==site and row['card'] in v['gpus']]
  row.update(site=site,registered=registered,project='external/excluded' if site=='innet' and row['card']==1 else 'defense' if registered else 'unregistered/idle')
  cards.append(row)
save(U/'GPU_project_status_rule16.json',dict(utc=utc(),controller_utc=S['utc'],cards=cards))
files=[U/'Gemma_Mistral_preparation_status_20261111.json',U/'GPU_project_status_rule16.json',ex,probe,Path(__file__),
 T/'u300_generation_matrix_v3.py',T/'unified300_generation_metadata_snapshot_v2.py',T/'u300_active_search_budget_selector.py']
commit=publish(files,'Audit model prerequisites, register release-triggered preparation and exclude n10 diagnostic summaries from paper tables')
print(json.dumps(dict(commit=commit,models=models,timing=timing,cards=cards)))
