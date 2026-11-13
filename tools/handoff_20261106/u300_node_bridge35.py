from u300_schedule_prepare import *
import time,shlex
O=U/'followup35';keys=['qwen_translate-'+l+'_alpha0' for l in ['ml','mr']];done=set()
while len(done)<2:
 for key in keys:
  if key in done:continue
  remote='/home/dell/Def/results/audit/unified300/language_processed33/'+key
  test=subprocess.run(['ssh','node01','test -f '+remote+'/complete.json'],capture_output=True)
  if test.returncode:continue
  D=U/'language_processed33'/key;D.mkdir(parents=True,exist_ok=True);subprocess.run(['scp','-r','node01:'+remote+'/.',str(D)],check=True,capture_output=True)
  c=L(D/'complete.json');assert len(c['row_sha256'])==440;assert all(H(D/'processed.private'/n)==h for n,h in c['row_sha256'].items())
  W=U/'score_waves'/('language33_'+key);W.mkdir(parents=True,exist_ok=True)
  for n in ['inputs.private.json','manifest.json']:subprocess.run(['scp','node01:/home/dell/Def/results/audit/unified300/score_waves/'+W.name+'/'+n,str(W/n)],check=True,capture_output=True)
  assert H(W/'inputs.private.json')==L(W/'manifest.json')['inputs_sha256'];done.add(key);save(O/'node_translation_sync.json',dict(utc=utc(),completed=sorted(done),wave_hashes={k:H(U/'score_waves'/('language33_'+k)/'manifest.json') for k in done}))
 time.sleep(30)
