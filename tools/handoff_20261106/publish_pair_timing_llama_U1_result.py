"""Publish coded timing, exact numeric reconciliation and the fresh cosine result."""
from pathlib import Path
import datetime,fcntl,hashlib,json,re,shutil,subprocess
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';B=R/'results/audit/pair500';G=R/'prereg_repo';D=C/'U1_llama_seed3_check'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 now=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip();x=json.loads((D/'complete.json').read_text());assert x['steps']==40
 doc=R/'docs/287_U1_LLAMA_SEED3_RESULT.md';assert not doc.exists()
 doc.write_text(f'''# U1 fixed-cache Llama seed3 result

RecordedUTC {now}. Frozen before training in planSHA `{sha(D/'plan.json')}`. TrainingUTC {x['training_started_utc']} through {x['utc']},40steps,elapsed{x['elapsed_training_seconds']:.6f}s. Same frozen seed3 initialization, native Llama block9/norm5.21, original trainer and fixed U1 attack/keep target cache. No new val70 or test outputs generated; historical results not replaced.

Cosine to frozen same-seed vector (float64 calculation): **{x['cosine_float64']:.12f}**.
Difference L2: **{x['difference_l2']:.12f}**.
New/reference norms: {x['new_vector_norm']:.12f} / {x['reference_vector_norm']:.12f}.

This meets the user's suggested0.999 descriptive closeness reference. It is one observed fixed-cache reconstruction, not target-byte identity, a proof of target equivalence, or a quantified distribution of training nondeterminism. Future descriptions can report the cosine instead of only saying 'not verified', while retaining that limit. No threshold was loosened or target rewritten to achieve it.

ResultJSON SHA256 `{sha(D/'complete.json')}`; new vectorSHA256 `{x['vector_sha256']}`; frozen vectorSHA256 `{x['frozen_vector_sha256']}`. Vector/checkpoint contents stay private. New-model training remains subject to individual frozen refusal audits; this cosine alone does not unlock it.
''')
 models={}
 for key in ['qwen','gemma','vicuna']:
  counts={name:len(list((C/'native_selection_private'/key/name).glob('*.json')))for name in ['legal400','val70']}
  models[key]={'alpha0_counts':counts,'training_started':False}
 for key in ['qwen','gemma']:
  p=C/('qwen_norm_semantics_addendum2.json'if key=='qwen'else'gemma_preflight.json');z=json.loads(p.read_text())
  models[key]['norm_source_sha256']=sha(p)
  if key=='gemma':models[key].update(keep60_median=z['measured_residual_norm_median'],rho=z['rho'],injection_block=z['injection_block'])
  else:models[key].update(keep60_median=z['measured_residual_norm_median'],rho=z['training_vector_norm_rho'],injection_block=z['measurement_layers_zero_based'])
 models['vicuna'].update(keep60_median=None,rho=None,injection_block=12,weights_innet='official revision, complete verified')
 vd=C/'vicuna_norm_node01';vp=vd/'complete.json'
 if vp.exists():
  v=json.loads(vp.read_text());models['vicuna'].update(keep60_median=v['keep60_median'],rho=v['rho'],norm_backend=v['backend'],norm_receipt_sha256=sha(vp),norm_rows=v['n'])
 elif(vd/'controller_live.json').exists():models['vicuna']['norm_stage']=json.loads((vd/'controller_live.json').read_text())['phase']
 if(vd/'load_failure.json').exists():models['vicuna']['norm_failure']=json.loads((vd/'load_failure.json').read_text())
 sample=json.loads((C/'qwen_refusal_admission/sample_manifest.json').read_text());models['qwen'].update(refusal_samples_fixed=60,review_labels_collected=sample['review_labels_collected'])
 snapshot={'date_u':now,'models':models,'llama_seed3_complete_sha256':sha(D/'complete.json'),'GPU_inventory_innet':subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader'],text=True).splitlines(),'GPU_compute_innet':subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'],text=True).splitlines(),'GPU_inventory_node01':subprocess.check_output(['ssh','node01','nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader'],text=True).splitlines(),'GPU_compute_node01':subprocess.check_output(['ssh','node01','nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader'],text=True).splitlines(),'known_external_innet_processes':{'2763505':'other point-cloud project stage2 onGPU0','1727458':'external MTA onGPU1','2763506':'other point-cloud project stage3 onGPU3'},'external_processes_signalled':False,'new_model_training_locks_retained':True,'weights_or_raw_outputs_published':False}
 status=C/'ops_snapshot_after_U1_llama.json';assert not status.exists();status.write_text(json.dumps(snapshot,indent=2)+'\n')
 editorial=R/'paper/editorial_status_after_pair_read.json';assert not editorial.exists();editorial.write_text(json.dumps({'utc':now,'status':'numeric table awaiting user verification; previously inserted narrative abstract is an unverified draft','abstract_finalized':False,'manuscript_table_sha256':sha(R/'paper/tables/pair500_primary.tex'),'no_paper_text_or_numeric_cell_changed_in_this_reconciliation':True,'main_tex_sha256':sha(R/'paper/main.tex')},indent=2)+'\n')
 log=f'{now} U1_LLAMA_FIXED_CACHE_RESULT cosine={x["cosine_float64"]:.12f} diff_L2={x["difference_l2"]:.12f} result_SHA={sha(D/"complete.json")} result_doc_SHA={sha(doc)}; one_run_closeness_not_target_equivalence; addendum10=8_steps_complete; timing_reconciliation_doc_SHA={sha(R/"docs/290_PAIR_READ_TIMING_AND_NUMERIC_RECONCILIATION.md")}; abstract_unverified_draft; new_model_training_locks_retained.\n'
 for n in ['PREREG_LOG.txt','OPS_LOG.txt']:
  with(R/'docs'/n).open('a')as f:f.write(log)
 files=['docs/290_PAIR_READ_TIMING_AND_NUMERIC_RECONCILIATION.md','docs/287_VICUNA_NORM_LOAD_BLOCK.md',str(doc.relative_to(R)),'docs/PREREG_LOG.txt','docs/OPS_LOG.txt','paper/editorial_status_after_pair_read.json',str(status.relative_to(R)),*[str(p.relative_to(R))for p in(B/'read_order10/reconciliation').glob('*')if p.is_file()],*[str((D/n).relative_to(R))for n in ['launch.json','complete.json']],str((C/'vicuna_node01_transfer/launch.json').relative_to(R)),*['tools/handoff_20261106/'+n for n in ['pair254_reconcile_timing_and_tables.py','publish_pair_timing_llama_U1_result.py','crossmodel287_vicuna_norm_node01.py','crossmodel287_queue_vicuna_norm.py']],*['results/audit/pair500/'+n for n in ['canonical254/classifier_complete_innet.json','canonical254/hash_complete_innet.json','wildguard_pair254/queue_live.json']]]
 files +=[str(p.relative_to(R))for p in vd.glob('*.json')if '.private'not in p.name and 'live'not in p.name]
 if vp.exists():files +=[str(p.relative_to(R))for p in(vd/'rows').glob('*.json')]
 for n in files:
  assert '.private'not in n and not n.endswith(('.pt','.npy','.bin','.safetensors'));assert not re.search(r'hf_[A-Za-z0-9]{20,}',(R/n).read_text())
 with(R/'logs/prereg_publish.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
  for n in files:p=G/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
  m='manifests_pair_timing_and_U1_llama_result.json';(G/m).write_text(json.dumps({'utc':now,'files':{n:sha(G/n)for n in files},'no_raw_attack_prompt_reply_target_or_weight':True,'original_eight_receipts_unchanged':True},indent=2)+'\n')
  subprocess.run(['git','add',*files,m],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Reconcile read chronology and both estimands; report fixed-cache Llama seed3 cosine'],cwd=G,check=True);subprocess.run(['git','push','origin','main'],cwd=G,check=True)
 print(json.dumps({'date_u':now,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),'timing_report_sha256':sha(R/'docs/290_PAIR_READ_TIMING_AND_NUMERIC_RECONCILIATION.md'),'llama_result_sha256':sha(D/'complete.json'),'status_sha256':sha(status)}))
if __name__=='__main__':main()
