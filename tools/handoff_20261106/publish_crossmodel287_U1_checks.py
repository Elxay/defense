"""Publish coded U1 checks and keep manuscript protocol descriptions current."""
from pathlib import Path
import datetime,fcntl,hashlib,json,re,shutil,subprocess
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';G=R/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();note=C/'U1_Qwen_wording_cap_note.json';assert not note.exists()
 rows=[]
 for ident in ['pair_jbbh_0009','pair_jbbh_0015']:
  p=C/'qwen_private/fit_alpha0'/(ident+'.json');x=json.loads(p.read_text());assert x['new_tokens']==512 and x['eos']is False
  rows.append({'id':ident,'source_sha256':sha(p),'new_tokens':x['new_tokens'],'eos':x['eos'],'v2_refusal':x['v2_refusal']})
 note.write_text(json.dumps({'utc':now,'rows':rows,'interpretation':'Both native-alpha0 v2-positive replies hit the512 generation cap withoutEOS; length/wording comparison is descriptive and truncation-limited. This does not change U1 targets or certify complete task refusal.','no_raw_output_text':True},indent=2)+'\n')
 report=R/'docs/287_U1_TOKENIZATION_AND_EXECUTION_CHECK.md'
 with report.open('a')as f:f.write(f'\n## Supplementary cap metadata check\n\nUTC {now}. Both native Qwen v2-positive fit12 replies have stored new_tokens=512 and eos=False. The two corresponding U1 targets each encode to8 Qwen tokens. Length and wording comparisons therefore include a truncation limitation and are not a style superiority claim or a full-text refusal validation. SupplementSHA256 `{sha(note)}`.\n')
 setup=R/'paper/sections/03_setup.tex';s=setup.read_text();old='\\paragraph{Target-source variants (pending).} Native donor-target feasibility is an operational rule, set after the Qwen baseline was known. The failed Qwen native branch is preserved; a separately specified arm transfers all twelve cached Llama donor-generated target continuations. Other ports use the same fixed failure branch. Target source and different selected operating points preclude treating these as identical native-method replications. Fresh model-specific refusal audits precede training.'
 new='\\paragraph{Unified fixed targets for pending ports.} Before any new-model vector training, a versioned amendment replaced the conditional native-donor branch with the same twelve fixed Llama donor-generated target texts for Qwen, Gemma and Vicuna. Each model retains its own benign keep continuations. The failed Qwen native-target gate is preserved as a superseded diagnostic, not lowered or erased. The fixed texts are an old-recipe Llama reconstruction; their byte identity to every historical Llama training run is not established. These are uniform text-transfer ports, not certified replicas of the historical native-target runs. Fresh model-specific refusal audits still precede training. Gemma system baselines use a user-turn prefix because its native template rejects a system role.'
 assert old in s or new in s;s=s.replace(old,new);setup.write_text(s)
 limits=R/'paper/sections/06_limitations.tex';s=limits.read_text();old='For pending model ports, the native donor-target gate and subsequent Llama-target-transfer amendment were decided after the Qwen baseline was known. The original failed gate is preserved. No pending port or target-transfer result is counted as a completed model replication.'
 new='For pending model ports, the native donor-target gate and its subsequent replacement by uniform fixed Llama targets were decided after the Qwen baseline was known but before new-model vector training. The original failed gate is preserved. Llama-style target wording may differ from a new model\'s natural refusals and may favor the v2 rule; WildGuard refusal is reported alongside it. The fixed target cache is a reconstruction, not a certificate that every historical Llama seed used byte-identical targets. No pending port or target-transfer result is counted as a completed model replication.'
 assert old in s or new in s;s=s.replace(old,new);limits.write_text(s)
 # Reproduce receipt rows from immutable files, without rereading any inference.
 records=[]
 for i in range(1,9):
  p=R/'results/audit/pair500/read_order10/ordered_results'/f'{i:02d}.json';x=json.loads(p.read_text());records.append({'step':i,'utc':x['utc'],'sha256':sha(p),'previous_sha256':x['previous_receipt_sha256']})
 receipts=C/'U1_requested_PAIR_read_receipts.json';assert not receipts.exists();receipts.write_text(json.dumps({'utc':now,'source':'previously completed immutable read; no new inference or numerical reread','steps':records},indent=2)+'\n')
 files=['docs/287_U1_TOKENIZATION_AND_EXECUTION_CHECK.md','paper/sections/03_setup.tex','paper/sections/06_limitations.tex','tools/handoff_20261106/crossmodel287_U1_tokenization.py','tools/handoff_20261106/publish_crossmodel287_U1_checks.py']
 files +=[str((C/n).relative_to(R))for n in ['U1_tokenization_check.json','U1_tokenization_rows.csv','U1_active_execution_binding.json','U1_Qwen_wording_cap_note.json','U1_requested_PAIR_read_receipts.json']]
 log=f'{now} CROSSMODEL287_U1_CHECKS_PUBLISHED report_SHA={sha(report)} tokenization36/36_no_UNK_or_target_control; Qwen_native_two_refusal_outputs_hit512_noEOS; cap_note_SHA={sha(note)} active_binding_U1_only; all_new_model_training_awaits_refusal_admission; legacy_conditional_sources_historical_only.\n'
 for name in ['PREREG_LOG.txt','OPS_LOG.txt']:
  with(R/'docs'/name).open('a')as f:f.write(log)
  files.append('docs/'+name)
 for n in files:
  assert '.private'not in n
  text=(R/n).read_text();assert not re.search(r'hf_[A-Za-z0-9]{20,}',text)
 with(R/'logs/prereg_publish.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
  for n in files:p=G/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
  name='manifests_crossmodel287_U1_checks.json';(G/name).write_text(json.dumps({'utc':now,'files':{n:sha(G/n)for n in files},'no_raw_prompt_response_or_target_text':True,'new_models_trained':False,'tokenization_CPU_only':True},indent=2)+'\n')
  subprocess.run(['git','add',*files,name],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Verify U1 target tokenization across three model templates and bind Qwen payload'],cwd=G,check=True);subprocess.run(['git','push','origin','main'],cwd=G,check=True)
 print(json.dumps({'utc':now,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),'report_sha256':sha(report),'tokenization_sha256':sha(C/'U1_tokenization_check.json'),'receipt_list_sha256':sha(receipts),'raw_text_published':False}))
if __name__=='__main__':main()
