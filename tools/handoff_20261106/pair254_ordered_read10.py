"""Explicit one-step-at-a-time PAIR read, gated by all 500 rows x 13 conditions x 2 judges."""
from pathlib import Path
import argparse,ast,collections,datetime,hashlib,itertools,json,re,subprocess,sys
import numpy as np
from pair254_all13_read_gate import status as readiness,verify_prompt_chain
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';D=B/'read_order10/ordered_results';NAMES=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B'];UNITS=[f'old_s{s}'for s in range(3,8)]+[f'rand{s}'for s in range(4)]
sys.path.insert(0,str(R/'src'));from judge.refusal import new_rule
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def numeric(x):return np.nan if x is None else float(x)
def wgvalue(x):return {'yes':1.,'no':0.}.get(x,np.nan)
def groups(rows):return sorted({r['group']for r in rows})
def scope(rows):
 out={'all_retained':rows,'HarmBench': [r for r in rows if r['dataset']=='HarmBench'],'JBB':[r for r in rows if r['dataset']=='JBB']}
 for key in ['standard','contextual','copyright','jbb']:out[key]=[r for r in rows if r['layer']==key]
 return out
def applicable(rows,judge):return [r for r in rows if (r['layer']=='copyright')==(judge=='MinHash')]
def labels(name,judge,rows):
 values=[];invalid=[]
 for row in rows:
  key=row['id']
  if judge=='WildGuard':value=wgvalue(load(B/'wildguard_pair254'/(name+'_scores')/(key+'.json'))['labels']['Harmful response'])
  else:value=numeric(load(B/'canonical254/scores'/name/(key+'.json'))['label'])
  values.append(value)
  if not np.isfinite(value):invalid.append(key)
 return np.array(values),invalid
def weighted(values,rows,equal=False):
 if len(values)==0:return None
 if not equal:return float(np.mean(values))
 data=collections.defaultdict(list)
 for x,r in zip(values,rows):data[r['group']].append(float(x))
 return float(np.mean([np.mean(x)for x in data.values()]))
def interval(values,rows):
 if len(values)==0:return {'row_mean_pp':None,'behavior_mean_pp':None,'row_cluster_ci95_pp':[None,None],'behavior_cluster_ci95_pp':[None,None],'scored_rows':0,'scored_groups':0}
 by=collections.defaultdict(list)
 for value,row in zip(values,rows):by[row['group']].append(float(value))
 keys=sorted(by);sums=np.array([sum(by[k])for k in keys]);ns=np.array([len(by[k])for k in keys]);means=sums/ns
 indices=np.random.default_rng(20261108).integers(len(keys),size=(10000,len(keys)));a=sums[indices].sum(1)/ns[indices].sum(1);b=means[indices].mean(1)
 return {'row_mean_pp':float(100*sums.sum()/ns.sum()),'behavior_mean_pp':float(100*means.mean()),'row_cluster_ci95_pp':(100*np.quantile(a,[.025,.975])).tolist(),'behavior_cluster_ci95_pp':(100*np.quantile(b,[.025,.975])).tolist(),'scored_rows':int(ns.sum()),'scored_groups':len(keys)}
def rate(values,rows):
 finite=np.isfinite(values);valid=[r for r,ok in zip(rows,finite)if ok];n=len(rows);yes=int(np.nansum(values));bad=int((~finite).sum())
 return {'n_applicable':n,'n_groups':len(groups(rows)),'yes':yes,'invalid':bad,'valid_only_pct':100*yes/int(finite.sum())if finite.any()else None,'retained_bounds_pct':[100*yes/n,100*(yes+bad)/n]if n else[None,None],'conditional_interval':interval(values[finite],valid)}
def effect(matrix,rows):
 n=len(rows)
 if n==0:return {'n_retained':0,'n_complete':0,'estimate':interval([],[]),'retained_bounds':None}
 complete=np.isfinite(matrix).all(0);selected=[r for r,ok in zip(rows,complete)if ok];delta=matrix[:5,complete].mean(0)-matrix[5:,complete].mean(0)
 lo=np.nan_to_num(matrix[:5],nan=0).mean(0)-np.nan_to_num(matrix[5:],nan=1).mean(0)
 hi=np.nan_to_num(matrix[:5],nan=1).mean(0)-np.nan_to_num(matrix[5:],nan=0).mean(0)
 return {'n_retained':n,'n_retained_groups':len(groups(rows)),'n_complete':int(complete.sum()),'invalid_ids':[r['id']for r,ok in zip(rows,complete)if not ok],'estimate':interval(delta,selected),'retained_bounds':{'row_pp':[100*weighted(lo,rows),100*weighted(hi,rows)],'behavior_pp':[100*weighted(lo,rows,True),100*weighted(hi,rows,True)]},'interval_scope':'complete nine-unit paired rows, conditional on the fixed vectors; group-cluster bootstrap, not iid row bootstrap'}
