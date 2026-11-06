from pathlib import Path
import json,hashlib,subprocess,datetime,ast
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round5';repo=b/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pending=subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).splitlines()
assert all(x[3:].startswith(('docs/','tools/handoff_20261106/','night/'))for x in pending),'preserve non-publication checkout edits' # resume only this attempt's known allowlisted copy set
assert json.loads((o/'validation.json').read_text())['passed']
L=json.loads((o/'llama_b_pair_summary.json').read_text());assert L['completed_before_deadline']
for p in(b/'tools/handoff_20261106').glob('round5*.py'):ast.parse(p.read_text())
for p in list(o.iterdir()):
 if not p.is_file()or p.suffix not in ['.csv','.json']or p.name.endswith('.analysis_meta.json')or'_live'in p.name:continue
 name=p.name;baseline='not_applicable'
 if name.startswith('wjb_'):baseline='results/hfjudge/JUDGE_HF_wjb_a0_innet_round2'
 elif name.startswith('llama_'):baseline='results/audit/LEGALVALB_none.json'
 elif name.startswith(('handoff12','qwen_')):baseline='results/audit/LEGALVALB_qwen_a0.json'
 elif name.startswith(('cosine','vanilla')):baseline='results/audit/WJB_BENIGN246_alpha0.json'
 elif name.startswith('val70_'):baseline='results/audit/JUDGE_RERUN_v70_a0.0_b8f62434.json'if'legacy'in name else'results/hfjudge/JUDGE_HF_RERUN_v70_a0.0_b8f62434.json'
 meta={'source_file':str(p.relative_to(b)),'source_sha256':sha(p),'refusal_fn_sha256':sha(b/'src/judge/refusal.py'),'baseline_file':baseline,'note':'source identity only; no original generation/cache bytes modified; model labels not human calibration'}
 p.with_suffix('.analysis_meta.json').write_text(json.dumps(meta,indent=2)+'\n')
subprocess.run(['git','-C',str(repo),'fetch','origin'],check=True);subprocess.run(['git','-C',str(repo),'merge','--ff-only','origin/main'],check=True)
docs=['239_ADDENDUM7.md','250_BENIGN_SEEDS_PREREG.md','250_ADDENDUM_ANALYSIS_SET.md','246_ADDENDUM_SUPPLEMENTS.md','249_RESULTS_51_DRAFT.md','251_EVAL_TRAPS_DRAFT.md','255_RESULTS_53_DRAFT.md','259_HANDOFF_ROUND5_AUDIT.md','260_WJB_FLIP_REVIEW.md','261_LLAMA_B_PAIR_AND_TAIL.md','PREREG_LOG.txt']
files=[b/'docs'/n for n in docs]+list((b/'tools/handoff_20261106').glob('round5*.py'))+[Path(__file__)]+[b/'night'/n for n in ['wjb_treat.py','wjb_treat_innet.py','s0check20.py','alpha0_check20.py','generate_pairs_seeds.py']]
allowed=[];pub=[]
for p in files:
 rel=p.relative_to(b);dest=repo/rel;dest.parent.mkdir(parents=True,exist_ok=True);content=p.read_bytes()
 if p.suffix=='.py'and p.parent.name!='night':content=('\n'.join(x.rstrip()for x in p.read_text().splitlines()).rstrip()+'\n').encode()
 q=dest.with_suffix(dest.suffix+'.tmp');q.write_bytes(content);q.replace(dest);allowed.append(str(rel));pub.append({'file':str(rel),'sha256':sha(dest),'server_source_sha256':sha(p)})
for name in ['wjb_treat.py','wjb_treat_innet.py']:assert sha(repo/'night'/name)==sha(b/'night'/name)
assert sha(repo/'tools/handoff_20261106/round5_judge_seeds.py')==sha(b/'tools/handoff_20261106/round5_judge_seeds.py')
manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'public_files':pub,'private_artifacts_hashes_only':[{'file':str(p.relative_to(b)),'sha256':sha(p)}for p in sorted(o.iterdir())if p.is_file()and'_live'not in p.name],'excluded':'raw attacks, prompts, generated outputs and private per-item tables are not uploaded; live future progress intentionally not hashed as immutable','future_seed_results_read':False}
(repo/'manifests_round5.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');allowed.append('manifests_round5.json')
subprocess.run(['git','-C',str(repo),'add','--',*allowed],check=True);staged=subprocess.check_output(['git','-C',str(repo),'diff','--cached','--name-only'],text=True).splitlines();assert set(staged)<=set(allowed)and not any(x.startswith(('results/','data/','models/'))for x in staged)
subprocess.run(['git','-C',str(repo),'diff','--cached','--check'],check=True);subprocess.run(['git','-C',str(repo),'commit','-m','Audit WJB full-output flips and reconcile paired evaluation sources'],check=True)
commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();subprocess.run(['git','-C',str(repo),'push','origin','HEAD:main'],check=True)
with(b/'docs/PREREG_LOG.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+' ROUND5_PUBLISHED content_commit='+commit+' docs/scripts/hash-only manifests; no raw attack or generated text. Llama B paired+tail reads completed21:13JST before22:30. 85 WJB flip outputs full-read with ranges. Correctedreference-top5 DD6.62; preserved9 historicalunknown labels; HF baseline63/70 vs vLLM62+1INVALID distinguished. Future s5-s7 effect scores not inspected; registered idleGPU2/3 pipeline pending generation completion.\n')
p=repo/'docs/PREREG_LOG.txt';q=p.with_suffix('.tmp');q.write_bytes((b/'docs/PREREG_LOG.txt').read_bytes());q.replace(p)
subprocess.run(['git','-C',str(repo),'add','docs/PREREG_LOG.txt'],check=True);subprocess.run(['git','-C',str(repo),'commit','-m','Record round-five publication and predeadline reading evidence'],check=True);subprocess.run(['git','-C',str(repo),'push','origin','HEAD:main'],check=True)
result={'content_commit':commit,'log_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),'artifact_hashes':{n:sha(o/n)for n in ['wjb_s0_flips58.csv','wjb_s3_unhit15.csv','wjb_s4_unhit12.csv','llama_b_paired400.csv','llama_tail60_review.json','handoff12_reconciled.csv','qwen_guard_A_replace_check.json','cosine_and_exclusions.json','vanilla_two_review.json','generation_snapshot_final.json']},'doc_hashes':{n:sha(b/'docs'/n)for n in docs if n!='PREREG_LOG.txt'}}
(o/'publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
