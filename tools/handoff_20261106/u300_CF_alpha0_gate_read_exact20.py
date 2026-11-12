from u300_schedule_prepare import *
import collections
from u300_alpha0_cache_scope20 import load_alpha0_cache
cells=[]
for model in ['llama','qwen']:
 for family in ['translate-zh-cn','translate-fr']:
  wave='language_alpha0_'+model+'_'+family;W=U/'score_waves'/wave
  assert L(W/'SORRY_complete.json')['N_inputs']==440
  assert H(W/'inputs.private.json')==L(W/'manifest.json')['inputs_sha256']
  cells.append((model,family,W,L(W/'inputs.private.json')))
status=U/'CF_alpha0_gate_status_exact20.json';save(status,dict(utc=utc(),N_cells=4,N_rows=1760,source_manifests={w.name:H(w/'manifest.json') for _,_,w,_ in cells},judge_complete={w.name:H(w/'SORRY_complete.json') for _,_,w,_ in cells},scope='SORRY alpha0 original B1 gate only; no other judges or nonzero'))
found={(r['generation_sha256'],r['preprocessing_sha256']):load_alpha0_cache(R,r,H(U/'language_scoring_schedule_v1.json')) for m,f,w,rows in cells for r in rows}
assert len(found)==1760
out=[]
for m,f,w,rows in cells:
 scores=[found[r['generation_sha256'],r['preprocessing_sha256']] for r in rows];yes=sum(z.get('label')==1 for z in scores);invalid=[z['id'] for z in scores if z.get('label') not in [0,1]];lo=yes/440;hi=(yes+len(invalid))/440
 out.append(dict(model=m,family=f,N=440,fulfillment=yes,INVALID_IDs=invalid,rate_bounds=[lo,hi],gate='no_dynamic_range' if hi<.25 else 'active' if lo>=.25 else 'INVALID_crossing_continue',passing_count=110))
p=U/'CF_alpha0_gate_read_exact20.json';save(p,dict(utc=utc(),read_status_sha256=H(status),original_B1_path_preserved=True,rows=out,no_nonzero_effects_read=True))
commit=publish([status,p],'Read only completed original-B1 Chinese/French alpha0 dynamic-range gates with full denominators')
print(json.dumps(dict(commit=commit,sha256=H(p),rows=out)))
