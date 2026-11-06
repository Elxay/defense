
from pathlib import Path
import json,csv,hashlib,datetime,subprocess
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round2';repo=b/'prereg_repo'
data=json.loads((o/'qwen_counts.json').read_text())
rows=list(csv.DictReader((o/'qwen_per_item.csv').open()))
for r in data['summary']:
 subset=[x for x in rows if x['condition']==r['condition']and x['base_v2']=='False'and (r['fixed_denominator']==392 or x['base_v3_existing']=='False')]
 r['rule_v2_union_v3_new']=sum(x['v2']=='True'or x['v3_existing']=='True'for x in subset)
 assert len(subset)==r['fixed_denominator']
(o/'qwen_counts.json').write_text(json.dumps(data,indent=2))
with (b/'docs/248_ROUND2_AUDIT.md').open('a') as f:
 f.write('\n## 粗筛RA与既有规则重叠\n\n'+(o/'coarse_ra_overlap.json').read_text()+'\n不能把RA总数视为FN；B_replace 13条中7条v2已捕获，新增漏判6条。基线RA2条均已由v2捕获。\n')
 f.write('\n391/392口径完整计数：\n'+json.dumps(data['summary'],ensure_ascii=False)+'\n')
 f.write('\n同机补判全量跨机核对：\n'+(o/'wjb_cross_host_check.json').read_text()+'\n')
files=[]
for p in (b/'docs').iterdir():
 if p.is_file()and((p.name[:3].isdigit()and int(p.name[:3])>=230)or p.name=='PREREG_LOG.txt'):files.append(p)
files+=list((b/'tools/handoff_20261106').glob('*.py'))
files +=[b/rel for rel in ['src/gen/common.py','src/judge/refusal.py','src/eval/legal_val_batch.py','src/eval/legal_val_eval.py','night/qwen_ab_additions.py']]
allowed=['docs/POSTHOC_LEGAL_RUBRIC.md']
for p in files:
 dest=repo/p.relative_to(b);dest.parent.mkdir(exist_ok=True,parents=True);tmp=dest.with_suffix(dest.suffix+'.tmp');tmp.write_bytes(p.read_bytes());tmp.replace(dest);allowed.append(p.relative_to(b).as_posix())
rub=repo/'docs/POSTHOC_LEGAL_RUBRIC.md';tmp=rub.with_suffix('.tmp');tmp.write_bytes((o/'rubric.md').read_bytes());tmp.replace(rub)
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'published_files':[{'file':p.relative_to(b).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in files],
 'private_artifacts_hashes_only':[{'file':p.relative_to(b).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(o.iterdir())if p.is_file()]}
(repo/'manifests_round2.json').write_text(json.dumps(manifest,indent=2));allowed.append('manifests_round2.json')
subprocess.run(['git','-C',str(repo),'add','--',*allowed],check=True)
staged=subprocess.run(['git','-C',str(repo),'diff','--cached','--name-only'],text=True,capture_output=True,check=True).stdout.splitlines()
assert set(staged)<=set(allowed)
assert all(not p.startswith(('results/','data/','models/'))for p in staged)
assert all(p.startswith(('docs/','tools/','src/','night/'))or p=='manifests_round2.json'for p in staged)
(o/'push_allowlist.json').write_text(json.dumps(staged,indent=2))
print('SAFE_STAGED',len(staged))
subprocess.run(['git','-C',str(repo),'diff','--cached','--check'],check=True)
subprocess.run(['git','-C',str(repo),'commit','-m','Document round-two refusal audit and joint-noise sensitivity'],check=True)
commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
subprocess.run(['git','-C',str(repo),'push','origin','HEAD:main'],check=True)
line=datetime.datetime.now(datetime.timezone.utc).isoformat()+' ROUND2 PUBLISHED commit='+commit+'; allowlisted documents/scripts/hash-manifest only; no raw attacks, generated outputs or blind-text package published.\n'
with (b/'docs/PREREG_LOG.txt').open('a')as f:f.write(line)
dest=repo/'docs/PREREG_LOG.txt';tmp=dest.with_suffix('.tmp');tmp.write_bytes((b/'docs/PREREG_LOG.txt').read_bytes());tmp.replace(dest)
subprocess.run(['git','-C',str(repo),'add','docs/PREREG_LOG.txt'],check=True)
subprocess.run(['git','-C',str(repo),'commit','-m','Record published round-two content commit'],check=True)
record=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
subprocess.run(['git','-C',str(repo),'push','origin','HEAD:main'],check=True)
result={'content_commit':commit,'log_record_commit':record,'remote_head':subprocess.check_output(['git','-C',str(repo),'ls-remote','origin','refs/heads/main'],text=True).strip(),'rubric_sha256':hashlib.sha256((o/'rubric.md').read_bytes()).hexdigest(),'per_item_sha256':hashlib.sha256((o/'qwen_per_item.csv').read_bytes()).hexdigest(),'docs247_sha256':hashlib.sha256((b/'docs/247_RESULTS_51_SKELETON.md').read_bytes()).hexdigest()}
(o/'publication.json').write_text(json.dumps(result,indent=2));print('PUBLICATION',json.dumps(result))
