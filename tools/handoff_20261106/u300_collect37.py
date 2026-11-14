from u300_schedule_prepare import *
import shlex,statistics,sys
O=U/'followup37'
reg=L(U/'T2_processing36_registry.json')['cells']
code='''from pathlib import Path
import json,statistics,datetime
R=Path(ROOT);U=R/'results/audit/unified300';reg=REG
def L(p):return json.loads(p.read_text())
def gen(folder):
 files=list((folder/'generation.private').glob('*.json'));mets=[L(p) for p in (folder/'metrics').glob('*.json')];sec=sum(x.get('elapsed_seconds',0) for x in mets);n=sum(x.get('rows',0) for x in mets)
 return dict(N=len(files),complete=(folder/'complete.json').exists(),measured_rows=n,seconds=sec,seconds_per_row=sec/n if n else None)
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'site':SITE,'cells':[],'baseline_rates':{},'old_translation':{}}
for r in reg:
 gs='node01' if r['model']=='llama' and r['family'] in ['translate-ml','translate-ta'] else 'innet'
 row={'cell_id':r['cell_id']}
 if gs==SITE:
  folder=U/r['generation_root'];row['generation']=gen(folder);out['baseline_rates'][r['model']+'_'+r['family']]=gen(folder.parent/'alpha0')
 if r['site']==SITE:
  folder=U/'language_processed36'/r['cell_id'];files=list((folder/'processed.private').glob('*.json'));vals=[L(p) for p in files];sec=sum(x.get('elapsed_seconds',0) for x in vals)
  row['processing']=dict(N=len(files),complete=(folder/'complete.json').exists(),seconds=sec,seconds_per_row=sec/len(files) if files else None)
 if len(row)>1:out['cells'].append(row)
for folder in (U/'language_processed33').glob('*'):
 if not folder.is_dir():continue
 files=list((folder/'processed.private').glob('*.json'))
 if not files:files=list(folder.glob('*.json'))
 vals=[L(p) for p in files if p.name not in ['complete.json','manifest.json']];vals=[x for x in vals if 'elapsed_seconds' in x]
 if vals:out['old_translation'][folder.name]={'N':len(vals),'seconds':sum(x['elapsed_seconds'] for x in vals),'seconds_per_row':statistics.mean(x['elapsed_seconds'] for x in vals)}
print(json.dumps(out))
'''
snapshots=[]
for site,root,py in [('innet',str(R),sys.executable),('node01','/home/dell/Def','/data/ray/env/bin/python')]:
 c=code.replace('ROOT',repr(root)).replace('REG',repr(reg)).replace('SITE',repr(site))
 if site=='innet':
  p=O/'metadata_probe.private.py';p.write_text(c);z=json.loads(subprocess.check_output([py,str(p)],text=True))
 else:z=json.loads(subprocess.check_output(['ssh','node01',py+' -c '+shlex.quote(c)],text=True))
 snapshots.append(z)
save(O/'T2_metadata_snapshot.json',dict(utc=utc(),snapshots=snapshots,no_protected_labels_read=True))
for z in snapshots:print(json.dumps(z,indent=2))
# Exact requested alpha0 judge repetition only: no protected effects.
P=U/'selfrepeat37_plan.json';rows=L(U/'score_waves/last_internal_repeat37_r1/inputs.private.json');runs=[]
for run in [1,2]:
 folder=U/'selfrepeat37'/f'last_internal_repeat37_r{run}'/'SORRY'/'records.private';out=[]
 for r in rows:
  fields={k:r[k] for k in ['generation_sha256','prompt_sha256','response_sha256','behavior_sha256']};fields.update(preprocessing_sha256=r.get('preprocessing_sha256'),judge='SORRY',schedule_sha256=H(P));key=hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest();z=L(folder/(key+'.json'));out.append(z)
 runs.append(out)
print('JUDGE_RECORD_KEYS',list(runs[0][0]))
old={int(x['id']):x['SORRY_same_internal'] for x in L(U/'followup36/rating264_results.json')['rows'] if x['kind']=='last'}
result=dict(utc=utc(),N=132,run_summaries=[],input_same=True,changed_ids=[],output_changed_ids=[])
for i,vals in enumerate(runs,1):
 labels=[z.get('label') for z in vals];result['run_summaries'].append(dict(run=i,fulfilled=sum(x==1 for x in labels),unfulfilled=sum(x==0 for x in labels),invalid=sum(x not in [0,1] for x in labels),changed_vs_previous264=[int(str(r['id']).split(':')[0]) for r,z in zip(rows,vals) if z.get('label')!=old[int(str(r['id']).split(':')[0])]]))
for r,a,b in zip(rows,*runs):
 if a.get('label')!=b.get('label'):result['changed_ids'].append(r['id'])
 if a.get('output')!=b.get('output'):result['output_changed_ids'].append(r['id'])
result['fresh_complete_UTC']=[L(U/'selfrepeat37'/f'last_internal_repeat37_r{i}'/'complete.json')['utc'] for i in [1,2]];result['repeat_plan_sha256']=H(P)
save(O/'judge_selfrepeat_results.json',result);print('REPEAT_RESULT',json.dumps(result))