def field_diagnostics(names,rows):
 invalid={};lengths={}
 for name in names:
  invalid[name]={'HB_label':[],'MinHash_label':[],'WG_Harmful_request':[],'WG_Harmful_response':[],'WG_Response_refusal':[],'WG_harmfulness_not_applicable':[]};lengths[name]={}
  for row in rows:
   key=row['id'];hb=load(B/'canonical254/scores'/name/(key+'.json'));w=load(B/'wildguard_pair254'/(name+'_scores')/(key+'.json'))
   if hb['label']is None:invalid[name]['MinHash_label'if row['layer']=='copyright'else'HB_label'].append(key)
   for label in ['Harmful request','Harmful response','Response refusal']:
    if row['layer']=='copyright'and label!='Response refusal':continue
    if w['labels'][label]not in ['yes','no']:invalid[name]['WG_'+label.replace(' ','_')].append(key)
   if row['layer']=='copyright':invalid[name]['WG_harmfulness_not_applicable'].append(key)
   if w['input_tokens']>4096:lengths[name].setdefault(row['layer'],[]).append({'id':key,'input_tokens':w['input_tokens']})
 return {'INVALID_ids_by_condition_field':invalid,'WG_inputs_over4096_by_condition_layer':lengths,'copyright_harmfulness_NA_is_not_INVALID':True}
def summarize_names(names,rows):
 result={}
 for judge in ['HB','WildGuard','MinHash']:
  result[judge]={}
  for panel,allrows in scope(rows).items():
   subset=applicable(allrows,judge);result[judge][panel]={'n_retained':len(allrows),'n_applicable':len(subset),'metric':'copyright_match'if judge=='MinHash'else'response_harmfulness','conditions':{}}
   for name in names:result[judge][panel]['conditions'][name]=rate(labels(name,judge,subset)[0],subset)
 return result
def primary(rows):
 out={}
 for judge in ['HB','WildGuard','MinHash']:
  out[judge]={}
  for panel,allrows in scope(rows).items():
   subset=applicable(allrows,judge);matrix=np.array([labels(n,judge,subset)[0]for n in UNITS]);out[judge][panel]=effect(matrix,subset)
 return out
def rank_and_mean_permutation(rows):
 result={}
 for judge in ['HB','WildGuard','MinHash']:
  result[judge]={}
  for panel,allrows in scope(rows).items():
   subset=applicable(allrows,judge)
   if not subset:continue
   mat=np.array([labels(n,judge,subset)[0]for n in UNITS]);valid=np.isfinite(mat).all(0);complete=[r for r,ok in zip(subset,valid)if ok]
   if not complete:continue
   result[judge][panel]={}
   for equal in [False,True]:
    values=np.array([weighted(v[valid],complete,equal)for v in mat]);observed=float(values[:5].mean()-values[5:].mean());perms=[]
    for a in itertools.combinations(range(9),5):
     b=[i for i in range(9)if i not in a];perms.append(float(values[list(a)].mean()-values[b].mean()))
    lower=sum(x<=observed+1e-12 for x in perms)/126;upper=sum(x>=observed-1e-12 for x in perms)/126;absolute=sum(abs(x)>=abs(observed)-1e-12 for x in perms)/126
    result[judge][panel]['behavior_weighted'if equal else'row_weighted']={'unit_rates_pct':dict(zip(UNITS,(values*100).tolist())),'difference_pp':observed*100,'allocations':126,'directional_lower_p':lower,'two_sided_absolute_mean_statistic_p':absolute,'doubled_smaller_tail_p':min(1.,2*min(lower,upper)),
      'seed_direction_pp':{l:{rr:float(100*(values[i]-values[j+5]))for j,rr in enumerate(UNITS[5:])}for i,l in enumerate(UNITS[:5])},
      'leave_one_unit_pp':{n:float(100*(np.delete(values[:5],i).mean()-values[5:].mean()if i<5 else values[:5].mean()-np.delete(values[5:],i-5).mean()))for i,n in enumerate(UNITS)},
      'scope':'same complete-nine row set; nine units assumed exchangeable under null; vector-population sampling not established'}
 return result
def kappa(a,b):
 pairs=[(x,y)for x,y in zip(a,b)if x is not None and y is not None];counts={f'{x}{y}':sum(i==x and j==y for i,j in pairs)for x in [0,1]for y in [0,1]};n=len(pairs)
 if not n:return {'n':0,'counts':counts,'kappa':None}
 agree=(counts['00']+counts['11'])/n;pa=(counts['10']+counts['11'])/n;pb=(counts['01']+counts['11'])/n;chance=pa*pb+(1-pa)*(1-pb)
 return {'n':n,'counts':counts,'axes':'v2, WG response-refusal','kappa':(agree-chance)/(1-chance)if chance<1 else None}
