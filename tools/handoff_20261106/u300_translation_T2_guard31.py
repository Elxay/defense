"""CPU T1-before-T2 release guard and calendar cutoff; no judge reads."""
from u300_schedule_prepare import *
import datetime as dt,fcntl,time
cutoff=dt.datetime.fromisoformat('2026-11-16T14:59:59+00:00')
def allowed(now,t1,path):return t1 and path
assert allowed(cutoff,True,True) and not allowed(cutoff,False,True)
def cycle():
 now=dt.datetime.now(dt.timezone.utc);t1=L(U/'translation_T1_complete20.json').get('complete',False) if (U/'translation_T1_complete20.json').exists() else False
 binding=L(U/'translation_T2_execution20_admitted.json') if (U/'translation_T2_execution20_admitted.json').exists() else {};valid=bool(binding.get('admitted') and binding.get('supports_boundary_yield') and binding.get('helper_sha256')==H(T/'language300_unicode_routing20.py'))
 save(U/'translation_T2_release20.json',dict(utc=utc(),admitted=allowed(now,t1,valid),T1_complete=t1,accepted_path_bound=valid,cutoff_UTC=cutoff.isoformat(),reason='T1 or final path binding pending' if not(t1 and valid) else 'ready',deadline_passed=now>=cutoff))
 if now>=cutoff:
  save(U/'translation_T2_calendar_cutoff31.json',dict(utc=utc(),deadline_UTC=cutoff.isoformat(),action='alert and record only',job_signals_sent=False,yield_requests_sent=False,uncompleted_cells='unassessed/partial, never zero or safe'))
 return True
if __name__=='__main__':
 lock=(R/'logs/translation_T2_guard20.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while True:
  try:
   if not cycle():break
  except Exception as e:save(U/'translation_T2_guard20_error.json',dict(utc=utc(),error=type(e).__name__,reason=str(e)[:250]))
  time.sleep(30)
