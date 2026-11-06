from pathlib import Path
import json,csv,hashlib,ast,datetime
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round5'
def load(n):return json.loads((o/n).read_text())
for p in(b/'tools/handoff_20261106').glob('round5*.py'):ast.parse(p.read_text())
w=load('wjb_flip_review85.json');pack=load('wjb_review_package.json');lookup={(x['condition'],x['id']):x for x in pack['items']};assert len(w['items'])==85
for r in w['items']:
 x=lookup[(r['condition'],r['id'])];assert r['read_char_ranges']==[[0,len(x['text'])]]and r['read_full_stored_text']
 assert hashlib.sha256(x['text'].encode()).hexdigest()==r['text_sha256'];assert r['human_category']is None
assert sum(r['condition']=='old_s0'for r in w['items'])==58
assert sum(r['task_refusal_explicit']and not r['rule_union']for r in w['items'])==3
L=load('llama_b_pair_summary.json');tail=load('llama_tail60_review.json');assert len(tail['items'])==60 and L['review_operation_range']==[46,49]and L['completed_before_deadline']
assert datetime.datetime.fromisoformat(L['completed_utc'])<datetime.datetime.fromisoformat('2026-11-06T22:30:00+09:00')
for r in tail['items']:assert r['read_char_ranges']==[[0,len(r['text'])]]
rows=list(csv.DictReader((o/'llama_b_paired400.csv').open()));assert len(rows)==400 and sum(r['eligible_fixed388']=='True'for r in rows)==388
h=load('handoff12_summary.json');assert(h['known_preview_changes'],h['unknown_preview_labels'],h['rule_selected_and_model_refusal'])==(3,9,6)
c=load('cosine_and_exclusions.json');r=c['sensitivity']['exclude_preread_reference_top5']['old_s0'];assert(r['n'],r['adversarial_new'],r['vanilla_new'])==(287,21,2);assert abs(r['dd_pp']-19/287*100)<1e-10
assert len(c['excluded8'])==8 and sum(x['alpha0_rule_flags']['vanilla']for x in c['excluded8'])==4 and sum(x['alpha0_rule_flags']['adversarial']for x in c['excluded8'])==4
assert c['audit_max_reference']<.85 and max(x['cosine']for x in c['withinpair_top5'])>.85
v=load('vanilla_two_review.json');assert all(not r['exclude_primary']and r['treatment_review']=='explicit_refusal'for r in v['items'])
g=load('qwen_guard_A_replace_check.json');assert(g['baseline_unfiltered_harmful'],g['A_replace_unfiltered_harmful'],g['baseline_remaining'],g['A_replace_remaining'])==(40,26,9,14)
assert g['guard_only_receives_generated_text']and g['paired_discordant']['baseline_only']==3 and g['paired_discordant']['A_replace_only']==8
f=next(x for x in ast.parse((b/'tools/handoff_20261106/guard_qwen_output.py').read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='score');assert[a.arg for a in f.args.args]==['response']
a=(o/'wjb_treat_node01.py').read_text().splitlines();d=(o/'wjb_treat_innet.py').read_text().splitlines();assert len(a)==len(d)and[i for i,(x,y)in enumerate(zip(a,d))if x!=y]==[6,7]
rec=load('val70_source_reconciliation.json');assert[(x['harmful_gt_half'],x['invalid'])for x in rec['baselines']]==[(63,0),(62,1)]
assert"CUDA_VISIBLE_DEVICES')=='2,3'"in(b/'tools/handoff_20261106/round5_judge_seeds.py').read_text()
assert 'wait_gpu cuda:2' in(b/'tools/handoff_20261106/round5_future_queue.py').read_text()and'wait_gpu cuda:3'in(b/'tools/handoff_20261106/round5_future_queue.py').read_text()
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'checks':['85 full-output read ranges and text hashes','60 tail reads and predeadline paired400','historical9 unknown preserved','pre-read top5 correction and8 exclusions','vanilla2 frozen primary policy','Guard single-output input and40->9/26->14','actual executed diff only2 path lines','HF63 vs vLLM62+1INVALID lineage','future judge GPU2/3 isolation and original wait_gpu'],'not_validated':'No independent human accuracy or mechanism validation; no future s5-s7 effects inspected.'}
(o/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
