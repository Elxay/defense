"""Post-read exports requested by user; immutable step artifacts stay unchanged."""
from pathlib import Path
import datetime,hashlib,itertools,json,sys,collections
import numpy as np
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';D=B/'read_order10/ordered_results';O=B/'requested_steps_35678';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'tools/handoff_20261106'))
import pair254_ordered_read10 as reader
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):assert not p.exists(),p.name;p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 steps={i:json.loads((D/f'{i:02d}.json').read_text())for i in range(1,9)};audit=json.loads((B/'row_audit.json').read_text());lookup={r['id']:r for r in audit['flags']};rows=[lookup[r['id']]for r in json.loads((B/'frozen_prompt_snapshot.json').read_text())['rows']]
 unseen=[r for r in rows if r['untouched']and r['layer']!='copyright'];assert len(unseen)==139
 omitted=[r for r in rows if not r['untouched']and not r['historical_group_used']];assert len(omitted)==99 and all('train_strat97'in r['group_flags']for r in omitted)
 marked=[r for r in rows if not r['untouched']];assert len(marked)==272
 pooled={'requested_after_existing_main_read':True,'definitions':{'unused139':'untouched standard53 + JBB13 + contextual73; no copyright','marked272':'not untouched; complements all228 untouched rows','old_historical173':'historical_group_used field; omits99 train_strat97 rows'},'unused139':{'n_rows':len(unseen),'n_groups':len(reader.groups(unseen)),'results':reader.primary(unseen)},'marked272':{'n_rows':len(marked),'n_groups':len(reader.groups(marked)),'results':reader.primary(marked)},'omitted99_ids':[r['id']for r in omitted],'does_not_change_main_contrast_or_rows':True}
 save(O/'unused139_and_complete_marked272.json',pooled)
 change={}
 for judge in ['HB','WildGuard','MinHash']:
  part=reader.applicable(rows,judge);base,_=reader.labels('alpha0',judge,part);change[judge]={}
  for name in reader.UNITS:
   val,_=reader.labels(name,judge,part);mat=np.array([base,val]);where=np.argwhere(~np.isfinite(mat));assert len(where)<12
   outcomes=[]
   for binary in itertools.product([0.,1.],repeat=len(where)):
    m=mat.copy()
    for (i,j),v in zip(where,binary):m[i,j]=v
    b=m[0].mean();a=m[1].mean();outcomes.append((100*b,100*a,100*(a-b),100*(b-a)/b if b else np.nan))
   arr=np.array(outcomes);change[judge][name]={'n_retained':len(part),'baseline_pct_bounds':[float(arr[:,0].min()),float(arr[:,0].max())],'condition_pct_bounds':[float(arr[:,1].min()),float(arr[:,1].max())],'delta_pp_bounds':[float(arr[:,2].min()),float(arr[:,2].max())],'relative_reduction_pct_bounds':[float(arr[:,3].min()),float(arr[:,3].max())],'relative_reduction_definition':'100*(baseline_rate-condition_rate)/baseline_rate; positive means decline','INVALID_cells_enumerated':len(where),'no_invalid_defaulted_safe':True}
 save(O/'all_units_vs_alpha0_retained_bounds.json',change)
 C=R/'results/audit/crossmodel287/qwen_refusal_admission';manifest=json.loads((C/'sample_manifest.json').read_text());ids=json.loads((C/'ids_only.json').read_text());mapping=json.loads((C/'mapping.private.json').read_text());print('MAPPING_SCHEMA',list(mapping[0].keys()))
 groupkey=next(k for k in mapping[0]if any(v.get(k)in ['legal388','val70']for v in mapping))
 byblind={r['blind_id']:r for r in mapping};q={'manifest_sha256':sha(C/'sample_manifest.json'),'original_combined_ID_file_sha256':sha(C/'ids_only.json'),'presentation_seed':manifest['presentation_seed'],'sets':{},'saved_batches':[]}
 for group,values in ids.items():
  p=O/f'qwen_{group}_ids_only.json';save(p,values);q['sets'][group]={'seed':manifest['populations'][group]['seed'],'pool':manifest['populations'][group]['v2_negative_pool'],'n':len(values),'export_ID_file_sha256':sha(p)}
 batches=list((C/'annotation_batches').glob('*.json'));saved={}
 for p in batches:
  x=json.loads(p.read_text());q['saved_batches'].append({'name':p.name,'sha256':sha(p),'utc':x['labels_saved_utc'],'n':len(x['items'])})
  for item in x['items']:assert item['blind_id']not in saved;saved[item['blind_id']]=item
 progress=json.loads((C/'GPT_review_progress.json').read_text());working={r['blind_id']:r for r in progress['rows']};aliases={'COMPLY':'COMPLIANCE','COMPLY_WARN':'COMPLIANCE_WITH_WARNING'}
 q['batch_counts_by_set']={group:dict(collections.Counter(aliases.get(r['category'],r['category'])for k,r in saved.items()if byblind[k][groupkey]==group))for group in ids}
 q['working_counts_by_set']={group:dict(collections.Counter(r['category']for k,r in working.items()if byblind[k][groupkey]==group))for group in ids}
 q.update(saved_n=len(saved),working_n=len(working),working_progress_sha256=sha(C/'GPT_review_progress.json'),working_utc=progress['utc'],conflicts=[{'blind_id':k,'saved_category':r['category'],'working_category':working[k]['category']}for k,r in saved.items()if k in working and aliases.get(r['category'],r['category'])!=working[k]['category']],working_only_ids=sorted(set(working)-set(saved)),final_admission_available=False,training_admitted=False,model_labels_without_human_calibration=True,shared_context_not_independent=True)
 save(O/'Qwen_recall_audit_status.json',q)
 save(O/'export_manifest.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_steps':{str(i):sha(D/f'{i:02d}.json')for i in [2,3,4,5,6,7,8]},'files':{p.name:sha(p)for p in O.glob('*.json')},'source_steps_not_modified':True,'new_poolings_and_missing_label_bounds_are_post_read_requested_exports':True,'raw_prompts_responses_not_exported':True})
 print('POOLED',json.dumps({k:{'n':pooled[k]['n_rows'],'groups':pooled[k]['n_groups'],'judges':{j:pooled[k]['results'][j]['all_retained']for j in ['HB','WildGuard']}}for k in ['unused139','marked272']}))
 print('RANDOM',json.dumps({j:{n:x for n,x in change[j].items()if n.startswith('rand')}for j in change}))
 print('QWEN',json.dumps(q))
if __name__=='__main__':main()
