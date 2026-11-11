from pathlib import Path
import subprocess,json
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
source=T/'u300_read_pair_alpha0_diagnostic.py';worker=T/'u300_read_tap_alpha0_diagnostic.py'
worker.write_text(source.read_text().replace('PAIR','TAP'))
assert L(U/'score_waves/TAP_alpha0_diagnostic/SORRY_complete.json')['N_inputs']==20
commit=publish([worker,Path(__file__)], 'Pin TAP timing-pilot alpha0 diagnostic reader before authorized label read')
save(U/'TAP_alpha0_independent_replay/read_program_frozen.json',dict(utc=utc(),commit=commit,worker_sha256=H(worker)))
subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(worker)],check=True)
