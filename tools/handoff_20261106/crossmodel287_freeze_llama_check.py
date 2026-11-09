from pathlib import Path
import datetime,fcntl,hashlib,json,shutil,subprocess
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';D=C/'U1_llama_seed3_check';G=R/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=True);assert not(D/'plan.json').exists();now=datetime.datetime.now(datetime.timezone.utc).isoformat();old=json.loads((R/'results/style_intervention/old_recipe_targets.json').read_text());worker=R/'tools/handoff_20261106/crossmodel287_U1_llama_seed3.py'
 plan={'utc':now,'seed':3,'teacher_file':'results/style_intervention/old_recipe_targets.json','teacher_sha256':sha(R/'results/style_intervention/old_recipe_targets.json'),'old_trainer_sha256':sha(R/'stage136/keep60_seed.py'),'worker_sha256':sha(worker),'initialization_file':old['initials']['3']['file'],'initialization_sha256':old['initials']['3']['npy_sha256'],'frozen_vector_sha256':sha(R/'results/audit/runs/block10_keep60_s3/v.npy'),'same_40_steps_lr0_005_keep_weight0_075':True,'generate_new_targets':False,'generate_eval_outputs':False,'physical_gpu':2,'launch_job_wait_gpu_2000MiB_shared_flock_required':True,'allocation_deadline_utc':'2026-11-09T15:00:00+00:00','read_cosine_only_after_complete':True,'interpretation':'Report cosine and L2 distance to frozen same seed; >=0.999 is the user-suggested descriptive closeness reference, not a proof of target equivalence or quantified training noise. Preserve every result.','new_model_training_waits_for_this_check_and_individual_refusal_admission':True}
 (D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 doc=R/'docs/287_U1_LLAMA_SEED3_RETRAIN_CHECK.md';doc.write_text(f'''# Fixed U1 target cache: one Llama seed3 retrain

FrozenUTC {now}, before this fresh training run or cosine. Same historical trainer, initialization, frozen model/revision, layer9, norm5.21,40Adam steps,lr0.005,12fixed U1 fit targets and60cached native Llama keep continuations at0.075. Only the on-the-fly target-generation stage is replaced by the signed existing cache. New output directory prevents overwriting historical vectors or metadata. No new attacks, val70 or test inference.

Report raw signed cosine in float64 and vector difference L2 to the frozen seed3. User's >=0.999 is a descriptive closeness reference, not an empirically calibrated equivalence margin. Even a high cosine cannot establish byte identity of unavailable historical targets, general target equivalence, or a training-variance distribution from one run. A discrepancy remains a discrepancy, with no target editing or re-search to pass.

Use registered launch_job, shared GPU2 lock, unchanged memory gate and atomic optimizer/vector/receipt files. Checkpoint after every step and preserve RNG state. If allocation ends at15:00UTC, stop at a step boundary and preserve the checkpoint; no silent use beyond the allocation. New-model vector training awaits this comparison and each model's addendum4 refusal admission. No historical criterion or main Llama result is revised.

PlanSHA256 `{sha(D/'plan.json')}`. WorkerSHA256 `{sha(worker)}`. TargetCacheSHA256 `{plan['teacher_sha256']}`.
''')
 for n in ['PREREG_LOG.txt','OPS_LOG.txt']:
  with(R/'docs'/n).open('a')as f:f.write(f'{now} U1_LLAMA_SEED3_CHECK_FROZEN plan_SHA={sha(D/"plan.json")} doc_SHA={sha(doc)}; before_fresh_retrain; not_target_byte_equivalence; new_model_training_still_locked.\n')
 files=[str(p.relative_to(R))for p in [doc,D/'plan.json',worker,R/'tools/handoff_20261106/crossmodel287_freeze_llama_check.py']]+['docs/PREREG_LOG.txt','docs/OPS_LOG.txt']
 with(R/'logs/prereg_publish.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
  for n in files:p=G/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
  subprocess.run(['git','add',*files],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Specify a fresh fixed-cache Llama seed3 check before model-port training'],cwd=G,check=True);subprocess.run(['git','push','origin','main'],cwd=G,check=True)
 print(json.dumps({'utc':now,'plan_sha256':sha(D/'plan.json'),'doc_sha256':sha(doc),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip()}))
if __name__=='__main__':main()
