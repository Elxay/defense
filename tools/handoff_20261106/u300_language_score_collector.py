"""CPU-only per-completed-language-cell transfer and score admission."""
from pathlib import Path
import fcntl,json,subprocess,time
from u300_schedule_prepare import R,U,T,H,L,utc,save
lock=(R/'logs/u300_language_score_collector.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
P=L(U/'language_preprocess_execution_v1.json')
while True:
 try:
  new=[]
  for c in P['cells']:
   key=c['key'];rel='results/audit/unified300/language_processed_alpha0_v1/'+key
   dest=R/rel
   # Only a published complete marker admits a cell; no partial translation is judged.
   exists=subprocess.run(['ssh','node01','test -f /home/dell/Def/'+rel+'/complete.json']).returncode==0
   if not exists:continue
   dest.mkdir(parents=True,exist_ok=True)
   subprocess.run(['rsync','-a','node01:/home/dell/Def/'+rel+'/',str(dest)+'/'],check=True,capture_output=True)
   meta=L(dest/'complete.json');wave=meta['wave'];W=U/'score_waves'/wave;W.mkdir(parents=True,exist_ok=True)
   subprocess.run(['rsync','-a','node01:/home/dell/Def/results/audit/unified300/score_waves/'+wave+'/',str(W)+'/'],check=True,capture_output=True)
   assert H(W/'manifest.json')==meta['manifest_sha256']
   assert H(W/'inputs.private.json')==L(W/'manifest.json')['inputs_sha256']
   tid='score_'+wave
   new.append(dict(id=tid,priority=7,site='innet',gpus=[0],kind='preprocessed_alpha0_cache_only_scoring',yieldable=False,
      argv=['/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/u300_language_SORRY_cache_v1.py','SORRY',wave],
      requires=[dict(path=str((dest/'complete.json').relative_to(R)))]))
  with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
   fcntl.flock(lk,fcntl.LOCK_EX);C=U/'ready_queue_catalog.json';cat=L(C);known={t['id'] for t in cat['tasks']}
   cat['tasks'] += [t for t in new if t['id'] not in known];save(C,cat)
  save(U/'language_score_collector_live.json',dict(utc=utc(),pid=__import__('os').getpid(),completed_preprocessing_cells=len(new),
       no_labels_read=True))
 except Exception as e:save(U/'language_score_collector_error.json',dict(utc=utc(),error_type=type(e).__name__,reason=str(e)[:300]))
 time.sleep(60)
