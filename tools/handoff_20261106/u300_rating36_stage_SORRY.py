from u300_schedule_prepare import *
import time
O=U/'followup36'
while not (U/'score_diagnostic36/raw_complete.json').exists():time.sleep(3)
W=U/'score_waves/PAIR_internal_rating_diagnostic36';W.mkdir(parents=True,exist_ok=True)
for n in ['inputs.private.json','manifest.json']:subprocess.run(['scp','node01:/home/dell/Def/results/audit/unified300/score_waves/PAIR_internal_rating_diagnostic36/'+n,str(W/n)],check=True,capture_output=True)
assert H(W/'inputs.private.json')==L(W/'manifest.json')['inputs_sha256'];save(O/'SORRY_internal_wave_staged.json',dict(utc=utc(),ready=True,N=264,manifest_sha256=H(W/'manifest.json'),scope='same saved internal responses; original root SORRY backend'))
