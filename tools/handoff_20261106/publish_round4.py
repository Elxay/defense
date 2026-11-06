from pathlib import Path
import json,hashlib,subprocess,datetime,ast
b=Path('/data/HZX/Def');repo=b/'prereg_repo';o=b/'results/audit/handoff_round4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip(),'preserve existing checkout changes'
for p in(b/'tools/handoff_20261106').glob('*.py'):ast.parse(p.read_text())
# Private sidecars keep frozen bytes intact while attaching analysis provenance.
fnsha=sha(b/'src/judge/refusal.py')
for p in list(sorted(o.rglob('*'))):
 if not p.is_file()or p.suffix not in ['.csv','.json']or p.name.endswith('.analysis_meta.json'):continue
 name=p.name.lower();parent=p.parent.name
 baseline='not_applicable'
 if parent=='guard_diagnostic'or name.endswith('_reference_gate.json'):baseline='results/audit/RERUN_v70_a0.0_b8f62434.json'
 elif name.startswith('llama'):baseline='results/audit/LEGALVALB_none.json'
 elif name.startswith('baseline'):baseline='per_row_baseline_file'
 elif name.startswith('doc246'):baseline='results/audit/WJB_BENIGN246_alpha0.json'
 elif any(s in name for s in ['qwen','preview'])or parent=='guard_v2':baseline='results/audit/LEGALVALB_qwen_a0.json'
 invalid=p.parent==o and p.name.startswith('GUARD_QWEN_')
 meta={'source_file':str(p.relative_to(b)),'source_sha256':sha(p),'refusal_fn_sha256':fnsha,'baseline_file':baseline,'validity':'INVALIDATED_GUARD_V1_DO_NOT_ANALYZE'if invalid else'see_analysis_method_and_limits','note':'analysis sidecar; original artifact bytes unchanged'}
 p.with_suffix('.analysis_meta.json').write_text(json.dumps(meta,indent=2)+'\n')
subprocess.run(['git','-C',str(repo),'fetch','origin'],check=True)
subprocess.run(['git','-C',str(repo),'merge','--ff-only','origin/main'],check=True)
names=['247_RESULTS_51_SKELETON.md','249_RESULTS_51_DRAFT.md','251_EVAL_TRAPS_DRAFT.md','252_GUARD_QWEN_EXECUTION_NOTE.md','253_ROUND4_AUDIT.md','254_FRONTIER_APPENDIX.md','255_RESULTS_53_DRAFT.md','256_DOC246_RESULTS.md','257_GUARD_PROTOCOL_REPAIR.md','258_QWEN_GUARD_RESULTS.md','POSTHOC_MODEL_REVIEW_METHOD.md','PREREG_LOG.txt']
files=[b/'docs'/n for n in names]+list((b/'tools/handoff_20261106').glob('*.py'))
allowed=[];public=[]
for p in files:
 rel=p.relative_to(b);dest=repo/rel;dest.parent.mkdir(parents=True,exist_ok=True);raw=p.read_bytes();content=raw
 if p.suffix=='.py':content=('\n'.join(x.rstrip()for x in p.read_text().splitlines()).rstrip()+'\n').encode()
 tmp=dest.with_suffix(dest.suffix+'.tmp');tmp.write_bytes(content);tmp.replace(dest);allowed.append(rel.as_posix());public.append({'file':rel.as_posix(),'sha256':sha(dest),'server_source_sha256':sha(p)})
# These two hashes are embedded in result metadata and must be byte-exact in Git.
for n in ['guard_qwen_output.py','analyze_doc246_complete.py']:
 assert sha(repo/'tools/handoff_20261106'/n)==sha(b/'tools/handoff_20261106'/n),n+' byte drift'
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'public_files':public,'private_artifacts_hashes_only':[{'file':str(p.relative_to(b)),'sha256':sha(p)}for p in sorted(o.rglob('*'))if p.is_file()and p.suffix!='.tmp'],'exclusions':'No original attack/request/response text or private per-item result data published. Guard v1 score files explicitly invalidated; validated results use guard_v2.'}
(repo/'manifests_round4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');allowed.append('manifests_round4.json')
subprocess.run(['git','-C',str(repo),'add','--',*allowed],check=True)
staged=subprocess.check_output(['git','-C',str(repo),'diff','--cached','--name-only'],text=True).splitlines();assert set(staged)<=set(allowed)and not any(x.startswith(('results/','data/','models/'))for x in staged)
subprocess.run(['git','-C',str(repo),'diff','--cached','--check'],check=True)
subprocess.run(['git','-C',str(repo),'commit','-m','Complete model annotation audit and validate Qwen Guard scoring'],check=True)
commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();subprocess.run(['git','-C',str(repo),'push','origin','HEAD:main'],check=True)
with(b/'docs/PREREG_LOG.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+' ROUND4 PUBLISHED content_commit='+commit+'; documents/scripts/hash-only manifests, no raw attacks or outputs. Historical9 labels unknown, Llama B109 full reads, Guard corrected2350 with20-reference gate, docs246292 pairs first aggregate after all complete; harmful-WJB rand1 still generating.\n')
p=repo/'docs/PREREG_LOG.txt';q=p.with_suffix('.tmp');q.write_bytes((b/'docs/PREREG_LOG.txt').read_bytes());q.replace(p)
subprocess.run(['git','-C',str(repo),'add','docs/PREREG_LOG.txt'],check=True);subprocess.run(['git','-C',str(repo),'commit','-m','Record round-four content commit and completion state'],check=True);subprocess.run(['git','-C',str(repo),'push','origin','HEAD:main'],check=True)
log_commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
result={'content_commit':commit,'log_commit':log_commit,'artifact_hashes':{n:sha(o/n)for n in ['preview12_vs_full.csv','llama_b_per_item.csv','llama_b_review.json','baseline_two_paths_corrected.csv','review_method.md','guard_qwen_thresholds.csv','doc246_results.json']},'doc247_sha256':sha(b/'docs/247_RESULTS_51_SKELETON.md'),'rubric_v2_sha256':sha(b/'results/audit/handoff_round3/rubric_v2.md')}
(o/'publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
