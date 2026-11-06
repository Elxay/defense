"""Validate report provenance, sample alignment, and the handoff corrections."""
from pathlib import Path
import datetime, hashlib, json
ROOT=Path('/data/HZX/Def');OUT=ROOT/'results/audit/handoff_20261106'
def read(p):return json.loads((ROOT/p).read_text())
report=(ROOT/'docs/247_RESULTS_51_SKELETON.md').read_text();count=0
for line in report.splitlines():
    if not line.startswith('| '):continue
    cells=[x.strip() for x in line.split('|')[1:-1]]
    if len(cells)!=3 or not cells[1].startswith(('results/','configs/','docs/')):continue
    files=cells[1].split('<br>');hashes=cells[2].split('<br>');assert len(files)==len(hashes)
    for f,h in zip(files,hashes):assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,(f,h)
    count+=1
d=read('results/audit/handoff_20261106/frontier_reanalysis.json')
for key in ['verified','previous_report','mean_p']:assert d['stats'][key]['t95'][0]<0<d['stats'][key]['t95'][1]
assert d['stats']['mean_p']['included_seeds']==[3,4,5,7]
for r in d['rows']:assert abs(r['d_previous_report']-r['d_verified']-100/388)<1e-9
review=read('results/audit/handoff_20261106/qwen_assistant_review.json')
assert len(review['items'])==122 and len(review['v2_positive_supplement'])==15
for r in review['items']+review['v2_positive_supplement']:
    assert hashlib.sha256(r['text'].encode()).hexdigest()==r['text_sha256']
    assert r['human_label'] is None
assert hashlib.sha256((OUT/'qwen_screen_package.json').read_bytes()).hexdigest()==review['package_sha256']
stat=read('results/audit/handoff_20261106/doc246_first_generation_stat.json')
assert all(r['mtime_ns']<stat['first_output_mtime_ns'] for r in stat['prereg_files'])
for r in stat['prereg_files']:assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256']
judge=read('results/hfjudge/JUDGE_HF_wjb_rand0')
assert judge['n']==300 and len(judge['items'])==300 and judge['invalid']==0 and judge['verified']
assert max(x['abs_delta'] for x in judge['gate'])==0
assert hashlib.sha256((ROOT/'results/audit/WJB_rand0.json').read_bytes()).hexdigest()==judge['source_sha256']
wjb=read('results/audit/handoff_20261106/wjb_refusal_decomposition.json')
assert len(wjb['rows'])==3
assert [c['n'] for c in wjb['learned_vs_rand_comparisons']]==[300,299,298]
assert len(wjb['down_flip_ids'])-len(wjb['up_flip_ids'])==118-77
for p in (ROOT/'tools/handoff_20261106').glob('*.py'):compile(p.read_text(),str(p),'exec')
manifest=read('results/audit/handoff_20261106/report_manifest.json')
assert hashlib.sha256((ROOT/manifest['report_file']).read_bytes()).hexdigest()==manifest['report_sha256']
res={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_hashed_table_rows':count,
 'source_hashes_match':True,'review_full_text_hashes_match':True,'human_labels_not_fabricated':True,
 'd_baseline_offset_reproduced':True,'prefile_timing_pass':True,'python_compile_pass':True,
 'wjb_all300_zero_invalid':True,'wjb_gate20_exact':True,'wjb_three_analysis_sets':[300,299,298],
 'report_sha256':manifest['report_sha256']}
(OUT/'validation.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res))