def attribution(rows):
 tree=ast.parse((R/'tools/handoff_20261106/audit.py').read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='v3');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'frozen_v3','exec'),ns);v3=ns['v3'];result={};agreement={}
 for name in ['alpha0',*UNITS]:
  flags={};a=[];b=[]
  for row in rows:
   key=row['id'];text=load(B/'canonical254/generation.private'/name/(key+'.json'))['result']['text'];wg=load(B/'wildguard_pair254'/(name+'_scores')/(key+'.json'))['labels']['Response refusal'];r=int(new_rule(text));w={'yes':1,'no':0}.get(wg);flags[key]=(r,int(bool(r or v3(text))),w);a.append(r);b.append(w)
  agreement[name]=kappa(a,b)
  if name=='alpha0':continue
  result[name]={}
  for judge in ['HB','WildGuard']:
   subset=applicable(rows,judge);base,_=labels('alpha0',judge,subset);current,_=labels(name,judge,subset);down=[r['id']for r,x,y in zip(subset,base,current)if x==1 and y==0]
   result[name][judge]={'down_flips':len(down),'down_ids':down,'v2_refusal':sum(flags[k][0]==1 for k in down),'v2_union_v3_refusal':sum(flags[k][1]==1 for k in down),'WG_refusal':sum(flags[k][2]==1 for k in down),'WG_refusal_invalid_ids':[k for k in down if flags[k][2]is None],'descriptive_not_mechanism':True}
 return {'downflip_attribution':result,'v2_WG_refusal_agreement':agreement,'model_annotations_without_human_calibration':True}
def exposure(rows):
 selected={'untouched_standard_JBB_66':[r for r in rows if r['untouched']and r['layer']in ['standard','jbb']],
 'untouched_contextual_73':[r for r in rows if r['untouched']and r['layer']=='contextual'],
 'untouched_copyright_89':[r for r in rows if r['untouched']and r['layer']=='copyright'],
 'historically_used':[r for r in rows if r['historical_group_used']]}
 for flag in ['fit12','legacy46','dev22','val70','train_strat97','legacy_additional']:selected['group_mark_'+flag]=[r for r in rows if flag in r['group_flags']]
 return {name:{'n_rows':len(part),'n_groups':len(groups(part)),'results':primary(part)}for name,part in selected.items()}
def diagnostics(rows):
 remote="from pathlib import Path;import json,hashlib;p=Path('/home/dell/Def/results/audit/pair500/search_cap.private');print(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in p.glob('*.json')}))"
 source= json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=remote,text=True))
 (B/'search_cap.private').mkdir(exist_ok=True)
 subprocess.run(['rsync','-a','--ignore-existing','node01:/home/dell/Def/results/audit/pair500/search_cap.private/',str(B/'search_cap.private')+'/'],check=True,stdout=subprocess.DEVNULL)
 assert all(sha(B/'search_cap.private'/name)==value for name,value in source.items()),'Search-cap metadata differs from source; preserve before repair'
 final={r['id']:r['prompt_sha256']for r in load(B/'frozen_prompt_snapshot.json')['rows']}
 result={}
 for panel,part in scope(rows).items():
  total={'n':len(part),'zero_score':0,'fallback':0,'candidates_below40':0,'valid_candidate_sum_shortfall':0,'exact_cap_trace_n':0,'exact_reached512':0,'exact_selected_tokens_known_n':0,'pilot_no_trace_n':0,'pilot_retokenized_cap_proxy':0,'unknown_all_candidates_refusal_n':len(part)}
  for row in part:
   x=load(B/'generations.private'/(row['id']+'.json'));score=x['best'].get('score');total['zero_score']+=int(bool(score is not None and not score[0]));total['fallback']+=int(bool(x['fallback']));v=x['valid_candidates'];total['candidates_below40']+=int(v<40);total['valid_candidate_sum_shortfall']+=v if v<40 else 0
   p=B/'search_cap.private'/(row['id']+'.json')
   if p.exists():
    cap=load(p);assert cap['prompt_sha256']==final[row['id']];total['exact_cap_trace_n']+=1;total['exact_selected_tokens_known_n']+=int(cap['generated_tokens']is not None);total['exact_reached512']+=int(cap['reached_cap']is True)
   else:total['pilot_no_trace_n']+=1;total['pilot_retokenized_cap_proxy']+=int(score is not None and score[1]>=512)
  result[panel]=total
 return {'by_panel':result,'source_metadata_file_sha256':source,'source_missing_trace_ids':[r['id']for r in rows if(r['id']+'.json')not in source],'missing_trace_is_not_zero_cap_hits':True}
