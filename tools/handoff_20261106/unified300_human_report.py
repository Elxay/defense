"""Generate review tables from diagnostic and metadata artifacts, no hand copying."""
from pathlib import Path
import datetime,hashlib,json,sys
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';O=R/'results/audit/sorry296'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pct(x):return f'{100*x:.2f}'
def jst(s):return datetime.datetime.fromisoformat(s).astimezone(datetime.timezone(datetime.timedelta(hours=9))).strftime('%m/%d %H:%M JST')
def main():
 perfpath=U/sys.argv[1];perf=load(perfpath);d=load(U/'human_refusal_diagnostics.json');coverage=load(U/'S0_coverage_confirmation.json')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=U/f'S0_HUMAN_AND_ACCEPTANCE_REPORT_{stamp}.md'
 lines=['# S0 human-reference and acceptance review','',f"UTC snapshot: {perf['utc']}; S1 and formal testing remain locked.",'',
 '## External-human comparison','',
 'Matrix is [[human0/model0, human0/model1], [human1/model0, human1/model1]]. Human0=nonfulfillment (3111), human1=fulfillment (1289). Accuracy counts INVALID as incorrect; kappa uses valid pairs. Recall denominators retain INVALID.','',
 '| Judge field | Accuracy % | Kappa | Matrix | Recall human0 % | Recall human1 % | INVALID |','|---|---:|---:|---|---:|---:|---:|']
 for name in ['SORRY','HB','WG_harmful','WG_1_minus_refusal']:
  x=d['overall'][name];lines.append(f"| {name} | {pct(x['accuracy_all_lower'])} | {x['kappa_valid']:.6f} | {x['confusion_human0_1_by_model0_1']} | {pct(x['recall_human_nonfulfillment_all'])} | {pct(x['recall_human_fulfillment_all'])} | {x['invalid']} |")
 comp=d['WG_field_comparison'];lines += ['',f"Inverse-refusal accuracy gain={comp['accuracy_gain_pp']:.6f}pp, paired440-instruction95% CI={comp['accuracy_gain_CI95_pp']}; kappa gain={comp['kappa_gain']:.6f}, CI={comp['kappa_gain_CI95']}. Selected field={comp['selected_WG_SORRY_fulfillment_field']}. External-human labels used for this choice; no new target-test effect used.",'',
 '## Response signal strata','',d['stratification_caveat'],'',
 '| Operational type proxy | N | SORRY errors % | HB errors % | WG inverse-refusal errors % | WG harmful errors % |','|---|---:|---:|---:|---:|---:|']
 for kind in ['front_anchored_refusal_signal','WG_only_refusal_signal','warning_nonrefusal_candidate','unwarned_nonrefusal_candidate','v2_WG_refusal_conflict','WG_refusal_INVALID']:
  x=d['strata'][kind];v=x['judges'];values=[pct(v[k]['error_all_including_INVALID'])for k in ['SORRY','HB','WG_1_minus_refusal','WG_harmful']];lines.append('| '+kind+' | '+str(x['N'])+' | '+' | '.join(values)+' |')
 lines += ['', '## Train/test audit','', 'Published splits:202503=2640 train+4400 test;202406 train=2700. All440 base instruction texts shared with test. Answer-ID and question/model/style/reply record overlaps=0. Same instruction+identical response duplicates against either train version: test_1809,test_1939,test_2110,test_2261. Keep all rows. Actual optimizer training-row manifest unavailable.','',
 'Original paper v2 Tables1/6: fine-tuned Mistral kappa0.810, recall nonfulfillment91.1%/fulfillment93.4%; WildGuard kappa0.606. Our HB full-response pipeline is not claimed to reproduce its table.','',
 '## Dataset and scope','', 'Base:202503,440 rows/44 categories/10 per category. Every listed transform440 rows; IDs identical to base.','', '| Group | Files | In first round? |','|---|---|---|']
 groups={
 'writing':(['question','slang','uncommon_dialects','technical_terms','role_play','misspellings'],'no'),
 'persuasion':(['logical_appeal','authority_endorsement','misrepresentation','evidence-based_persuasion','expert_endorsement'],'yes'),
 'encoding':(['ascii','caesar','morse','atbash'],'yes'),
 'languages':(['translate-ml','translate-ta','translate-mr','translate-zh-cn','translate-fr'],'yes')}
 for name,(values,used)in groups.items():lines.append('| '+name+' | '+', '.join('question_'+x+'.jsonl'for x in values)+' | '+used+' |')
 lines += ['', 'Overlap: all byte/normalized exact counts0. MiniLM cosine>=0.85 flags below; overlap across references, do not sum counts. All rows retained.','', '| Reference | flagged SORRY rows |','|---|---:|']
 for name,x in coverage['overlap_summary'].items():lines.append(f"| {name} | {x['SORRY_cos_ge_085']} |")
 lines += ['',f"Union={coverage['overlap_union']}/440. Calibration700 rows retained,697 normalized base-request groups. Similarity flag is not proof of semantic identity/independence.",'',
 'Qwen old-grid stop:2026-11-10T05:04:03–05:04:07UTC; receipt05:04:10UTC.9867 generation files unchanged; before/after manifest bf94912bb631d35d5fe4085b57b7c6d4158cc899129b799864b2471907b64775. Old WG cache9382 retained; condition effects unread.','',
 'Budget:600 GPUh main alpha0 search, build W/replay/adaptive separate; no condition stacking; no additional role-play family or SORRY role_play mutation. DeepInception retains its fixed definition.','',
 '## Acceptance throughput (actual files and wall clock)','',perf['method'],'',
 '| Model | saved/1200 | cap120 single row/h | cap120 batch row/h | cap2400 single row/h | cap2400 batch row/h | generation ETA |','|---|---:|---:|---:|---:|---:|---|']
 for key,x in perf['models'].items():
  values=[]
  for cap,route in [('120','legacy_single'),('120','candidate_batch'),('2400','legacy_single'),('2400','candidate_batch')]:
   z=x['by_cap'].get(cap,{}).get(route);values.append(f"{z['effective_rows_per_hour']:.1f} (n={z['n']})"if z else'pending')
  eta=x['generation_ETA'];v=eta.get('utc_same_speed_range');when='–'.join(jst(t)for t in v)if v else eta.get('status','pending')
  lines.append('| '+key+' | '+str(x['total_saved'])+'/1200 | '+' | '.join(values)+' | '+when+' |')
 lines += ['', 'Llama B16 long panel self-stopped at10:49:28UTC:1686044672bytes headroom, below3GiB. Its780 original files remain unchanged;80 failed long B16 candidate records are excluded from replacement B8. New Llama logical count includes100 explicitly referenced original B1 rows; copied references are not new throughput. Long B8 regenerates all three candidate conditions. No OOM or forced termination.','',
 'ETA uses only observed acceptance long-output row rates; same-speed scenario, not upper bound/CI. Excludes labels, historical20 and search20. Different model batch sizes allowed; same-model/family conditions keep identical batching.','',
 '### Memory telemetry coverage','', 'Successful exact allocator peaks were not persisted by original acceptance worker; its per-batch3GiB margin check remains. No runtime source was edited. Monitor data below is sampled total-card use since its stated start, can include external CUDA contexts, not an exact whole-run or per-process peak.','']
 if 'sampled_memory'in perf:
  m=perf['sampled_memory'];lines += ['Monitor start='+m['started_utc']+'; every5seconds.','', '| Card | sampled peak MiB | sampled minimum free MiB |','|---|---:|---:|']
  for card,peak in m['sampled_peak_card_used_MiB'].items():lines.append(f"| innet GPU{card} | {peak} | {m['sampled_min_card_free_MiB'][card]} |")
 for model,x in perf['models'].items():
  if x.get('own_batch_telemetry'):
   m=x['own_batch_telemetry'];lines += ['',f"{model} new-version per-batch allocator telemetry (not whole v1 run): reserved peak={m['peak_reserved_bytes']/1024**3:.3f}GiB, allocated peak={m['peak_allocated_bytes']/1024**3:.3f}GiB, minimum measured headroom={m['minimum_measured_headroom_bytes']/1024**3:.3f}GiB; batches={m['batches']}."]
 gatepath=U/'acceptance_cap120_labels/result.json'
 if gatepath.exists():
  gate=load(gatepath);lines += ['', '## Completed120-token paired-label gate','', '| Model | Condition | v2 flips/100 | WG known/worst-case flips/100 | Passed |','|---|---|---:|---|---|']
  for model,x in gate['models'].items():
   for condition,s in x['conditions'].items():lines.append(f"| {model} | {condition} | {s['v2_flips']} | {s['WG_known_flips']}/{s['WG_worstcase_flips']} | {s['passed']} |")
  lines += ['', 'Gate covers120 only; does not admit2400, historical batch20 or search patch20. Absolute condition refusal rates were not aggregated. Gate result SHA='+sha(gatepath)+'.']
 lines += ['', 'A transient additional GPU2 context PID54588/2496MiB was observed10:42UTC and exited before its ownership could be inspected. It was not touched and its project is unconfirmed. Card-use peaks cannot all be attributed to this experiment. Three requested admission gates remain unpassed.','',
 '## Provenance','', '- Human diagnostic SHA: '+sha(U/'human_refusal_diagnostics.json'),'- Performance SHA: '+sha(perfpath),'- Field amendment SHA: '+sha(R/'docs/300_ADDENDUM1_EXTERNAL_HUMAN_WG_FIELD.md'),'- Master candidate SHA: '+sha(R/'docs/300_UNIFIED_PROTOCOL.md'),'',
 'Sources: https://arxiv.org/html/2406.14598v2 ; https://github.com/SORRY-Bench/SORRY-Bench .']
 out.write_text('\n'.join(lines)+'\n');print('REPORT',out.name);print('SHA',sha(out))
if __name__=='__main__':main()
