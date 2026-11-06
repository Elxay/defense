from pathlib import Path
import csv,json,sys,hashlib
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round4'
sys.path.insert(0,str(b/'src'));from judge.refusal import new_rule
rows=list(csv.DictReader((b/'results/audit/handoff_round3/baseline_two_paths.csv').open()))
base=json.loads((b/'results/audit/LEGALVALB_qwen_a0.json').read_text());eligible=[k for k,v in base.items()if not new_rule(v['text'])];assert len(eligible)==392
for row in rows:
 qwen='qwen'in row['analysis_file'].lower()
 row['batch_comparison_valid']='YES'if qwen else'NOT_ASSERTED_BY_THIS_CORRECTION'
 row['alternate_single_path_sensitivity_available']='NO'if qwen else'YES'
 row['comparison_note']='同模型批量8对批量8可比；仅缺单条路径反事实敏感性，不影响实际比较。'if qwen else'同模型双路径敏感性；实际生成路径匹配另见baseline_file。'
 if qwen:
  d=json.loads((b/row['analysis_file']).read_text());row['new_batch']=sum(new_rule(d[k]['text'])for k in eligible);row['batch_eligible_n']=len(eligible)
  row['new_single']='UNAVAILABLE';row['single_minus_batch']='UNAVAILABLE';row['abs_diff_gt1']='NOT_TESTABLE'
 else:row['batch_eligible_n']=388
fieldnames=list(rows[0])
with(o/'baseline_two_paths_corrected.csv').open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader();w.writerows(rows)
print('QWEN_VALID',[(x['analysis_file'],x['new_batch'])for x in rows if'qwen'in x['analysis_file'].lower()])
