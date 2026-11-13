from u300_schedule_prepare import *
import time,os,shlex
O=U/'takeover30';deadline=datetime.datetime.fromisoformat('2026-11-16T14:59:59+00:00');checkpoint=datetime.datetime.fromisoformat('2026-11-15T09:00:00+00:00')
def cycle():
 now=datetime.datetime.now(datetime.timezone.utc);admitted=now<deadline
 save(O/'Indian_schedule_admission.json',dict(utc=utc(),admitted=admitted,deadline_UTC=deadline.isoformat(),does_not_override_translation_or_SORRY_gates=True))
 if now>=checkpoint and not (O/'checkpoint_20261115.json').exists():
  p=O/'language_status_checkpoint_20261115.json';run=subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(T/'u300_language_status30.py'),str(R),str(O/'language_cell_registry.json'),str(p)],capture_output=True,text=True)
  save(O/'checkpoint_20261115.json',dict(utc=utc(),exit_code=run.returncode,status_sha256=H(p) if p.exists() else None,scheduled_UTC=checkpoint.isoformat(),no_effect_reads=True))
 if not admitted:
  state=L(U/'ready_queue/state.json')['tasks'];cat=L(U/'ready_queue_catalog.json');defs={t['id']:t for t in cat['tasks']}
  for tid,s in state.items():
   argv=defs.get(tid,{}).get('argv',[])
   if s.get('state')!='running' or not any(x in argv for x in ['translate-ml','translate-ta','translate-mr']):continue
   # Only request batch-boundary yield from a registered project worker.
   if s['site']=='innet':save(U/'queue_jobs'/s['job_dir']/'yield.request',dict(utc=utc(),reason='Frozen Indian-language cutoff'))
   else:
    code="from pathlib import Path;import json;p=Path('/home/dell/Def/results/audit/unified300/queue_jobs/"+s['job_dir']+"/yield.request');p.write_text(json.dumps(dict(reason='Frozen Indian-language cutoff')))";subprocess.run(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(code)],check=True,capture_output=True)
  if not (O/'deadline_snapshot.json').exists():
   p=O/'language_status_deadline.json';run=subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(T/'u300_language_status30.py'),str(R),str(O/'language_cell_registry.json'),str(p)],capture_output=True,text=True)
   save(O/'deadline_snapshot.json',dict(utc=utc(),status_sha256=H(p) if p.exists() else None,exit_code=run.returncode,unfinished_cells_are_unassessed=True))
 save(O/'checkpoint_guard_live.json',dict(utc=utc(),pid=os.getpid(),schedule_admitted=admitted,no_effect_reads=True))
lock=(R/'logs/registered_checkpoint30.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
while True:
 try:cycle()
 except Exception as e:save(O/'checkpoint_guard_error.json',dict(utc=utc(),error=type(e).__name__,reason=str(e)[:250]))
 time.sleep(30)
