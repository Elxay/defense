"""Frozen external-human style stratification on stored processed replies."""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
sys.path.insert(0,str(R/'tools/handoff_20261106'))
from unified300_human_agreement import stats
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=U/'human_style_results.json';assert not p.exists()
 plan=load(U/'human_style_diagnostic_plan.json');exe=load(U/'human_style_execution.json');assert sha(__file__)==exe['worker_sha256']and sha(U/'human_style_diagnostic_plan.json')==exe['plan_sha256']
 assert load(U/'active_protocol.json')['new_test_generation_allowed']is False
 gold=load(U/'human_gold.private.json');y=np.array([r['human_label']for r in gold]);q=np.array([r['question_id']for r in gold]);styles=np.array([r['prompt_style']for r in gold]);pred={k:[]for k in ['SORRY','HB','WG_nonrefusal','WG_harmful']}
 for r in gold:
  k=r['id'];pred['SORRY'].append(load(U/'SORRY_scores'/(k+'.json'))['label']);pred['HB'].append(load(U/'HB_scores'/(k+'.json'))['label']);labels=load(U/'WG_scores'/(k+'.json'))['labels'];ref={'yes':1,'no':0}.get(labels['Response refusal']);pred['WG_nonrefusal'].append(None if ref is None else 1-ref);pred['WG_harmful'].append({'yes':1,'no':0}.get(labels['Harmful response']))
 groups={'persuasion':['logical_appeal','authority_endorsement','misrepresentation','evidence-based_persuasion','expert_endorsement'],
         'encoding':['ascii','caesar','morse','atbash'],'languages':['translate-ml','translate-ta','translate-mr','translate-zh-cn','translate-fr'],
         'writing':['question','slang','uncommon_dialects','technical_terms','role_play','misspellings']}
 names=['base']+sum(groups.values(),[]);rng=np.random.default_rng(plan['bootstrap_seed']);result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan_sha256':sha(U/'human_style_diagnostic_plan.json'),'N':4400,'interface':'English base instruction plus stored supplied reply; no repeat decoding/translation','point_kappa_line':plan['kappa_eligibility'],'by_style':{},'pools':{},'raw_or_local_translation_validated':False,'automatic_scope_relaxation':False}
 def summarize(ix):
  if not len(ix):return {'N':0,'instruction_clusters':0,'human_class_counts':[0,0],'judges':{k:{'accuracy_all_lower':None,'kappa_valid':None,'eligible_processed_reference':False}for k in pred}}
  qi=q[ix];keys=sorted(set(qi));draw=rng.integers(0,len(keys),(plan['replicates'],len(keys)));out={'N':len(ix),'instruction_clusters':len(keys),'human_class_counts':[int((y[ix]==v).sum())for v in [0,1]],'judges':{}}
  for judge,values in pred.items():
   s=stats(y[ix],[values[i]for i in ix]);counts=[]
   for key in keys:
    rows=ix[qi==key];v=stats(y[rows],[values[i]for i in rows]);m=v['confusion_human0_1_by_model0_1'];counts.append([m[0][0],m[0][1],m[1][0],m[1][1],len(rows)])
   samples=np.array(counts)[draw].sum(axis=1);tn,fp,fn,tp,total=samples.T;valid=tn+fp+fn+tp
   with np.errstate(invalid='ignore',divide='ignore'):
    pe=((tn+fp)*(tn+fn)+(fn+tp)*(fp+tp))/valid**2;k=((tn+tp)/valid-pe)/(1-pe);acc=(tn+tp)/total
   k=k[np.isfinite(k)];s['accuracy_CI95']=np.quantile(acc,[.025,.975]).tolist();s['kappa_CI95']=np.quantile(k,[.025,.975]).tolist()if len(k)else None
   s['eligible_processed_reference']=s['kappa_valid']is not None and s['kappa_valid']>=plan['kappa_eligibility']and all(out['human_class_counts']);out['judges'][judge]=s
  return out
 for name in names:result['by_style'][name]=summarize(np.where(styles==name)[0])
 for group,items in groups.items():result['pools'][group]=summarize(np.where(np.isin(styles,items))[0])
 assert sum(v['N']for v in result['by_style'].values())==4400
 p.write_text(json.dumps(result,indent=2)+'\n')
 table=U/'human_style_results.md';lines=['# External-human style agreement','',f"Read UTC {result['utc']}. Cells: accuracy% / Cohen kappa; INVALID count-as-error for accuracy, valid pairs for kappa. Stored processed-reply English interface only; no raw-language/local-translator admission.",'','| Style | n | human0/1 | SORRY | HB | WG nonrefusal | WG harmful |','|---|---:|---|---|---|---|---|']
 for name in ['base']+groups['persuasion']+groups['encoding']+groups['languages']:
  x=result['by_style'][name];a=[]
  for j in pred:
   v=x['judges'][j];k=v['kappa_valid'];a.append(f"{100*v['accuracy_all_lower']:.2f}/{k:.3f}"if k is not None else'undefined')
  lines.append('| '+name+' | '+str(x['N'])+' | '+str(x['human_class_counts'])+' | '+' | '.join(a)+' |')
 lines +=['','Missing human styles: question and misspellings (N0). Other writing-style test cases485 are reported in JSON; not newly added to main test scope.','', 'Passing point kappa0.60 is only processed-reference eligibility. Small subgroup CI and the unvalidated new preprocessing path remain; no style-based judge dropping or automatic expansion.','', 'Result SHA '+sha(p)]
 table.write_text('\n'.join(lines)+'\n');print('\n'.join(lines));print('JSON_SHA',sha(p))
if __name__=='__main__':main()
