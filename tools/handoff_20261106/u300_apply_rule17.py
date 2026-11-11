from u300_schedule_prepare import *
import os,signal,time
src=T/'u300_score_dispatcher.py';s=src.read_text()
old='return (not used) and backlog>0 and (backlog>=26400 or completed==52800)'
new="return (not used) and backlog>0 and (completed==52800 if str(today)=='2026-11-12' else (backlog>=26400 or completed==52800))"
assert old in s;s=s.replace(old,new).replace('threshold=26400,all_generated_exception=',"threshold=52800 if str(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date())=='2026-11-12' else 26400,all_generated_exception=")
newsrc=T/'u300_score_dispatcher_rule17.py';newsrc.write_text(s)
# Numerical admission checks, independent of labels.
ns={};exec(s.split("if __name__")[0],ns)
a=ns['hb_window_allowed'];dt=datetime.datetime(2026,11,11,16,tzinfo=datetime.timezone.utc)
assert not a({},30000,51040,dt) and a({},30000,52800,dt)
assert not a({'score_HB_x':{'started_utc':dt.isoformat()}},30000,52800,dt)
commit=publish([newsrc,T/'u300_autodan_wallcap_watch.py',Path(__file__)],'Implement rule17 final-English HB gate and owned-worker wallclock cutoff')
state=L(U/'score_dispatch_state.json');pid=state['pid'];cmd=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
assert str(src).encode() in cmd,cmd
os.kill(pid,signal.SIGTERM);time.sleep(1)
with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json');retired=[]
 for t in cat['tasks']:
  if t['id'].startswith('AutoDAN') and t['id']!='AutoDAN_warmup_pilot20_v4':
   t.setdefault('requires',[]).append(dict(path='results/audit/unified300/rule17_autodan_resume_admitted.json',key='admitted',value=True));retired.append(t['id'])
 save(U/'ready_queue_catalog.json',cat)
q=L(U/'ready_queue/state.json')['tasks'];waves=L(U/'score_dispatch_state.json')['waves'];pending=[w for w in waves if w['judge']=='HB' and q.get(w['task_id'],{}).get('state') not in ['done']]
assert not pending,[(w['task_id'],q.get(w['task_id'],{})) for w in pending]
log=(R/'logs/u300_score_dispatcher_rule17.log').open('ab');proc=subprocess.Popen(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(newsrc)],stdout=log,stderr=log,start_new_session=True)
save(U/'rule17_scheduler_implementation.json',dict(utc=utc(),commit=commit,dispatcher_pid=proc.pid,old_dispatcher_pid=pid,blocked_old_Auto_tasks=retired,HB_tests_passed=3,pending_HB_waves=0,doc_sha256=H(R/'docs/300_ADDENDUM17_AUTODAN_WALLCAP_PHASED_READ_AND_MODEL_GATES.md')))
print(json.dumps(L(U/'rule17_scheduler_implementation.json')))
