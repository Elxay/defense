"""CPU engineering-only exact-key batch translator screen and B4 fallback."""
from u300_schedule_prepare import *
import sys,time,fcntl
sys.path.insert(0,str(T));from u300_alpha0_cache_scope20 import load_alpha0_cache
D=U/'translation_batch_engineering20'
def cycle():
 for B in [8,4]:
  here=D/('B'+str(B));result=here/'label_gate.json';failed=(here/'failed.json').exists()
  if failed:pass
  elif result.exists():gate=L(result);failed=not gate['passed']
  elif (here/'complete.json').exists() and (U/'score_waves'/('translation_engineering_B'+str(B))/'SORRY_complete.json').exists() and (U/'score_waves/translation_engineering_B1/SORRY_complete.json').exists():
   W=U/'score_waves'/('translation_engineering_B'+str(B));V=U/'score_waves/translation_engineering_B1';a=L(V/'inputs.private.json');b=L(W/'inputs.private.json');assert len(a)==len(b)==100;changes=[];invalid=[];up=down=0
   for x,y in zip(a,b):
    assert x['id']==y['id'];left=load_alpha0_cache(R,x,H(U/'scoring_schedule_v1.json'));right=load_alpha0_cache(R,y,H(U/'scoring_schedule_v1.json'));l=left['label'];r=right['label']
    if l not in [0,1] or r not in [0,1]:invalid.append(x['id']);changes.append(x['id'])
    elif l!=r:
     changes.append(x['id']);up+=int(l==0 and r==1);down+=int(l==1 and r==0)
   gate=dict(utc=utc(),N=100,B=B,disagreement=len(changes),changed_engineering_IDs=changes,INVALID_engineering_IDs=invalid,B1_zero_to_batch_one=up,B1_one_to_batch_zero=down,passed=len(changes)<=2,source_manifests=[H(V/'manifest.json'),H(W/'manifest.json')],scope='alpha0 translation engineering only',formal_translation_worker_admitted=False)
   save(result,gate);failed=not gate['passed']
  else:continue
  if not failed:
   save(D/'selected_candidate.json',dict(utc=utc(),B=B,engineering_gate_sha256=H(result),engineering_passed=True,formal_execution_admitted=False));return
  if B==8:
   with (R/'logs/unified300_catalog_mutation.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json')
    if not any(t['id']=='translation_engineering20_B4' for t in cat['tasks']):
     cat['tasks'].append(dict(id='translation_engineering20_B4',priority=18,site='innet',gpus=[3],kind='translation_engineering_only',yieldable=False,argv=['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/u300_translation_batch_worker20.py','4'],requires=[dict(path='results/audit/unified300/translation_batch_engineering20/B1/complete.json')]))
     save(U/'ready_queue_catalog.json',cat)
  else:save(D/'selected_candidate.json',dict(utc=utc(),B=1,reason='Frozen B8 then B4 screen failed; original single path fallback',engineering_passed=False,formal_execution_admitted=False))
 save(U/'translation_batch_gatekeeper20_live.json',dict(utc=utc(),pid=__import__('os').getpid(),main_effects_read=False))
if __name__=='__main__':
 lock=(R/'logs/translation_batch_gatekeeper20.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while True:
  try:cycle()
  except Exception as e:save(U/'translation_batch_gatekeeper20_error.json',dict(utc=utc(),error=type(e).__name__,reason=str(e)[:300]))
  time.sleep(30)
