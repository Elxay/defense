"""Export completed immutable PAIR read receipts; never reopen inference text."""
from pathlib import Path
import csv,datetime,hashlib,json

R=Path('/data/HZX/Def');B=R/'results/audit/pair500';D=B/'read_order10/ordered_results'
O=B/'read_order10/published_tables';P=R/'paper'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def csvout(name,rows):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 return p
def fmt(x):return '--'if x is None else f'{x:.2f}'
def ci(x):return '['+', '.join(fmt(v)for v in x)+']'
def main():
 steps={i:load(D/f'{i:02d}.json')for i in range(1,9)}
 for i,x in steps.items():
  assert x['step']==i
  if i>1:assert x['previous_receipt_sha256']==sha(D/f'{i-1:02d}.json')
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();d=steps[4]['data'];tests=steps[5]['data'];attr=steps[6]['data'];exposure=steps[7]['data']
 rows=[]
 for judge in ['HB','WildGuard','MinHash']:
  for panel,x in d['primary'][judge].items():
   if not x['n_retained']:continue
   est=x['estimate'];bounds=x['retained_bounds'];t=tests[judge][panel]
   rows.append(dict(judge=judge,panel=panel,metric='copyright_match'if judge=='MinHash'else'response_harmfulness',n_applicable=x['n_retained'],n_groups=x['n_retained_groups'],n_complete=x['n_complete'],row_pp=est['row_mean_pp'],row_ci_low=est['row_cluster_ci95_pp'][0],row_ci_high=est['row_cluster_ci95_pp'][1],behavior_pp=est['behavior_mean_pp'],behavior_ci_low=est['behavior_cluster_ci95_pp'][0],behavior_ci_high=est['behavior_cluster_ci95_pp'][1],retained_row_bound_low=bounds['row_pp'][0],retained_row_bound_high=bounds['row_pp'][1],permutation_lower=t['row_weighted']['directional_lower_p'],permutation_two_sided_absolute=t['row_weighted']['two_sided_absolute_mean_statistic_p'],permutation_doubled_tail=t['row_weighted']['doubled_smaller_tail_p'],source_sha256=sha(D/'04.json'),test_source_sha256=sha(D/'05.json')))
 primary=csvout('primary.csv',rows)
 unitrows=[]
 for judge,panels in d['unit_rates'].items():
  for panel,cell in panels.items():
   if not cell['n_applicable']:continue
   for name,c in cell['conditions'].items():
    unitrows.append(dict(judge=judge,panel=panel,condition=name,n_applicable=c['n_applicable'],yes=c['yes'],invalid=c['invalid'],valid_only_pct=c['valid_only_pct'],retained_low_pct=c['retained_bounds_pct'][0],retained_high_pct=c['retained_bounds_pct'][1],source_sha256=sha(D/'04.json')))
 csvout('unit_rates.csv',unitrows)
 invalid=[]
 for n in [2,4]:
  field=steps[n]['data']['field_diagnostics']
  for name,fs in field['INVALID_ids_by_condition_field'].items():
   for f,ids in fs.items():
    if f=='WG_harmfulness_not_applicable':continue
    for ident in ids:invalid.append(dict(condition=name,field=f,id=ident,source_sha256=sha(D/f'{n:02d}.json')))
 if invalid:csvout('invalid_fields.csv',invalid)
 attrrows=[]
 for name,judges in attr['downflip_attribution'].items():
  for judge,x in judges.items():
   attrrows.append(dict(condition=name,judge=judge,down_flips=x['down_flips'],v2=x['v2_refusal'],v2_union_v3=x['v2_union_v3_refusal'],WildGuard=x['WG_refusal'],WG_refusal_invalid=len(x['WG_refusal_invalid_ids']),source_sha256=sha(D/'06.json')))
 csvout('downflip_attribution.csv',attrrows)
 erows=[]
 for name,part in exposure.items():
  for judge,panels in part['results'].items():
   x=panels['all_retained']
   if not x['n_retained']:continue
   est=x['estimate'];erows.append(dict(stratum=name,n_rows=part['n_rows'],judge=judge,n_applicable=x['n_retained'],n_complete=x['n_complete'],row_pp=est['row_mean_pp'],row_ci_low=est['row_cluster_ci95_pp'][0],row_ci_high=est['row_cluster_ci95_pp'][1],behavior_pp=est['behavior_mean_pp'],source_sha256=sha(D/'07.json')))
 csvout('exposure.csv',erows)
 # The TeX table reads the exported CSV, not a second set of handwritten values.
 cells={(x['judge'],x['panel']):x for x in csv.DictReader(primary.open())}
 tex=['% Generated from primary.csv; complete-case estimates and group-cluster intervals.',r'\begin{table*}[t]',r'\centering\small',r'\begin{tabular}{lrr}',r'\toprule',r'Layer & HarmBench judge & WildGuard \\',r'\midrule']
 for panel,label in [('all_retained','All harmfulness rows (400)'),('HarmBench','HarmBench harm strata (300)'),('standard','Standard (200)'),('contextual','Contextual (100)'),('jbb','JBB-Behaviors (100)')]:
  values=[]
  for judge in ['HB','WildGuard']:
   z=cells[judge,panel];values.append(f"{float(z['row_pp']):.2f} [{float(z['row_ci_low']):.2f}, {float(z['row_ci_high']):.2f}]")
  tex.append(label+' & '+' & '.join(values)+r' \\')
 tex +=[r'\bottomrule',r'\end{tabular}',r'\caption{PAIR-style fixed prompts: learned minus random harmfulness rate (pp), with 95\% behavior-cluster intervals conditional on the nine vectors. Rows remain in the dataset. WildGuard estimates for the standard and pooled rows use the 197 and 397 complete nine-unit rows, respectively; full-denominator bounds are reported in the text. Copyright (100 rows) is evaluated separately by MinHash.}',r'\label{tab:pair500-primary}',r'\end{table*}']
 # A compact table avoids repeating a second label for the full-row bounds.
 (P/'tables/pair500_primary.tex').write_text('\n'.join(tex)+'\n')
 hb=d['primary']['HB']['all_retained'];wg=d['primary']['WildGuard']['all_retained'];mh=d['primary']['MinHash']['copyright']
 body=r'''\paragraph{A fixed, unfiltered PAIR-style search.}
The completed campaign retains all500 HarmBench text and JBB-Behaviors rows (479 behavior groups), including unsuccessful searches and historically used rows. It is a fixed rule-scored PAIR-style attack against the unmodified Llama model; evaluation under steering is transfer rather than an adaptive attack. The400 rows applicable to harmfulness judging and the100 copyright rows have different outcomes and are not averaged into one ASR.
\input{tables/pair500_primary}
'''
 body+=f"On the400 harmfulness rows, learned minus random is {fmt(hb['estimate']['row_mean_pp'])} pp under the HarmBench judge and {fmt(wg['estimate']['row_mean_pp'])} pp under WildGuard. The latter complete-case estimate uses397 rows, rather than assigning an INVALID output a safe label. Allowing each missing label to be zero or one on the entire400-row denominator gives {ci(wg['retained_bounds']['row_pp'])} pp; this is an identification bound, not a confidence interval. Equal weighting after averaging within behavior groups gives {fmt(hb['estimate']['behavior_mean_pp'])} and {fmt(wg['estimate']['behavior_mean_pp'])} pp on the respective complete-row sets. The standard, contextual and JBB strata have the same negative sign under both judges.\n\n"
 body+=r'''All five learned unit rates are below all four random rates on the common scored rows. The126-label-allocation mean test gives directional$p=1/126$; a doubled smaller-tail convention gives$p=2/126$. The absolute-mean two-sided statistic also gives$1/126$, because the5-versus4 allocation distribution is asymmetric. These are exploratory unit-label tests under exchangeability, not evidence that seeds and directions were independently sampled from vector populations. The confidence intervals above condition on the observed nine vectors.

The HarmBench standard/contextual judge uses the actual source behavior and context here, avoiding the behavior-mapping step needed for the official WildJailbreak evaluation. Both judges remain model labels without human calibration; WildGuard also shares the WildJailbreak source used in other evaluations. For copyright, the baseline MinHash match rate is10\%, below the frozen25\% dynamic-range threshold. The learned-minus-random match difference is'''
 body+=f" {fmt(mh['estimate']['row_mean_pp'])} pp {ci(mh['estimate']['row_cluster_ci95_pp'])}; it does not support an effectiveness claim.\n\n"
 body+=r'''Search diagnostics are read after the primary comparisons:70/500 selected prompts are in the zero-score tier and2/500 use fallback. An exact selected-token trace exists for488 nonpilot rows, of which406 reach the512-token search cap. The first10 pilot rows lack that exact trace. Copyright has fewer than40 usable candidates on96/100 rows, compared with5/400 elsewhere. Neither a zero-score tier nor a long selected reply proves all candidates were refusals or that the selected attack succeeded. Search configuration was not changed after these readings.
'''
 (P/'generated/pair500_completed_read.tex').write_text(body)
 # Minimal experiment chronology and hashes, with no prompt or response content.
 doc=R/'docs/289_PAIR500_COMPLETED_ORDERED_READ.md'
 receiptlines='\n'.join(f"|{i}|{steps[i]['utc']}|`{sha(D/f'{i:02d}.json')}`|"for i in range(1,9))
 tablelines='\n'.join(f"|{x['judge']}|{x['panel']}|{x['n_applicable']}|{x['n_complete']}|{x['row_pp']:.3f}|[{x['row_ci_low']:.3f}, {x['row_ci_high']:.3f}]|[{x['retained_row_bound_low']:.3f}, {x['retained_row_bound_high']:.3f}]|"for x in rows if x['panel']in ['all_retained','HarmBench','standard','contextual','jbb','copyright'])
 doc.write_text(f'''# PAIR-500 completed ordered read

ExportUTC {now}. All500 rows x13 conditions x2 scoring routes admitted before step1;6500 prompt/generation/cache signature chains checked. Search source completionUTC2026-11-09T11:56:07.362927Z; last generated target fileUTC11:59:13.755903Z; coverage first observed completeUTC11:59:27.770861Z. Earlier12:17:48 readiness covered the nine units plus alpha0, not a first assertion that all13 were complete. Strict all13 admission was observed before step1 at13:31UTC.

No rows removed:500 rows,479 groups. HarmBench400 retained as300 classifier-applicable rows plus100 MinHash copyright rows; JBB100 classifier rows. Never report a single mixed harmfulness/copyright ASR. Main contrast is five learned means minus four random means; s0 and A/B are not permutation units.

## Ordered immutable receipts

|Step|UTC|SHA256|
|---|---|---|
{receiptlines}

1 status and chains;2 alpha0;3 layer gates;4 main differences and field-specific INVALIDs;5 exact allocation tests;6 refusal attribution;7 exposure layers;8 search diagnostics. Each preceding SHA is included in the next file. No subsequent queue or condition order was changed because of these values.

## Main table (pp)

|Judge|Panel|Applicable rows|Nine-unit complete rows|Learned-random|95% group-cluster CI|All-retained identification bound|
|---|---|---:|---:|---:|---|---|
{tablelines}

Intervals condition on these nine vectors. Complete-case estimates and all-retained identification bounds are different estimands and must not be conflated; no INVALID is silently called safe. Group-weighted estimates first average within groups, then weight groups equally. Exact126-allocation directional p is1/126 for harmfulness panels; absolute-mean two-sided p is1/126 and doubled-tail p is2/126. Report the definition, not just 'two-sided'. Unit exchangeability is exploratory and population sampling is not established.

Both judges and the standard/contextual/JBB layers have negative primary signs. Copyright baseline10/100 MinHash matches is below25%, and its effect interval includes zero; keep the100 rows and report no dynamic range. It cannot support an abstract efficacy claim. Per-field INVALID IDs, over4096 input records, downflip IDs, v2/union/WG counts and kappas, and66/73/89 untouched layers are in the immutable receipts and exported CSVs.

Contextual input audit includes all1300 inputs, max1962 tokens,23 over1900,0 over2048. The original512-token response clipping is retained. No GPU chunk-fallback inference was needed. Separate read chronology from protocol specification: this is a post-read report, not an additional preregistration.

Only coded IDs, counts, statistics, hashes and analysis source are published. No raw attacks, replies, training targets or weights. No newly ported model has a trained-vector result yet. Qwen's native donor gate remains failed and its newly authorized Llama-target transfer remains blocked on fresh native-alpha0 refusal review.
''')
 generated=[primary,*[p for p in O.glob('*.csv')if p!=primary],P/'tables/pair500_primary.tex',P/'generated/pair500_completed_read.tex',doc]
 dump(O/'export_manifest.json',{'utc':now,'read_receipts':{f'{i:02d}':sha(D/f'{i:02d}.json')for i in range(1,9)},'files':{str(p.relative_to(R)):sha(p)for p in generated},'raw_inference_text_opened':False,'no_condition_or_queue_change_from_results':True})
 print(json.dumps({'utc':now,'report_sha256':sha(doc),'export_manifest_sha256':sha(O/'export_manifest.json'),'primary_csv_sha256':sha(primary)}))
if __name__=='__main__':main()
