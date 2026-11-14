"""Metadata-only T2 reserve watcher; never reads protected judge labels."""
from u300_schedule_prepare import *
import ast,shlex,sys,time,collections,os
O=U/'followup37';W=O/'T2_watch';W.mkdir(exist_ok=True)
tree=ast.parse((T/'u300_collect37.py').read_text());code=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
reg=L(U/'T2_processing37_registry.json')['cells'];frozen=L(O/'T2_budget_release37.json');prior={r['cell_id']:r for r in frozen['cells']};deadline=datetime.datetime(2026,11,16,14,59,59,tzinfo=datetime.timezone.utc)
def snapshot():
 snaps=[]
 for site,root,py in [('innet',str(R),sys.executable),('node01','/home/dell/Def','/data/ray/env/bin/python')]:
  c=code.replace('ROOT',repr(root)).replace('REG',repr(reg)).replace('SITE',repr(site));args=[py,'-c',c] if site=='innet' else ['ssh','node01',py+' -c '+shlex.quote(c)];snaps.append(json.loads(subprocess.check_output(args,text=True,timeout=120)))
 by={}
 for s in snaps:
  for c in s['cells']:by.setdefault(c['cell_id'],{}).update(c)
 state=L(U/'ready_queue/state.json')['tasks'];loads={x:0. for x in ['innet:0','innet:2','innet:3','node01:0','node01:1','node01:2']};g=p=0.;pendingloads=0;unscored=0
 for c in reg:
  z=by[c['cell_id']];base=prior[c['cell_id']];gv=z['generation'];pv=z['processing'];gr=max(base['generation_seconds_per_row'],gv.get('seconds_per_row') or 0);pr=max(base['translation_seconds_per_row'],pv.get('seconds_per_row') or 0)
  gh=(440-gv['N'])*gr/3600;ph=(440-pv['N'])*pr/3600;g+=gh;p+=ph;loads[base['generation_lane']]+=gh;loads[c['site']+':'+str(c['gpu'])]+=ph;pendingloads+=(gv['N']<440)+(pv['N']<440);unscored+=state.get('T2SORRY36_'+c['cell_id'],{}).get('state')!='done'
 reserve=pendingloads*2/60;judge=unscored/30*2;Rpoint=g+p+reserve+judge;Rhigh=(g+p)*1.2+reserve+judge;Hleft=(deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()/3600
 highloads={k:v*1.2+reserve/6+(judge if k=='innet:2' else 0) for k,v in loads.items()};allmax=max(highloads.values())/.6
 # A naturally completed T2 lane can be released without moving any pending/partial cell.
 empty=[k for k,v in loads.items() if v<1e-9 and k!='innet:2'];eligible=[]
 for lane in empty:
  retained={k:v for k,v in highloads.items() if k!=lane};passed=Rhigh/(.6*5)<Hleft-12 and max(retained.values())/.6<Hleft-12
  if passed:eligible.append(lane)
 result=dict(utc=utc(),pid=os.getpid(),R_point_GPUh=Rpoint,R_high_planning_GPUh=Rhigh,remaining_wall_hours=Hleft,lane_point_GPUh=loads,lane_high_planning_GPUh=highloads,max_lane_high_hours_at_60pct=allmax,empty_T2_lanes=empty,eligible_natural_release_lanes=eligible,deadline_pass_without_twelve_hour_reserve=Rhigh/(.6*6)<Hleft,no_nonzero_labels_read=True,natural_complete_only=True)
 for lane in eligible:
  receipt=O/('T2_RELEASE_'+lane.replace(':','')+'.json')
  if not receipt.exists():save(receipt,dict(utc=utc(),admitted=True,lane=lane,reason='whole lane T2 generation/translation complete, conservative five-card budget and critical lane both satisfy twelve-hour reserve',snapshot_sha256=H(W/'live.json') if (W/'live.json').exists() else None))
 save(W/'live.json',result)
 with (W/'history.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
 return result
if __name__=='__main__':
 while True:
  try:print(json.dumps(snapshot()),flush=True)
  except Exception as e:save(W/'error.json',dict(utc=utc(),error_type=type(e).__name__,reason=str(e)[:500],action='no release on probe failure'));print(type(e).__name__,str(e)[:500],flush=True)
  if '--once' in sys.argv:break
  time.sleep(900)
