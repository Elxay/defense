from pathlib import Path
import collections,json
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
P=L(U/'PAIR_alpha0_independent_replay/plan.json');rows=[]
for r in P['rows']:
 model=r['model'];i=r['id'];gp=U/'static_alpha0'/model/'base/generation.private'/f'{i:04d}.json'
 sp=U/'static_alpha0_SORRY/tasks'/model/'base/scores.private'/f'{i:04d}.json'
 assert gp.exists() and sp.exists()
 rows.append(dict(model=model,id=i,generation_sha256=H(gp),SORRY_cache_sha256=H(sp)))
D=U/'direct_vs_PAIR_alpha0_read';D.mkdir(exist_ok=True)
save(D/'01_status.json',dict(utc=utc(),N=20,source_generation_and_score_hashes=rows,
      allowed_scope='Only same-ID direct-request alpha0 versus already-read independent PAIR alpha0'))
commit=publish([Path(__file__),D/'01_status.json'],'Bind same-behavior direct versus PAIR alpha0 diagnostic before cache read')
previous=H(D/'01_status.json');tick=utc()
pair={(r['model'],r['id']):r for r in L(U/'PAIR_alpha0_independent_replay/read_steps/02_alpha0_early_stop_cross_table.json')['details']}
details=[];summary=[]
for model in ['llama','qwen']:
 counter=collections.Counter();direct_yes=pair_yes=0
 for r in rows:
  if r['model']!=model:continue
  i=r['id'];sp=U/'static_alpha0_SORRY/tasks'/model/'base/scores.private'/f'{i:04d}.json'
  assert H(sp)==r['SORRY_cache_sha256'];z=L(sp)
  assert z['signature']['generation_sha256']==r['generation_sha256']
  a=z['label'];b=pair[model,i]['SORRY_fulfilled'];assert a in [0,1,None] and b in [0,1,None]
  direct_yes+=a==1;pair_yes+=b==1
  counter[str(a)+'->'+str(b)]+=1
  details.append(dict(model=model,id=i,direct_SORRY=a,PAIR_SORRY=b,PAIR_internal_early_stop=pair[model,i]['internal_early_stop']))
 summary.append(dict(model=model,N=10,direct_fulfilled=direct_yes,PAIR_fulfilled=pair_yes,
    transitions=dict(counter),descriptive_only=True))
save(D/'02_pairwise_comparison.json',dict(read_started_utc=tick,utc=utc(),previous_sha256=previous,
    rows=details,summary=summary,main_nonzero_effects_read=False,no_search_or_gate_decision_changed=True))
commit=publish([D/'02_pairwise_comparison.json'],'Read same-behavior direct and PAIR alpha0 labels only')
print(json.dumps(dict(commit=commit,utc=L(D/'02_pairwise_comparison.json')['utc'],
                     sha256=H(D/'02_pairwise_comparison.json'),summary=summary,rows=details)))
