from u300_schedule_prepare import *
import sys,shlex
sys.path.insert(0,str(T));from u300_alpha0_cache_scope20 import load_alpha0_cache
O=U/'followup31';ids={L(p)['id'] for p in Path('/tmp/tap88/rows').glob('*.json')};assert len(ids)==78;counts={}
for method in ['PAIR','TAP']:
 W=U/'score_waves'/('search88_'+method+'_qwen');rows=L(W/'inputs.private.json');labs={r['id']:load_alpha0_cache(R,r,H(U/'scoring_schedule_v1.json'))['label'] for r in rows};assert set(ids)<=set(labs);counts[method]=dict(N=78,fulfilled=sum(labs[i]==1 for i in ids),INVALID_IDs=[i for i in ids if labs[i] not in [0,1]],all88_fulfilled=sum(v==1 for v in labs.values()),manifest_sha256=H(W/'manifest.json'))
matches=0
for p in Path('/tmp/tap88/rows').glob('*.json'):
 r=L(p);matches+=int(r['source_logs'][-1]['adv_prompt']==r['selected_prompt'])
out=dict(utc=utc(),old_TAP78_label_object="source_logs[-1]['target_response'] (search-internal final logged candidate, not necessarily selected_prompt)",last_candidate_matches_selected=matches,matched_selected_prompt_replay_2400=counts,no_nonzero_labels_read=True);save(O/'TAP78_matched_sources.json',out);print(json.dumps(out))
code="""from pathlib import Path
import json
R=Path('/home/dell/Def');U=R/'results/audit/unified300';p=json.loads((U/'S1b_TAP_progressive_v1.json').read_text());ref=next(iter(p['progressive']['retained_pilot_rows']['qwen'].values()));d=(R/ref['path']).parent.parent;out=dict(pilot_dir=str(d),files=[x.name for x in d.iterdir()]);
for q in d.glob('*.json'):
 if 'private' in q.name:continue
 z=json.loads(q.read_text())
 if isinstance(z,dict):out[q.name]={k:v for k,v in z.items() if k in ['utc','N','cold_seconds','formal_window_seconds','elapsed_seconds','formal_config','N_saved','GPU_hours','rows'] and k!='rows'}
print(json.dumps(out))"""
try:pilot=json.loads(subprocess.check_output(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(code)],text=True));save(O/'TAP_pilot_metadata.json',pilot);print('TAP_PILOT',json.dumps(pilot))
except subprocess.CalledProcessError:print('TAP pilot metadata lookup failed; no search release')
