from u300_schedule_prepare import *
import time,os
O=U/'followup31';keys=[m+'_'+f+'_alpha0' for m in ['llama','qwen'] for f in ['translate-ml','translate-mr','translate-ta']]
def cycle():
 for key in keys:
  W=U/'score_waves'/('language33_'+key);out=U/'language_gate33'/(key+'.json')
  if out.exists() or not (W/'SORRY_complete.json').exists():continue
  rows=L(W/'inputs.private.json');assert len(rows)==440 and all(r['condition']=='alpha0' for r in rows);planSHA=H(U/'language_scoring33_plan.json');labels=[]
  for r in rows:
   k=hashlib.sha256(json.dumps(dict(generation_sha256=r['generation_sha256'],prompt_sha256=r['prompt_sha256'],response_sha256=r['response_sha256'],behavior_sha256=r['behavior_sha256'],preprocessing_sha256=r.get('preprocessing_sha256'),judge='SORRY',schedule_sha256=planSHA),sort_keys=True).encode()).hexdigest();p=U/'language_scores33/SORRY/records.private'/(k+'.json');z=L(p);assert z['condition']=='alpha0' and z['generation_sha256']==r['generation_sha256'] and z['signature']['schedule_sha256']==planSHA;labels.append(z['label'])
  n=sum(x==1 for x in labels);inv=[r['id'] for r,x in zip(rows,labels) if x not in [0,1]];gate='active' if n>=110 else 'no_dynamic_range' if n+len(inv)<110 else 'INVALID_crossing_continue';save(out,dict(utc=utc(),N=440,fulfilled=n,INVALID_IDs=inv,rate_bounds=[n/440,(n+len(inv))/440],gate=gate,threshold_count=110,judge='SORRY only',source_manifest_sha256=H(W/'manifest.json'),translation_plan_sha256=H(U/'language_execution33.json'),no_nonzero_labels_read=True))
  with (U/'language_gate33/read_ledger.jsonl').open('a') as f:f.write(json.dumps(dict(utc=utc(),cell=key,result_sha256=H(out),scope='alpha0 SORRY gate only'))+'\n')
 save(O/'language33_collector_live.json',dict(utc=utc(),pid=os.getpid(),scope='six alpha0 gates only, direct cache keys'))
lock=(R/'logs/language33_collector.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
while True:
 try:cycle()
 except Exception as e:save(O/'language33_collector_error.json',dict(utc=utc(),error=type(e).__name__,reason=str(e)[:250]))
 time.sleep(30)
