
from pathlib import Path
import json,hashlib,subprocess,datetime
b=Path('/data/HZX/Def');repo=b/'prereg_repo';o=b/'results/audit/handoff_round3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Sanity checks exercise real source alignments without re-reading pending experiment outcomes.
l=json.loads((o/'lmi_pairs.json').read_text());assert sum(r['cond2_only_harmful']-r['full_only_harmful']for r in l['per_seed'])==0
assert len(l['per_seed'])==5 and all(r['invalid']==0 for r in l['per_seed'])
q=json.loads((o/'qwen_paired.json').read_text());assert(q['A_only_n'],q['B_only_n'])==(0,6)
assert all(p.name.startswith('WJB_') for p in (b/'results/audit').glob('WJB_BENIGN246_*.json')) # no outcomes examined
for p in (b/'tools/handoff_20261106').glob('*.py'):compile(p.read_text(),str(p),'exec')
subprocess.run(['git','-C',str(repo),'fetch','origin'],check=True)
subprocess.run(['git','-C',str(repo),'merge','--ff-only','origin/main'],check=True)
files=[b/'docs'/n for n in ['239_ADDENDUM6_PARALLEL.md','247_RESULTS_51_SKELETON.md','249_RESULTS_51_DRAFT.md','250_ROUND3_AUDIT.md','251_EVAL_TRAPS_DRAFT.md','PREREG_LOG.txt']]
files+=list((b/'tools/handoff_20261106').glob('*.py'))
allowed=[]
for p in files:
 rel=p.relative_to(b);dest=repo/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 content=p.read_bytes()
 if p.suffix=='.py':content=('\n'.join(x.rstrip()for x in p.read_text().splitlines()).rstrip()+'\n').encode()
 temp=dest.with_suffix(dest.suffix+'.tmp');temp.write_bytes(content);temp.replace(dest);allowed.append(rel.as_posix())
r=repo/'docs/POSTHOC_LEGAL_RUBRIC_V2.md';r.write_bytes((o/'rubric_v2.md').read_bytes());allowed.append('docs/POSTHOC_LEGAL_RUBRIC_V2.md')
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'published':[{'file':f,'sha256':sha(repo/f)}for f in allowed],'private_artifacts_hashes_only':[{'file':p.relative_to(b).as_posix(),'sha256':sha(p)}for p in sorted(o.iterdir())if p.is_file()]}
(repo/'manifests_round3.json').write_text(json.dumps(manifest,indent=2));allowed.append('manifests_round3.json')
subprocess.run(['git','-C',str(repo),'add','--',*allowed],check=True)
staged=subprocess.check_output(['git','-C',str(repo),'diff','--cached','--name-only'],text=True).splitlines()
assert set(staged)<=set(allowed) and not any(x.startswith(('results/','data/','models/'))for x in staged)
subprocess.run(['git','-C',str(repo),'diff','--cached','--check'],check=True)
subprocess.run(['git','-C',str(repo),'commit','-m','Correct LMI inference and document parallel WJB schedule'],check=True)
commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
subprocess.run(['git','-C',str(repo),'push','origin','HEAD:main'],check=True)
with(b/'docs/PREREG_LOG.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+' ROUND3 PUBLISHED commit='+commit+'; safe documents/scripts/hash-only manifests; no raw outputs/attacks; cond2 uncertainty corrected, addendum6 parallelization logged before new-condition outcome reading.\n')
dest=repo/'docs/PREREG_LOG.txt';tmp=dest.with_suffix('.tmp');tmp.write_bytes((b/'docs/PREREG_LOG.txt').read_bytes());tmp.replace(dest)
subprocess.run(['git','-C',str(repo),'add','docs/PREREG_LOG.txt'],check=True)
subprocess.run(['git','-C',str(repo),'commit','-m','Record round-three published content commit'],check=True)
subprocess.run(['git','-C',str(repo),'push','origin','HEAD:main'],check=True)
tip=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
result={'content_commit':commit,'log_commit':tip,'addendum6_sha256':sha(b/'docs/239_ADDENDUM6_PARALLEL.md'),'baseline_csv_sha256':sha(o/'baseline_two_paths.csv'),'rubric_v2_sha256':sha(o/'rubric_v2.md'),'lmi_pairs_sha256':sha(o/'lmi_pairs.json'),'refusal_fn_sha256':sha(b/'src/judge/refusal.py')}
(o/'publication.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