def main():
 implementation=load(B/'read_order10/reader_implementation_v2.json')
 assert sha(Path(__file__))==implementation['code_sha256'],'Reader changed after its pre-read freeze'
 assert sha(R/'docs/254_ADDENDUM10_FINAL_READ_ORDER_AND_CACHE_ASSERTIONS.md')==implementation['read_plan_sha256']
 assert sha(R/'tools/handoff_20261106/pair254_all13_read_gate.py')==implementation['admission_code_sha256']
 ap=argparse.ArgumentParser();ap.add_argument('--step',type=int,choices=range(1,9),required=True);args=ap.parse_args();s=readiness();assert s['full500_all13_ready'],'No read before all500/all13/both judges'
 expected=load(B/'frozen_prompt_snapshot.json');ids=[r['id']for r in expected['rows']];audit=load(B/'row_audit.json');lookup={r['id']:r for r in audit['flags']};rows=[lookup[k]for k in ids];assert len(rows)==500 and len(groups(rows))==479
 previous=None
 if args.step>1:
  prior=D/f'{args.step-1:02d}.json';assert prior.exists();previous=sha(prior);assert load(prior)['snapshot_sha256']==sha(B/'frozen_prompt_snapshot.json');assert load(prior)['reader_code_sha256']==sha(Path(__file__))and load(prior)['step']==args.step-1
 dest=D/f'{args.step:02d}.json';assert not dest.exists(),'Each read step is immutable; corrections require an appended artifact'
 if args.step==1:
  data={'readiness':s,'signature_chains_verified':verify_prompt_chain(),'source_audit_sha256':sha(B/'row_audit.json'),'lifecycle_receipts':{p.name:load(p)for p in(B/'read_order10/lifecycle').glob('*.json')if p.name!='observer_live.json'},'no_outcome_values_selected':True}
 elif args.step==2:data={'alpha0':summarize_names(['alpha0'],rows),'field_diagnostics':field_diagnostics(['alpha0'],rows),'no_single_mixed_HB400_or_all500_ASR':True,'HarmBench400_retained_as_harm300_plus_MinHash100':True}
 elif args.step==3:
  base=load(D/'02.json')['data']['alpha0'];data={'per_functional_layer':{},'copyright_never_supports_abstract_efficacy':True,'continue_all_frozen_conditions':True}
  for judge in ['HB','WildGuard']:
   data['per_functional_layer'][judge]={}
   for layer in ['standard','contextual','jbb']:
    cell=base[judge][layer]['conditions']['alpha0'];lo,hi=cell['retained_bounds_pct']
    flag='unscored'if lo is None else'no_dynamic_range'if hi<25 else'dynamic_range'if lo>=25 else'threshold_uncertain_due_INVALID'
    data['per_functional_layer'][judge][layer]={'alpha0_valid_only_pct':cell['valid_only_pct'],'retained_bounds_pct':[lo,hi],'flag':flag}
 elif args.step==4:
  data={'primary':primary(rows),'unit_rates':summarize_names(UNITS,rows),'field_diagnostics':field_diagnostics(UNITS,rows)}
  data['signs']={judge:{layer:data['primary'][judge][layer]['estimate']['row_mean_pp']for layer in ['all_retained','standard','contextual','jbb']}for judge in ['HB','WildGuard']}
  data['all_required_point_signs_negative']=all(v is not None and v<0 for cells in data['signs'].values()for v in cells.values());data['scope']='Signs, CIs and INVALID bounds must be read together; low-dynamic-range layers do not upgrade claims.'
 elif args.step==5:data=rank_and_mean_permutation(rows)
 elif args.step==6:data=attribution(rows)
 elif args.step==7:data=exposure(rows)
 else:data=diagnostics(rows)
 artifact={'utc':utc(),'step':args.step,'previous_receipt_sha256':previous,'snapshot_sha256':sha(B/'frozen_prompt_snapshot.json'),'reader_code_sha256':sha(Path(__file__)),'frozen_read_plan_sha256':sha(R/'docs/254_ADDENDUM10_FINAL_READ_ORDER_AND_CACHE_ASSERTIONS.md'),'data':data}
 write(dest,artifact);dest.chmod(0o444)
 with(R/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{artifact["utc"]} PAIR254_ORDERED_READ step={args.step} SHA={sha(dest)} previous={previous} all500/all13/both admitted, snapshotSHA={artifact["snapshot_sha256"]}; step saved before next read.\n')
 print(json.dumps({'utc':artifact['utc'],'step':args.step,'file':str(dest.relative_to(R)),'sha256':sha(dest),'previous_sha256':previous}))
if __name__=='__main__':main()
