"""CPU T1-before-T2 release guard and calendar cutoff; no judge reads."""
from u300_schedule_prepare import *
import datetime as dt,fcntl,time
cutoff=dt.datetime.fromisoformat('2026-11-16T14:59:59+00:00')
def allowed(now,t1,path):return now<cutoff and t1 and path
assert not allowed(cutoff,True,True) and not allowed(cutoff-dt.timedelta(seconds=1),False,True) and allowed(cutoff-dt.timedelta(seconds=1),True,True)
def cycle():
 now=dt.datetime.now(dt.timezone.utc);t1=L(U/'translation_T1_complete20.json').get('complete',False) if (U/'translation_T1_complete20.json').exists() else False
 binding=L(U/'translation_T2_execution20_admitted.json') if (U/'translation_T2_execution20_admitted.json').exists() else {};valid=bool(binding.get('admitted') and binding.get('supports_boundary_yield') and binding.get('helper_sha256')==H(T/'language300_unicode_routing20.py'))
 save(U/'translation_T2_release20.json',dict(utc=utc(),admitted=allowed(now,t1,valid),T1_complete=t1,accepted_path_bound=valid,cutoff_UTC=cutoff.isoformat(),reason='calendar cutoff' if now>=cutoff else 'T1 or final path binding pending' if not(t1 and valid) else 'ready'))
 if now>=cutoff:
  S=L(U/'ready_queue/state.json')['tasks'];asked=[]
  for tid in set(binding.get('task_ids',[])+['language_alpha0_reply_preprocessing_v2_India']):
   task=S.get(tid,{})
   if task.get('state')!='running':continue
   rel='results/audit/unified300/queue_jobs/'+task['job_dir']+'/yield.request'
   if task['site']=='innet':(R/rel).touch()
   else:subprocess.run(['ssh','node01','touch /home/dell/Def/'+rel],check=True,capture_output=True)
   asked.append(tid)
  save(U/'translation_T2_calendar_cutoff20.json',dict(utc=utc(),deadline_UTC=cutoff.isoformat(),boundary_yield_requested=asked,uncompleted_cells='unassessed/partial, never zero or safe',pending_release_closed=True,planned_model_language_condition_cells=36,no_outcomes_read=True))
  return False
 return True
if __name__=='__main__':
 lock=(R/'logs/translation_T2_guard20.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while True:
  try:
   if not cycle():break
  except Exception as e:save(U/'translation_T2_guard20_error.json',dict(utc=utc(),error=type(e).__name__,reason=str(e)[:250]))
  time.sleep(30)
