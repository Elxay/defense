"""Resource-aware generation ETA scenarios. No judge label reads."""
from pathlib import Path
import concurrent.futures,datetime as dt,heapq,json,statistics,subprocess
from u300_schedule_prepare import R,U,T,H,L,utc,save
helper=T/'unified300_generation_metadata_snapshot_v2.py'
subprocess.run(['scp',str(helper),'node01:/home/dell/Def/tools/handoff_20261106/'+helper.name],check=True,capture_output=True)
def collect(site):
 if site=='innet':cmd=['env','DEF_ROOT='+str(R),'/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(helper)]
 else:cmd=['ssh','node01','env DEF_ROOT=/home/dell/Def /data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/'+helper.name]
 return site,json.loads(subprocess.check_output(cmd,text=True))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:sources=dict(p.map(collect,['innet','node01']))
rows=[]
for a,b in zip(sources['innet']['rows'],sources['node01']['rows']):
 assert (a['model'],a['family'],a['condition'])==(b['model'],b['family'],b['condition'])
 node=(a['family'] in ['ascii','caesar','morse','atbash'] or
       (a['model']=='llama' and a['family'].startswith('translate-') and a['family']!='translate-zh-cn'))
 rows.append({**(b if node else a),'site':'node01' if node else 'innet'})
lookup={(r['model'],r['family'],r['condition']):r for r in rows};C=L(U/'ready_queue_catalog.json');S=L(U/'ready_queue/state.json')
tasks={t['id']:t for t in C['tasks']};main={k:t for k,t in tasks.items() if k.startswith('main_')}
now=dt.datetime.now(dt.timezone.utc);JST=dt.timezone(dt.timedelta(hours=9))
hb=L(U/'queue_jobs/score_HB_0001__1/live.json');prev=L(U/'search_gate_followup_status.json')['score_progress']['HB']
seconds=(dt.datetime.fromisoformat(hb['utc'])-dt.datetime.fromisoformat(prev['utc'])).total_seconds()
hn=hb.get('completed_input_rows',hb['total_rows'] if hb['phase']=='complete' else 0)
hb_rate=(hn-prev['completed_input_rows'])*3600/seconds if seconds>0 else None
assert hb_rate and hb_rate>0
hb_remaining=max(0,hb['total_rows']-hn)/hb_rate*3600
# Setup includes real pause/reloads already observed for completed generation tasks.
attempts={};score_seconds_per_row=[]
for p in (U/'queue_jobs').glob('*/exit.json'):
 d=p.parent/'descriptor.json'
 if not d.exists():continue
 desc=L(d);x=L(p);tid=desc['task_id']
 attempts[tid]=attempts.get(tid,0)+x.get('resident_seconds',0)
 if tid.startswith('score_SORRY_') and tid[len('score_SORRY_'):].isdigit() and tid!='score_SORRY_0001' and x['returncode']==0:
  w=U/'score_waves'/tid[len('score_'):]/'manifest.json'
  if w.exists():score_seconds_per_row.append(x['resident_seconds']/L(w)['N'])
setup={};rates={}
for m in ['llama','qwen']:
 vals=[]
 for tid,t in main.items():
  mm,f,c=t['argv'][2:5];r=lookup[mm,f,c]
  if mm==m and r['normal_complete'] and tid in attempts:vals.append(max(0,attempts[tid]-r['metric_seconds']))
 setup[m]=statistics.median(vals) if vals else 30
for r in rows:
 own=r['rows_per_hour']
 if own and r['N_saved']>=16:rate,basis=own,'own measured'
 else:
  peers=[v['rows_per_hour'] for v in rows if v['model']==r['model'] and v['family']==r['family'] and
       v['condition']!='alpha0' and v['condition'].startswith('s')==r['condition'].startswith('s') and v['rows_per_hour'] and v['N_saved']>=16]
  base=lookup[r['model'],r['family'],'alpha0']['rows_per_hour']
  rate,basis=(statistics.median(peers),'same-family/class measured median') if peers else (base,'same-family alpha0 speed scenario')
 r.update(rate_used=rate,rate_basis=basis,eta_scenarios={},status='done' if r['normal_complete'] else 'not_admitted')
static_families={m:set(v) for m,v in L(U/'static_alpha0_inputs.private.json').items()}
completed_English=sum(440 for r in rows if r['family'] in static_families[r['model']] and r['normal_complete'])
allocated=sum(w['N'] for w in L(U/'score_dispatch_state.json')['waves'] if w['judge']=='SORRY')
judge_allowance=max(0,52800-allocated)*statistics.median(score_seconds_per_row) if score_seconds_per_row else 0
paths={f'results/audit/unified300/ready_generated/{m}/{f}/{c}/complete.json':tid for tid,t in main.items() for m,f,c in [t['argv'][2:5]]}
def simulate(name,with_judges):
 done={k for k,t in main.items() if lookup[tuple(t['argv'][2:5])]['normal_complete']}
 pending=[];active=[];occupied={};end={};t_elapsed=0.;reserve_inserted=False;next_window=False
 for tid,t in main.items():
  r=lookup[tuple(t['argv'][2:5])]
  if tid in done:continue
  state=S['tasks'].get(tid,{});r['status']='running' if state.get('state')=='running' else 'failed' if state.get('state')=='failed' else 'pending'
  duration=(440-r['N_saved'])/r['rate_used']*3600 if r['rate_used'] else None
  if duration is None:continue
  if state.get('state')=='running':
   gpu=state['gpus'][0];occupied[gpu]=tid;heapq.heappush(active,(max(duration,30),gpu,tid));end[tid]=max(duration,30)
  elif state.get('state','pending')=='pending':pending.append((t['priority'],tid,duration+setup[r['model']],r['model']))
 for gpu in [2,3]:
  if S['tasks'].get('score_HB_0001',{}).get('state')=='running':
   assert gpu not in occupied;occupied[gpu]='block_HB';heapq.heappush(active,(max(hb_remaining,30),gpu,'block_HB'))
 if with_judges and 0 not in occupied and judge_allowance:
  occupied[0]='block_SORRY_reserve';heapq.heappush(active,(judge_allowance,0,'block_SORRY_reserve'));reserve_inserted=True
 pending.sort()
 def ready(tid):
  for req in main[tid].get('requires',[]):
   dep=paths.get(req['path'])
   if dep:
    if dep not in done:return False
   else:
    p=R/req['path']
    if not p.exists():return False
    if 'key' in req:
     z=L(p)
     for k in req['key'].split('.'):z=z.get(k) if isinstance(z,dict) else None
     if z!=req['value']:return False
  return True
 while pending or active:
  change=True
  while change:
   change=False
   for i,(_,tid,duration,m) in enumerate(pending):
    if not ready(tid):continue
    gpu=next((g for g in C['compatible_innet_slots'][m] if g not in occupied),None)
    if gpu is None:continue
    occupied[gpu]=tid;finish=t_elapsed+max(duration,30);heapq.heappush(active,(finish,gpu,tid));end[tid]=finish
    pending.pop(i);change=True;break
  if not active:break
  t_elapsed,gpu,tid=heapq.heappop(active);occupied.pop(gpu,None)
  if not tid.startswith('block_'):
   done.add(tid)
   if with_judges and gpu==0 and not reserve_inserted and judge_allowance:
    occupied[0]='block_SORRY_reserve';heapq.heappush(active,(t_elapsed+judge_allowance,0,'block_SORRY_reserve'));reserve_inserted=True
  # A second scenario applies the next prospective once/day window at its
  # measured-backlog threshold, shifting eligible running GPU2/3 work.
  finished_rows=completed_English+sum(440-lookup[tuple(main[k]['argv'][2:5])]['N_saved'] for k in done if not lookup[tuple(main[k]['argv'][2:5])]['normal_complete'])
  if with_judges and not next_window and finished_rows-21120>=26400 and (now+dt.timedelta(seconds=t_elapsed)).astimezone(JST).date()>dt.date(2026,11,11):
   backlog=finished_rows-21120;length=backlog/hb_rate*3600+600
   revised=[]
   for at,g,k in active:
    if g in [2,3]:at+=length;end[k]=at if not k.startswith('block_') else end.get(k)
    revised.append((at,g,k))
   active=revised;heapq.heapify(active)
   for g in [2,3]:
    if g not in occupied:occupied[g]='block_next_HB';heapq.heappush(active,(t_elapsed+length,g,'block_next_HB'))
   next_window=True
 for tid,at in end.items():
  if tid in main:lookup[tuple(main[tid]['argv'][2:5])]['eta_scenarios'][name]=(now+dt.timedelta(seconds=at)).isoformat()
 return dict(unfinished_without_ETA=[tid for _,tid,_,_ in pending],next_HB_window_reserved=next_window)
scenarios={'known_window_only':simulate('known_window_only',False),'judge_reserve':simulate('judge_reserve',True)}
for r in rows:
 if r['normal_complete']:r['eta_scenarios']={'known_window_only':r['marker_utc'],'judge_reserve':r['marker_utc']}
 if r['family'] in ['ascii','caesar','morse','atbash'] and not r['normal_complete']:
  r['status']='pending_encoding_gate' if r['condition']=='alpha0' else 'locked_decoder_and_alpha0_gate'
 if r['family'].startswith('translate-') and r['condition']!='alpha0':r['status']='locked_reply_translation_and_alpha0_gate'
orders=L(U/'ready_generation_plan.json')['condition_order'];families=list(dict.fromkeys(r['family'] for r in rows))
result=dict(utc=now.isoformat(),source_utc={k:v['utc'] for k,v in sources.items()},ETA_version=3,
 HB_observed_rate=hb_rate,HB_remaining_seconds=hb_remaining,HB_release_estimate=(now+dt.timedelta(seconds=hb_remaining)).isoformat(),
 future_SORRY_GPU0_allowance_seconds=judge_allowance,incremental_SORRY_seconds_per_row=score_seconds_per_row,
 setup_seconds=setup,scenarios=scenarios,rows=rows,condition_order=orders,
 explanation='A: actual current HB occupancy, dependencies, measured cell rates. B: also prepay estimated remaining SORRY duty on GPU0 and reserve next once/day HB backlog window. Scenario span is not a confidence interval or upper bound. Locked/unmeasured cells have no calendar ETA. Only generation, no judge labels read.')
if (U/'queue_jobs/score_HB_0001__1/exit.json').exists():
 result['HB_actual_release_utc']=L(U/'queue_jobs/score_HB_0001__1/exit.json')['utc']
save(U/'family_condition_status_20261111_v3.json',result)
def fmt(s):return dt.datetime.fromisoformat(s).astimezone(JST).strftime('%m/%d %H:%M')
lines=['# 家族×条件生成表，ETA v3','', 'UTC '+now.isoformat(),'',
 '✓=440且完成标记有效；数字*=正在生成；锁=前置未齐；✓不代表判分已齐。ETA是已知窗口/判分预留两个情景，不是置信区间或保证。', '',
 (f"HB已于{fmt(result['HB_actual_release_utc'])} JST释放；" if 'HB_actual_release_utc' in result else f"HB当前观测行速{hb_rate:.0f}/小时，估计释放{fmt(result['HB_release_estimate'])} JST；")+
 f"未来SORRY GPU0总算力预留{judge_allowance/3600:.2f}小时。",'']
for m in ['llama','qwen']:
 lines += ['## '+m,'','| 家族 | α0 | s3 | r0 | s4 | r1 | s5 | 全六条件生成ETA JST |','|---|---:|---:|---:|---:|---:|---:|---|']
 for f in families:
  group=[lookup[m,f,c] for c in orders[m]]
  cells=['✓' if r['normal_complete'] else str(r['N_saved'])+'*' if r['status']=='running' else '锁' if 'locked' in r['status'] else str(r['N_saved']) for r in group]
  if all(r['normal_complete'] for r in group):eta='已齐'
  elif all(r['eta_scenarios'] for r in group):
   dates=[max(r['eta_scenarios'][k] for r in group) for k in ['known_window_only','judge_reserve']];eta=' ～ '.join(fmt(x) for x in sorted(dates))
  else:eta='待前置/行速'
  lines.append('| '+f+' | '+' | '.join(cells)+' | '+eta+' |')
 lines.append('')
(U/'family_condition_status_20261111_v3.md').write_text('\n'.join(lines).rstrip()+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
