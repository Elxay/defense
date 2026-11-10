"""External-human diagnostic only; never reads new SORRY target conditions."""
from pathlib import Path
import collections, datetime, hashlib, json, re, sys, unicodedata
import numpy as np
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';O=R/'results/audit/sorry296'
sys.path.insert(0,str(R/'tools/handoff_20261106'));sys.path.insert(0,str(R/'src'))
from unified300_human_agreement import stats
from judge.refusal import new_rule
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
 with p.open()as f:return [json.loads(line)for line in f]
def signature(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def extended(y,p):
 s=stats(y,p);a=np.asarray(y);s['recall_human_nonfulfillment_all']=s['confusion_human0_1_by_model0_1'][0][0]/int((a==0).sum())if (a==0).sum() else None
 s['recall_human_fulfillment_all']=s['confusion_human0_1_by_model0_1'][1][1]/int((a==1).sum())if (a==1).sum() else None
 s['invalid_by_human_label']=[sum(g==v and z not in [0,1]for g,z in zip(y,p))for v in [0,1]]
 s['error_all_including_INVALID']=1-s['accuracy_all_lower'];return s
def main():
 plan=load(U/'human_refusal_diagnostics_plan.json');assert sha(__file__)==plan['worker_sha256'];assert sha(R/'src/judge/refusal.py')==plan['v2_source_sha256']
 output=U/'human_refusal_diagnostics.json';assert not output.exists()
 assert load(U/'active_protocol.json')['new_test_generation_allowed']is False
 gold=load(U/'human_gold.private.json');inputs={r['id']:r for r in load(U/'human_inputs.private.json')};ids=[r['id']for r in gold];y=np.array([r['human_label']for r in gold]);q=np.array([r['question_id']for r in gold])
 predictors={k:[]for k in ['SORRY','HB','WG_harmful','WG_1_minus_refusal']};stratum=[];coded=[]
 warning=re.compile(plan['warning_marker_regex'],re.I)
 for r in gold:
  k=r['id'];raw=load(U/'WG_scores'/(k+'.json'));ref={'yes':1,'no':0}.get(raw['labels']['Response refusal']);harm={'yes':1,'no':0}.get(raw['labels']['Harmful response']);v2=int(new_rule(inputs[k]['response']))
  predictions={'SORRY':load(U/'SORRY_scores'/(k+'.json'))['label'],'HB':load(U/'HB_scores'/(k+'.json'))['label'],'WG_harmful':harm,'WG_1_minus_refusal':None if ref is None else 1-ref}
  for n,p in predictions.items():predictors[n].append(p)
  if ref is None:kind='WG_refusal_INVALID'
  elif ref and v2:kind='front_anchored_refusal_signal'
  elif ref:kind='WG_only_refusal_signal'
  elif v2:kind='v2_WG_refusal_conflict'
  elif warning.search(inputs[k]['response']):kind='warning_nonrefusal_candidate'
  else:kind='unwarned_nonrefusal_candidate'
  stratum.append(kind);coded.append({'id':k,'type_proxy':kind,'v2_refusal':v2,'WG_refusal':ref,'human_label':r['human_label'],'predictions':predictions})
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan_sha256':sha(U/'human_refusal_diagnostics_plan.json'),'N':len(ids),'overall':{k:extended(y,p)for k,p in predictors.items()},'strata':{},
   'stratification_caveat':'Operational model/rule/lexical proxies, not independent four-type semantic annotations. WG is used to define strata, so conditional error profiles do not establish a steering mechanism or transport to new responses.'}
 for kind in sorted(set(stratum)):
  ix=np.array([i for i,s in enumerate(stratum)if s==kind]);result['strata'][kind]={'N':len(ix),'human_nonfulfillment':int((y[ix]==0).sum()),'human_fulfillment':int((y[ix]==1).sum()),'judges':{k:extended(y[ix],[p[i]for i in ix])for k,p in predictors.items()}}
 result['base_OOD']={}
 for name,ix in [('base',np.array([i for i,r in enumerate(gold)if r['prompt_style']=='base'])),('OOD',np.array([i for i,r in enumerate(gold)if r['prompt_style']!='base']))]:result['base_OOD'][name]={k:extended(y[ix],[p[i]for i in ix])for k,p in predictors.items()}
 # Paired cluster intervals on the external-human data, not a test-effect gate.
 keys=sorted(set(q));rng=np.random.default_rng(plan['bootstrap_seed']);draw=rng.integers(0,len(keys),(2000,len(keys)))
 bootstrap={}
 for name in ['WG_harmful','WG_1_minus_refusal']:
  cells=[]
  for key in keys:
   ix=np.where(q==key)[0];p=[predictors[name][i]for i in ix];s=stats(y[ix],p);m=s['confusion_human0_1_by_model0_1'];cells.append([m[0][0],m[0][1],m[1][0],m[1][1],len(ix)])
  values=np.array(cells)[draw].sum(axis=1);tn,fp,fn,tp,total=values.T;n=tn+fp+fn+tp;po=(tn+tp)/n;pe=((tn+fp)*(tn+fn)+(fn+tp)*(fp+tp))/n**2
  bootstrap[name]=((tn+tp)/total,(po-pe)/(1-pe))
 dacc=bootstrap['WG_1_minus_refusal'][0]-bootstrap['WG_harmful'][0];dk=bootstrap['WG_1_minus_refusal'][1]-bootstrap['WG_harmful'][1]
 ciacc=np.quantile(dacc,[.025,.975]).tolist();cik=np.quantile(dk,[.025,.975]).tolist()
 result['WG_field_comparison']={'unit':'base instruction','clusters':len(keys),'B':2000,'seed':plan['bootstrap_seed'],
  'accuracy_gain_pp':100*(result['overall']['WG_1_minus_refusal']['accuracy_all_lower']-result['overall']['WG_harmful']['accuracy_all_lower']),
  'accuracy_gain_CI95_pp':[100*v for v in ciacc],'kappa_gain':result['overall']['WG_1_minus_refusal']['kappa_valid']-result['overall']['WG_harmful']['kappa_valid'],'kappa_gain_CI95':cik,
  'criterion_frozen_before_this_diagnostic':'both point gains positive and both paired instruction-bootstrap95 lower bounds >0; user qualitative clearly-higher operationalized without pp cutoff',
  'selected_WG_SORRY_fulfillment_field':'1-minus-Response-refusal'if ciacc[0]>0 and cik[0]>0 else'Harmful-response',
  'external_data_used_for_field_choice':True,'new_target_condition_effects_used':False}
 # Split record identity and input-content overlap are distinct questions.
 D=O/'downloads.private';train=rows(D/'sorry-bench-human-judgment-202503/train.jsonl');test=rows(D/'sorry-bench-human-judgment-202503/test.jsonl');oldtrain=rows(D/'sorry-bench-human-judgment-202406/train.jsonl')
 base={r['question_id']:r['turns'][0]for r in rows(D/'sorry-bench-202503/question.jsonl')};oldbase={r['question_id']:r['turns'][0]for r in rows(D/'sorry-bench-202406/question.jsonl')}
 def reply(r):return r['choices'][0]['turns'][0]
 def audit(a,b,mapa,mapb):
  full=lambda r,m:(m[r['question_id']],r['model_id'],r['prompt_style'],reply(r))
  pair=lambda r,m:(m[r['question_id']],reply(r))
  af={signature(full(r,mapa))for r in a};ap={signature(pair(r,mapa))for r in a};aids={r['answer_id']for r in a};over=[];full_over=[]
  for i,r in enumerate(b):
   if signature(pair(r,mapb))in ap:over.append('test_'+str(i).zfill(4))
   if signature(full(r,mapb))in af:full_over.append('test_'+str(i).zfill(4))
  return {'train_N':len(a),'test_N':len(b),'record_answer_ID_overlap':len(aids&{r['answer_id']for r in b}),'same_instruction_model_style_reply_overlap_testIDs':full_over,
   'same_instruction_reply_overlap_testIDs':over,'shared_instruction_texts':len({mapa[r['question_id']]for r in a}&{mapb[r['question_id']]for r in b})}
 result['split_audit']={'202503_train_vs_202503_test':audit(train,test,base,base),'202406_train_vs_202503_test':audit(oldtrain,test,oldbase,base),
  '202503_train_sha256':sha(D/'sorry-bench-human-judgment-202503/train.jsonl'),'202503_test_sha256':sha(D/'sorry-bench-human-judgment-202503/test.jsonl'),
  '202406_train_sha256':sha(D/'sorry-bench-human-judgment-202406/train.jsonl'),'202406_train_revision':'395ff7e7ea75f6d328845c3743d127a6477054a7',
  'split_unit':'different model responses within every base instruction; 3 ID+3 OOD train and 5 ID+5 OOD test per instruction',
  'checkpoint_training_provenance_limit':'Published train/test records and README audited; no independently supplied actual optimizer training-row manifest. Do not claim unseen-instruction or absolute content disjointness.'}
 result['paper_reference']={'url':'https://arxiv.org/html/2406.14598v2','tables':[1,6],'finetuned_Mistral_kappa':.810,'paper_refusal_recall':.911,'paper_fulfillment_recall':.934,'our_protocol_implementation_not_forced_to_match_table':True}
 private=U/'human_response_proxy_labels.private.json';private.write_text(json.dumps(coded,indent=2)+'\n');result['coded_row_labels_sha256']=sha(private)
 output.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'overall':result['overall'],'field_comparison':result['WG_field_comparison'],'strata':{k:{'N':v['N'],'errors_pct':{j:round(s['error_all_including_INVALID']*100,3)for j,s in v['judges'].items()}}for k,v in result['strata'].items()},'split':result['split_audit']},indent=2))
 print('OUTPUT_SHA',sha(output))
if __name__=='__main__':main()
