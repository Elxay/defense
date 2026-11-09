"""Append clock and table reconciliation without editing the immutable read."""
from pathlib import Path
import csv,datetime,hashlib,json
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';O=B/'read_order10/reconciliation';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):assert not p.exists(),p.name;p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();steps={i:load(B/'read_order10/ordered_results'/f'{i:02d}.json')for i in range(1,9)}
 names=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B'];coverage={}
 for judge in ['HB','WG']:
  paths=[p for n in names for p in((B/'canonical254/scores'/n)if judge=='HB'else(B/'wildguard_pair254'/(n+'_scores'))).glob('*.json')];assert len(paths)==6500;last=max(paths,key=lambda p:p.stat().st_mtime)
  coverage[judge]={'n_score_files':6500,'latest_score_relative_path':str(last.relative_to(B)),'latest_score_file_mtime_utc':datetime.datetime.fromtimestamp(last.stat().st_mtime,datetime.timezone.utc).isoformat()}
 markers={}
 for label,p in [('HB_classifier',B/'canonical254/classifier_complete_innet.json'),('MinHash',B/'canonical254/hash_complete_innet.json'),('WildGuard_all13',B/'wildguard_pair254/queue_live.json')]:
  x=load(p);markers[label]={'utc':x['utc'],'sha256':sha(p),'source':str(p.relative_to(R))}
 assert load(B/'wildguard_pair254/queue_live.json')['phase']=='all_conditions_complete_no_effect_read'
 chronology={'recorded_utc':now,'read_plan_steps':8,'step_count_source':'docs/254_ADDENDUM10_FINAL_READ_ORDER_AND_CACHE_ASSERTIONS.md','user_corrected_prior_nine_step_count':True,'all_eight_steps_complete':True,'window_markers':markers,'score_file_coverage_metadata_only':coverage,'step1_status_receipt_utc':steps[1]['utc'],'step2_alpha0_receipt_utc':steps[2]['utc'],'first_alpha_nonzero_numeric_access_time_bound':{'after_step3_receipt_utc':steps[3]['utc'],'no_later_than_step4_receipt_utc':steps[4]['utc']},'entrypoint_start_not_separately_timestamped':True,'pre_read_statement':'Within this assistant session and the registered audited project paths, no formal PAIR-500 alpha!=0 outcome labels or effects were selected for display or aggregation before step4. Scoring workers wrote signed row caches; admission checked file coverage and signatures only. This statement does not certify unobserved third-party shared-account sessions. Parsing a cache to select its signature is distinguished from inspecting its outcome fields.','no_global_nobody_ever_read_claim':True,'read_receipt_sha256':{str(i):sha(B/'read_order10/ordered_results'/f'{i:02d}.json')for i in range(1,9)},'past_receipts_not_modified':True}
 save(O/'timing_and_read_scope.json',chronology)
 data=steps[4]['data']['primary'];rows=[]
 for panel in ['standard','contextual','jbb','all_retained','HarmBench']:
  for judge in ['HB','WildGuard']:
   x=data[judge][panel];est=x['estimate'];bounds=x['retained_bounds']
   rows.append({'panel':panel,'judge':judge,'n_retained':x['n_retained'],'n_complete':x['n_complete'],'complete_groups':est['scored_groups'],'row_pp':est['row_mean_pp'],'row_CI_low':est['row_cluster_ci95_pp'][0],'row_CI_high':est['row_cluster_ci95_pp'][1],'behavior_pp':est['behavior_mean_pp'],'behavior_CI_low':est['behavior_cluster_ci95_pp'][0],'behavior_CI_high':est['behavior_cluster_ci95_pp'][1],'full_retained_row_bound_low':bounds['row_pp'][0],'full_retained_row_bound_high':bounds['row_pp'][1],'source_sha256':sha(B/'read_order10/ordered_results/04.json')})
 table=O/'functional_layers_both_estimands.csv';assert not table.exists()
 with table.open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 manuscript=R/'paper/tables/pair500_primary.tex';copy=O/'manuscript_table_verbatim.tex';assert not copy.exists();copy.write_bytes(manuscript.read_bytes());assert sha(copy)==sha(manuscript)
 by={(r['panel'],r['judge']):r for r in rows};lines=[]
 for panel,name in [('standard','standard'),('contextual','contextual'),('jbb','JBB'),('all_retained','All harmfulness rows'),('HarmBench','HarmBench harm strata')]:
  a=by[panel,'HB'];b=by[panel,'WildGuard'];lines.append(f"|{name}|{a['n_retained']} / {b['n_complete']}|{a['row_pp']:.6f}|{b['row_pp']:.6f}|{a['behavior_pp']:.6f}|{b['behavior_pp']:.6f}|")
 doc=R/'docs/290_PAIR_READ_TIMING_AND_NUMERIC_RECONCILIATION.md';assert not doc.exists()
 doc.write_text(f'''# PAIR read chronology and numeric reconciliation

RecordedUTC {now}. Per the user's correction, addendum10 enumerates8 steps, not9; all8 were completed. The historical '9' count was an enumeration mistake, not a missing computation. Immutable read receipts remain unchanged.

## End of scoring and start of reading

HB classifier completeUTC {markers['HB_classifier']['utc']}; MinHash completeUTC {markers['MinHash']['utc']}; WG all13 completeUTC {markers['WildGuard_all13']['utc']}. WG's last score-file mtimeUTC {coverage['WG']['latest_score_file_mtime_utc']}; the completion marker follows it. All13 routes contain6500 row files each before admission.

The step1 status receipt was savedUTC {steps[1]['utc']}, after both routes were complete. That is a receipt time, not a separately recorded invocation-entry timestamp. Step2 alpha0 receiptUTC {steps[2]['utc']}. The first alpha!=0 numerical access was in step4, after step3 receiptUTC {steps[3]['utc']} and no later than step4 receiptUTC {steps[4]['utc']}. Do not invent a more precise start time.

Read-scope declaration: within this assistant session and registered audited project code paths, no formal PAIR500 alpha!=0 outcome labels or effects were selected for display or aggregation before step4. Model workers wrote signed per-row caches; coverage/signature audits selected metadata only. This is not an independently proven claim that no unobserved shared-account user ever opened a file. It also does not describe earlier results from other datasets. A cached JSON parsed to select its signature is not claimed never to have contained label bytes in process memory.

The earlier report gave effect values without their already-existing receipt hashes. The source for those values remains step4SHA `{sha(B/'read_order10/ordered_results/04.json')}`; it was not regenerated after the user's request. Subsequent report export and manuscript edits are after that read, not extra prior plan freezes. The entire generation-to-read interval was not a continuous judge window.

## Fixed step4 values, pp (learned minus random)

|Layer|Retained rows / WG complete rows|HB row|WG row|HB behavior equal|WG behavior equal|
|---|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

WG full400 retained-row identification bound is[-24.725,-24.350]pp, whereas its397-row complete-case point is-24.219144pp. These use different denominators and are not interchangeable. The bounds are not a95% CI. The corresponding retained behavior bound is[-24.122922,-23.729221]pp; the378-complete-group point is-23.586861pp. Rows remain in the dataset; no INVALID is silently assigned a safe label. The400 harmfulness rows contain381 source behavior groups; WG complete-case rows contain378. Standard, contextual and JBB remain separate, and100copyright rows are retained under MinHash without entering these harmfulness means.

The current manuscript table is copied verbatim below. No numeric cell or its Python two-decimal formatting was changed during this reconciliation. It is a complete-case table with conditional group-cluster confidence intervals, not a table of full-denominator identified point values. CSV includes both estimands and both sets of CIs. Caption rows300/400 refer to retained applicable rows; WG complete-case denominators are297/397 respectively (standard197, contextual100,JBB100).

```latex
{manuscript.read_text()}```

CSV SHA256 `{sha(table)}`. Verbatim tableSHA256 `{sha(copy)}`. Chronology scopeJSON SHA256 `{sha(O/'timing_and_read_scope.json')}`. The abstract written in the previous pass is an unverified draft; it is not treated as user-approved or finalized. No abstract refinement or new results wording is made during this reconciliation.
''')
 for n in ['PREREG_LOG.txt','OPS_LOG.txt']:
  with(R/'docs'/n).open('a')as f:f.write(f'{now} PAIR254_RECONCILIATION addendum10_steps=8 all_complete; user_corrected_prior_count; report_SHA={sha(doc)} chronology_SHA={sha(O/"timing_and_read_scope.json")} original_step4_SHA={sha(B/"read_order10/ordered_results/04.json")} original_receipts_unchanged; assistant_scope_no_pre_step4_alpha_nonzero_effect_read; no_unobserved_session_claim; prior_abstract_unverified_draft.\n')
 print(json.dumps({'utc':now,'doc_sha256':sha(doc),'timing_sha256':sha(O/'timing_and_read_scope.json'),'numeric_csv_sha256':sha(table),'verbatim_table_sha256':sha(copy)}))
if __name__=='__main__':main()
