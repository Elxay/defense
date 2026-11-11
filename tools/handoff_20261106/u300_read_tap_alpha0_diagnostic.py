"""The only authorized read here is the 20-row independent TAP alpha0 diagnostic."""
from pathlib import Path
import collections,hashlib,json
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
D=U/'TAP_alpha0_independent_replay';W=U/'score_waves/TAP_alpha0_diagnostic';O=D/'read_steps'
assert L(W/'SORRY_complete.json')['N_inputs']==20
gate=L(W/'SORRY_gate20.json');assert gate['passed']
P=L(D/'plan.json');meta={(r['model'],r['id']):r for r in P['rows']}
rows=L(W/'inputs.private.json');schedule_sha=H(U/'scoring_schedule_v1.json');files=[]
for r in rows:
 key=hashlib.sha256(json.dumps(dict(generation_sha256=r['generation_sha256'],
    prompt_sha256=r['prompt_sha256'],response_sha256=r['response_sha256'],behavior_sha256=r['behavior_sha256'],
    preprocessing_sha256=None,judge='SORRY',schedule_sha256=schedule_sha),sort_keys=True).encode()).hexdigest()
 p=U/'main_scores/SORRY/records.private'/(key+'.json');assert p.exists();files.append((r,p))
save(O/'01_status.json',dict(utc=utc(),scope='only TAP alpha0 timing pilots, no nonzero read',N=20,
 main_replay_complete=L(D/'complete.json')['utc'],score_complete=L(W/'SORRY_complete.json')['utc'],
 gate20_sha256=H(W/'SORRY_gate20.json'),score_files_sha256={str(r['model'])+':'+str(r['id']):H(p) for r,p in files}))
previous=H(O/'01_status.json');started=utc();result=[];details=[]
for model in ['llama','qwen']:
 matrix=collections.Counter();n=0;fulfill=0;inv=0
 for r,p in files:
  if r['model']!=model:continue
  z=L(p);assert z['generation_sha256']==r['generation_sha256'];y=z['label'];m=meta[model,r['id']]
  assert y in [0,1,None];n+=1;fulfill+=y==1;inv+=y is None
  matrix[('early' if m['early_stop'] else 'not_early','INVALID' if y is None else 'fulfilled' if y else 'not_fulfilled')]+=1
  details.append(dict(model=model,id=r['id'],internal_early_stop=m['early_stop'],SORRY_fulfilled=y,
                      fallback=m['fallback']))
 result.append(dict(model=model,N=n,fulfilled=fulfill,not_fulfilled=n-fulfill-inv,INVALID=inv,
   fulfillment_percent=100*fulfill/n,early={k:matrix['early',k] for k in ['fulfilled','not_fulfilled','INVALID']},
   not_early={k:matrix['not_early',k] for k in ['fulfilled','not_fulfilled','INVALID']}))
save(O/'02_alpha0_early_stop_cross_table.json',dict(read_started_utc=started,utc=utc(),previous_step_sha256=previous,
 rows=result,details=details,scope='descriptive, N=10 per model; internal stopping is not independent fulfillment',
 no_tier_algorithm_alpha_or_nonzero_effect_changes=True))
summary=dict(utc=utc(),steps=[dict(step=1,utc=L(O/'01_status.json')['utc'],sha256=H(O/'01_status.json')),
 dict(step=2,utc=L(O/'02_alpha0_early_stop_cross_table.json')['utc'],sha256=H(O/'02_alpha0_early_stop_cross_table.json'))],rows=result)
save(D/'diagnostic_read_receipt.json',summary)
commit=publish([Path(__file__),O/'01_status.json',O/'02_alpha0_early_stop_cross_table.json',D/'diagnostic_read_receipt.json'],
              'Read only independent TAP alpha0 timing-row fulfillment versus internal early stop')
print(json.dumps(dict(commit=commit,**summary)))
