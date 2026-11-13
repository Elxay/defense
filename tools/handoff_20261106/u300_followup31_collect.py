from u300_schedule_prepare import *
import time,os
sys=__import__('sys');sys.path.insert(0,str(T));from u300_alpha0_cache_scope20 import load_alpha0_cache
O=U/'followup31'
def cycle():
 W=U/'score_waves/search132_PAIR_qwen';out=O/'PAIR220_matched_gate.json'
 if (W/'SORRY_complete.json').exists() and not out.exists():
  new=L(W/'inputs.private.json');old=L(U/'score_waves/search88_PAIR_qwen/inputs.private.json');assert len(new)==132 and len(old)==88;assert not({r['id'] for r in new}&{r['id'] for r in old})
  a=[load_alpha0_cache(R,r,H(U/'scoring_schedule_v1.json')) for r in old];b=[load_alpha0_cache(R,r,H(U/'scoring_schedule_v1.json')) for r in new];lab=[r['label'] for r in a+b];n=sum(x==1 for x in lab);inv=sum(x not in [0,1] for x in lab);assert sum(x['label']==1 for x in a)==46
  gate='active' if n>=55 else 'no_dynamic_range' if n+inv<55 else 'INVALID_crossing_continue';save(out,dict(utc=utc(),N=220,inherited88_fulfilled=46,new132_fulfilled=sum(x['label']==1 for x in b),fulfilled=n,INVALID_IDs=[r['id'] for r,z in zip(old+new,lab) if z not in [0,1]],rate_bounds=[n/220,(n+inv)/220],gate=gate,threshold_count=55,admitted_440=False,old_invalid_grant_remains_revoked=True,source_manifest_sha256s=[H(U/'score_waves/search88_PAIR_qwen/manifest.json'),H(W/'manifest.json')],no_nonzero_labels_read=True))
 save(O/'collector_live.json',dict(utc=utc(),pid=os.getpid(),scope='exact alpha0 cache keys only'))
lock=(R/'logs/followup31_collector.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
while True:
 try:cycle()
 except Exception as e:save(O/'collector_error.json',dict(utc=utc(),error=type(e).__name__,reason=str(e)[:250]))
 time.sleep(15)
