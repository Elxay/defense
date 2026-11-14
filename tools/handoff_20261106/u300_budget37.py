from u300_schedule_prepare import *
import collections,statistics,datetime,shlex
O=U/'followup37';S=L(O/'T2_metadata_snapshot.json');reg=L(U/'T2_processing36_registry.json')['cells'];by={}
old={};bas={}
for snap in S['snapshots']:
 old.update(snap['old_translation']);bas.update(snap['baseline_rates'])
 for r in snap['cells']:by.setdefault(r['cell_id'],{}).update(r)
rates={};prates={}
for c in reg:
 f=c['model']+'_'+c['family'];g=by[c['cell_id']].get('generation',{});v=g.get('seconds_per_row')
 if v and g['measured_rows']>=100:rates[f]=max(rates.get(f,0),v)
 p=by[c['cell_id']].get('processing',{});v=p.get('seconds_per_row')
 if v and p['N']>=100:prates[f]=max(prates.get(f,0),v)
for f,z in bas.items():
 if z.get('seconds_per_row'):rates[f]=max(rates.get(f,0),z['seconds_per_row'])
for k,z in old.items():
 f=k.removesuffix('_alpha0')
 if f in rates:prates[f]=max(prates.get(f,0),z['seconds_per_row'])
cells=[];genlane=collections.defaultdict(float)
for c in reg:
 f=c['model']+'_'+c['family'];z=by[c['cell_id']];g=z['generation'];p=z['processing'];gn=440-g['N'];pn=440-p['N'];gh=gn*rates[f]/3600;ph=pn*prates[f]/3600
 lane=('node01:1' if c['family']=='translate-ml' else 'node01:2') if c['model']=='llama' and c['family'] in ['translate-ml','translate-ta'] else ('innet:0' if c['model']=='llama' or c['family']=='translate-ta' else 'innet:2' if c['family']=='translate-ml' else 'innet:3')
 genlane[lane]+=gh;cells.append(dict(**c,generation_N=g['N'],processing_N=p['N'],generation_seconds_per_row=rates[f],translation_seconds_per_row=prates[f],remaining_generation_GPUh=gh,remaining_translation_GPUh=ph,generation_lane=lane))
loads={k:genlane[k] for k in ['innet:0','innet:2','innet:3','node01:0','node01:1','node01:2']};routes={}
# Never move a cell with any translated output; whole unstarted cells only.
for c in cells:
 if c['processing_N']:
  lane=c['site']+':'+str(c['gpu']);routes[c['cell_id']]=lane;loads[lane]+=c['remaining_translation_GPUh']
pending=sorted([c for c in cells if not c['processing_N']],key=lambda c:(-c['remaining_translation_GPUh'],c['cell_id']))
for c in pending:
 lane=min(loads,key=lambda x:(loads[x],x));routes[c['cell_id']]=lane;loads[lane]+=c['remaining_translation_GPUh']
now=datetime.datetime.now(datetime.timezone.utc);deadline=datetime.datetime(2026,11,16,14,59,59,tzinfo=datetime.timezone.utc);Hleft=(deadline-now).total_seconds()/3600
gen=sum(c['remaining_generation_GPUh'] for c in cells);trans=sum(c['remaining_translation_GPUh'] for c in cells)
# Explicit planning reserve, not a measured statistical upper bound:
# 20% slower rows plus 60 future model/reference loads at 2min and 2h SORRY/loading.
loads_reserve=60*2/60;judge_reserve=2.;point=gen+trans+loads_reserve+judge_reserve;high=(gen+trans)*1.2+loads_reserve+judge_reserve
result=dict(utc=utc(),deadline_UTC=deadline.isoformat(),remaining_wall_hours=Hleft,reserve_wall_hours=12,availability=.60,remaining_generation_GPUh=gen,remaining_translation_GPUh=trans,load_reference_reserve_GPUh=loads_reserve,SORRY_and_judge_loading_reserve_GPUh=judge_reserve,R_point_GPUh=point,R_high_planning_GPUh=high,R_high_is_not_a_statistical_bound=True,high_rule='1.20*(measured-row generation + translation estimate) + explicit loads + judge reserve; estimates not guarantees',lane_point_GPUh=loads,proposed_routes=routes,cells=cells,screen=[dict(cards=n,user_literal_R_over_n=high/n,conservative_R_over_effective_cards=high/(.60*n),budget_condition_pass=high/(.60*n)<Hleft-12) for n in range(1,7)],no_protected_labels_read=True)
save(O/'T2_budget_release37.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ['cells','proposed_routes']},indent=2));print('ROUTES',json.dumps(routes,indent=2))
# Collect only the registered project tasks and hardware processes, no guess by account.
state=L(U/'ready_queue/state.json');cat=L(U/'ready_queue_catalog.json');tasks={t['id']:t for t in cat['tasks']}
print('TRANSLATION_TASK_SAMPLE',json.dumps(tasks['T2translate36_llama_translate-mr_s3'],indent=2))
print('START_HISTORY')
for lang in ['ml','mr','ta']:
 tid=f'T2nonzero36_qwen_translate-{lang}_s3';starts=[]
 for d in sorted((U/'queue_jobs').glob(tid+'__*')):
  x=d/'execution.log'
  if x.exists():starts.extend([v for v in x.read_text(errors='replace').splitlines() if v.startswith('START')][:1])
  else:starts.append((d.name,'descriptor_mtime',datetime.datetime.fromtimestamp((d/'descriptor.json').stat().st_mtime,datetime.timezone.utc).isoformat()))
 print(lang,starts)
