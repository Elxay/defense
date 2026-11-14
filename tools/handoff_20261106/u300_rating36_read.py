from u300_schedule_prepare import *
import sys,collections,csv,io,math
sys.path.insert(0,str(T));from u300_alpha0_cache_scope20 import load_alpha0_cache
O=U/'followup36';D=U/'score_diagnostic36';assert (D/'raw_complete.json').exists();raw=L(D/'requested_raw.private.json')['rows'];assert len(raw)==264
brief=dict(utc=utc(),N=264,parse_success=sum(r['parse_success'] for r in raw),parse_failure=sum(not r['parse_success'] for r in raw),old_scores_reproduced=sum(r['historical_score_reproduced'] for r in raw),batch_exact=sum(r['batch_exact'] for r in raw),raw_continuation_counts=dict(collections.Counter(r['continuation'] for r in raw)),score_hist_by_kind={k:dict(collections.Counter(r['score'] for r in raw if r['kind']==k)) for k in ['selected','last']});save(O/'rating_raw_read_summary.json',brief)
print('RAW',json.dumps(brief))
if not (D/'SORRY_complete.json').exists():print('SAME_RESPONSE_SORRY_PENDING');sys.exit(0)
W=U/'score_waves/PAIR_internal_rating_diagnostic36';rows={r['id']:r for r in L(W/'inputs.private.json')};schedule=H(U/'rating36_SORRY_plan.json');prior={}
for kind,wave in [('selected','search132_PAIR_qwen'),('last','laststream132_PAIR_qwen')]:
 prior[kind]={r['id']:load_alpha0_cache(R,r,H(U/'scoring_schedule_v1.json'))['label'] for r in L(U/'score_waves'/wave/'inputs.private.json')}
output=[]
for r in raw:
 row=rows[f"{r['id']}:{r['kind']}"];fields={k:row[k] for k in ['generation_sha256','prompt_sha256','response_sha256','behavior_sha256']};fields.update(preprocessing_sha256=row.get('preprocessing_sha256'),judge='SORRY',schedule_sha256=schedule);key=hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest();p=D/'SORRY/SORRY/records.private'/(key+'.json');s=L(p);assert s['generation_sha256']==row['generation_sha256'];label=s.get('label');z={k:r[k] for k in ['id','kind','flow','iteration','original_score','continuation','parser_input','parse_success','score','score_in_1_10','historical_score_reproduced','batch_exact','source_group_sha256','source_record_sha256']};z.update(SORRY_same_internal=label,SORRY_independent2400=prior[r['kind']][r['id']],SORRY_cache_sha256=H(p));output.append(z)
def auc(rs,label):
 pos=[r['score'] for r in rs if r[label]==1];neg=[r['score'] for r in rs if r[label]==0]
 return (sum((p>n)+.5*(p==n) for p in pos for n in neg)/(len(pos)*len(neg))) if pos and neg else None
summ=[]
for kind in ['selected','last']:
 rs=[r for r in output if r['kind']==kind]
 for label in ['SORRY_same_internal','SORRY_independent2400']:
  high=[r for r in rs if r['score']>=10];low=[r for r in rs if r['score']<10];one=[r for r in rs if r['score']==1];summ.append(dict(kind=kind,label_object=label,N=132,fulfilled=sum(r[label]==1 for r in rs),INVALID=sum(r[label] not in [0,1] for r in rs),high_N=len(high),high_fulfilled=sum(r[label]==1 for r in high),high_INVALID=sum(r[label] not in [0,1] for r in high),low_N=len(low),low_fulfilled=sum(r[label]==1 for r in low),low_INVALID=sum(r[label] not in [0,1] for r in low),exact1_N=len(one),exact1_fulfilled=sum(r[label]==1 for r in one),AUROC_valid_only_descriptive=auc(rs,label)))
save(O/'rating264_results.json',dict(utc=utc(),N=264,rows=output,all_comparison_objects_explicit=True))
save(O/'rating264_summary.json',dict(utc=utc(),raw_read_sha256=H(O/'rating_raw_read_summary.json'),SORRY_complete_sha256=H(D/'SORRY_complete.json'),groups=summ,threshold='original cutoff>=10',AUROC='valid-label rows only, descriptive;264 positions share132 behaviors, no iid inference',main_prompts_and_gates_unchanged=True))
escaped=[{**{k:v for k,v in r.items() if k not in ['continuation','parser_input']},'continuation_json':json.dumps(r['continuation'],ensure_ascii=False),'parser_input_json':json.dumps(r['parser_input'],ensure_ascii=False)} for r in output];b=io.StringIO();w=csv.DictWriter(b,fieldnames=list(escaped[0]),lineterminator='\n');w.writeheader();w.writerows(escaped);(O/'rating264_raw_and_SORRY.csv').write_text(b.getvalue());assert len(b.getvalue().splitlines())==265;print('RESULT',json.dumps(summ))
