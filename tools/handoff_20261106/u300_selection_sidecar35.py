from pathlib import Path
import os,json,hashlib,datetime,time,collections
R=Path(os.environ.get('DEF_ROOT','/home/dell/Def'));U=R/'results/audit/unified300'
L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
def trace(row):
 ss=row['streams'];entries=[dict(flow=j+1,iteration=k+1,score=e['score'],prompt=e['adv_prompt']) for j,s in enumerate(ss) for k,e in enumerate(s)];entries.sort(key=lambda e:(e['iteration'],e['flow']));chosen=None;score=0
 for e in entries:
  if e['score']>score:chosen=e;score=e['score']
 assert chosen is not None and chosen['prompt']==row['selected_prompt']
 clean=lambda e:{k:e[k] for k in ['flow','iteration','score']}
 return dict(index_base=1,selected=clean(chosen),matching_selected_occurrences=[clean(e) for e in entries if e['prompt']==row['selected_prompt']],maximum_score=score,maximum_ties=sum(e['score']==score for e in entries),iteration_scores=[dict(iteration=k,scores=[clean(e) for e in entries if e['iteration']==k]) for k in sorted({e['iteration'] for e in entries})])
while True:
 D=U/'PAIR_progressive/qwen/tier440';O=U/'search_selection_trace35/PAIR_qwen/tier440'
 for p in (D/'rows.private').glob('*.json'):
  out=O/(p.stem+'.json')
  if out.exists():assert L(out)['source_row_sha256']==H(p);continue
  r=L(p)
  if r.get('failure'):z=dict(failure=r['failure'],selected_not_reconstructed=True)
  else:z=trace(r)
  save(out,dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),id=r['id'],source_row_sha256=H(p),source_controller_plan_sha256=r['plan_sha256'],derived_after_atomic_row=True,no_algorithm_change=True,**z))
 save(O/'live.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),PID=os.getpid(),rows=len(list(O.glob('[0-9]*.json'))),GPU_used=False))
 if (D/'complete.json').exists():
  for i,ref in L(D/'complete.json')['selected_rows'].items():
   p=R/ref['path'];assert H(p)==ref['sha256'];out=O/(f'{int(i):04d}.json')
   if not out.exists():save(out,dict(id=int(i),source_row_sha256=H(p),inherited=True,**trace(L(p))))
  save(O/'complete.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),N=440,record_sha256={p.name:H(p) for p in O.glob('[0-9]*.json')}));break
 time.sleep(20)
