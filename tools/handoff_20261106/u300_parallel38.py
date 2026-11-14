from u300_schedule_prepare import *
import os,sys,signal
os.environ['GIT_SSH_COMMAND']='ssh -o Hostname=127.0.0.1 -o Port=18443 -o HostKeyAlias=github.com -o StrictHostKeyChecking=yes -o ConnectTimeout=15'
O=U/'followup38';old=T/'u300_T2_watch38.py';s=old.read_text();needle="2. if state.get('Gemma_zero20_window38',{}).get('state')!='done' else 0."
assert needle in s;s=s.replace(needle,"2. if any(state.get(tid,{}).get('state')!='done' for tid in ['Gemma_zero20_window38','replay38_TAP_llama_first88','judge38_TAP_llama_first88']) else 0.");w=T/'u300_T2_watch38b.py';w.write_text(s);compile(s,str(w),'exec')
save(O/'parallel_slot_plan.json',dict(utc=utc(),TAP_llama_first88_gpu=3,after='Gemma_zero20_window38 exit, regardless of its diagnostic pass/fail',numeric_replay_plan_sha256=H(O/'replay_execution.json'),only_unstarted_tasks_moved=True,window_reserve='retain conservative2GPUh on GPU3 until Gemma and Llama first sensitivity plus judge finish; GPU2 retains1.5 until all replays/judges finish',total_engineering_window_reserve_GPUh=3.5,new_watch_sha256=H(w),nonzero_effects_read=False))
commit=publish([O/'parallel_slot_plan.json',w,Path(__file__)],'Reuse bounded engineering slot after Gemma for independent Llama TAP sensitivity without changing numerical paths')
with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json');state=L(U/'ready_queue/state.json')['tasks']
 for tid in ['replay38_TAP_llama_first88','judge38_TAP_llama_first88']:
  assert state.get(tid,{}).get('state','pending')=='pending';t=next(t for t in cat['tasks'] if t['id']==tid);t['gpus']=[3];a=t['argv'];key='results/audit/unified300/followup38/replay_execution.json' if tid.startswith('replay') else 'results/audit/unified300/scoring_schedule_v1.json';a[a.index(key)+1]='3'
  if a[0]=='env':a[1]='DEF_FROZEN_GIT_REV='+commit
  if tid.startswith('replay'):t['requires'].append(dict(path='results/audit/unified300/queue_jobs/Gemma_zero20_window38__1/exit.json'))
 save(U/'ready_queue_catalog.json',cat)
pid=L(U/'followup37/T2_watch/live.json')['pid'];assert b'u300_T2_watch38.py' in (Path('/proc')/str(pid)/'cmdline').read_bytes();os.kill(pid,signal.SIGTERM);log=(O/'T2_watch38b.log').open('a');p=subprocess.Popen([sys.executable,str(w)],stdout=log,stderr=log,start_new_session=True);save(O/'parallel_slot_execution.json',dict(utc=utc(),commit=commit,old_CPU_watch_pid=pid,new_CPU_watch_pid=p.pid,watch_sha256=H(w),GPU_workers_killed=False));print(json.dumps(L(O/'parallel_slot_execution.json')))
