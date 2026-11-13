from u300_schedule_prepare import *
import sys,shlex,statistics,collections
O=U/'followup34';out=dict(utc=utc(),cards=[])
for site in ['innet','node01']:
 cmd=[sys.executable,str(T/'u300_gpu_project_inventory.py')] if site=='innet' else ['ssh','node01','/data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/u300_gpu_project_inventory.py']
 for r in json.loads(subprocess.check_output(cmd,text=True)):r['site']=site;out['cards'].append(r)
code="""from pathlib import Path
import json,datetime
U=Path('/home/dell/Def/results/audit/unified300');D=Path('/data/ray/hzx_def/results/mistral_calibration32');o={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
for k,p in [('Mistral_live',U/'Mistral_calibration32_lease/live.json'),('norm_guard',U/'followup34/Mistral_norm_and_adjacent_guard.json'),('alpha150_reference',U/'followup34/Mistral_alpha150_reference20/result.json')]:
 if p.exists():o[k]=json.loads(p.read_text())
o['translations']={}
for key in ['qwen_translate-ml_alpha0','qwen_translate-mr_alpha0','qwen_translate-ta_alpha0']:
 D=U/'language_processed33'/key;rs=[json.loads(p.read_text()) for p in (D/'processed.private').glob('*.json')];secs=sum(r.get('elapsed_seconds',0) for r in rs);live=U/'followup34/leases'/key/'live.json';o['translations'][key]={'N':len(rs),'completed_row_seconds':secs,'rows_per_active_hour':len(rs)*3600/secs if secs else None,'live':json.loads(live.read_text()) if live.exists() else None,'complete':(D/'complete.json').exists()}
for g in [0,2]:
 p=U/'language_processed33/gates/node01'/('gpu'+str(g))/'reference20.json'
 if p.exists():o['node_translation_reference_gpu'+str(g)]={k:v for k,v in json.loads(p.read_text()).items() if k!='checks'}
print(json.dumps(o))"""
node=json.loads(subprocess.check_output(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(code)],text=True));out['node']=node
for key in ['Mistral_norm_and_adjacent_guard.json','Mistral_alpha150_reference20/result.json']:
 p=O/key;p.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['scp','node01:/home/dell/Def/results/audit/unified300/followup34/'+key,str(p)],capture_output=True)
g=node.get('norm_guard',{});conds=g.get('conditions',[]);dates=[datetime.datetime.fromisoformat(z['completed_utc']) for z in conds if z['complete']];intervals=[(b-a).total_seconds() for a,b in zip(dates,dates[1:])];out['Mistral_ETA_UTC']=None
if dates and intervals and not g.get('selection_execution_contract_passed'):
 per=statistics.median(intervals[-7:]);out['Mistral_ETA_UTC']=(dates[-1]+datetime.timedelta(seconds=(22-len(dates))*per)).isoformat();out['Mistral_median_last7_condition_seconds']=per
state=L(U/'ready_queue/state.json')['tasks'];out['running_tasks']={k:v for k,v in state.items() if v['state']=='running'}
out['root_languages']={}
for key in ['llama_translate-ml_alpha0','llama_translate-ta_alpha0','llama_translate-mr_alpha0']:
 d=U/'language_processed33'/key;rows=[L(p) for p in (d/'processed.private').glob('*.json')];secs=sum(r.get('elapsed_seconds',0) for r in rows);out['root_languages'][key]=dict(N=len(rows),failures=dict(collections.Counter(r.get('failure_type') for r in rows if r.get('primary_INVALID'))),active_row_seconds=secs,rows_per_active_hour=len(rows)*3600/secs if secs else None,complete=(d/'complete.json').exists())
tail=U/'encoding_ASCII_tail34';out['ASCII_tail_N']=len(list((tail/'generation.private').glob('*.json')));out['ASCII_tail_complete']=(tail/'complete.json').exists()
if (tail/'complete.json').exists():
 z=L(tail/'complete.json');out['ASCII_tail_completed_UTC']=z['utc'];out['ASCII_tail_rows']=[dict(id=L(p)['id'],B=L(p)['batch_size_actual']) for p in sorted((tail/'generation.private').glob('*.json'))];out['ASCII_complete_manifest_sha256']=H(tail/'complete.json')
out['laststream']=L(O/'laststream132_comparison.json');save(O/'snapshot.json',out)
print(json.dumps(dict(utc=out['utc'],cards=out['cards'],Mistral_complete=sum(c['complete'] for c in conds),Mistral_live=node.get('Mistral_live'),Mistral_ETA_UTC=out['Mistral_ETA_UTC'],node_translation=node['translations'],root_languages=out['root_languages'],ASCII_N=out['ASCII_tail_N'],ASCII_complete=out['ASCII_tail_complete'],ASCII_rows=out.get('ASCII_tail_rows'),translation_reference_gpu2=node.get('node_translation_reference_gpu2')),indent=2))
