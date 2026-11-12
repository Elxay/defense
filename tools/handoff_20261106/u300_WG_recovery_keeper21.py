from u300_schedule_prepare import *
import time,os
def cycle():
 S=L(U/'ready_queue/state.json')['tasks']
 for B in [4,1]:
  tid='WG_R1_uniform21_B'+str(B);st=S.get(tid,{});wave='WG_R1_uniform21_B'+str(B);W=U/'score_waves'/wave
  done=W/'WG_complete.json';gate=W/'WG_gate20.json'
  if done.exists():
   assert L(done)['N_inputs']==52800 and L(gate)['passed']
   save(U/'R1_WG_uniform_admission21.json',dict(utc=utc(),batch=B,coverage=52800,complete_sha256=H(done),reference_gate_sha256=H(gate),plan_sha256=H(U/('WG_uniform_R1_B'+str(B)+'_plan21.json')),main_effect_read_allowed=False));return
  if st.get('state')!='failed':continue
  folder=U/'queue_jobs'/st['job_dir'];log=folder/'worker.log'
  if not log.exists():log=folder/'runner.log'
  text=log.read_text(errors='replace')[-30000:]
  failure=any(k in text for k in ['OutOfMemoryError','CUDA out of memory','WG_MEMORY_HEADROOM_BELOW_3GIB','Fresh 20-reference gate failed'])
  if B==4 and failure:
   with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
    fcntl.flock(lk,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json')
    if not any(t['id']=='WG_R1_uniform21_B1' for t in cat['tasks']):
     task=dict(id='WG_R1_uniform21_B1',priority=8,site='node01',gpus=[2],kind='cache_only_uniform_WG_recovery',yieldable=False,sync_relpath='results/audit/unified300/main_scores_uniform21_B1',argv=['/data/ray/env/bin/python','{ROOT}/tools/handoff_20261106/u300_WG_uniform_recovery21.py','WG','WG_R1_uniform21_B1'],requires=[dict(path='results/audit/unified300/WG_recovery21_publication.json',key='published',value=True)])
     cat['tasks'].append(task);save(U/'ready_queue_catalog.json',cat)
  else:save(U/'WG_recovery21_blocked.json',dict(utc=utc(),batch=B,reason='Unexpected failure or B1 exhausted; no outcome reads'))
 save(U/'WG_recovery21_live.json',dict(utc=utc(),pid=os.getpid(),main_effects_read=False))
lock=(R/'logs/WG_recovery21_keeper.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
while True:
 try:cycle()
 except Exception as e:save(U/'WG_recovery21_error.json',dict(utc=utc(),error=type(e).__name__,reason=str(e)[:300]))
 time.sleep(30)
