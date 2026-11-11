"""Read-only per-cell generation metadata snapshot; never load responses or judge labels."""
from pathlib import Path
import json,datetime,os
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300'
F=['base','deepinception','refusal_suppression','logical_appeal','authority_endorsement','misrepresentation','evidence-based_persuasion','expert_endorsement','prefix_P1','prefix_P2','translate-ta','translate-ml','translate-mr','translate-zh-cn','translate-fr','ascii','caesar','morse','atbash']
out=[]
for model in ['llama','qwen']:
 for family in F:
  for cond in ['alpha0','s3','rand0'if model=='llama'else'61000','s4','rand1'if model=='llama'else'61001','s5']:
   if family.startswith('translate-'):
    base='ready_generated_B4_ml'if model=='llama'and family=='translate-ml'else'ready_generated_B4_ta'if model=='llama'and family=='translate-ta'else'ready_generated'
    d=U/base/model/family/cond
    if model=='qwen'and cond=='alpha0':d=U/'language_alpha0'/model/family
   elif cond=='alpha0':d=U/'static_alpha0'/model/family
   else:d=U/'ready_generated'/model/family/cond
   records=list((d/'generation.private').glob('*.json'))
   ids=[str(int(p.stem))for p in records if p.stem.isdigit()]
   assert len(ids)==len(set(ids)),'duplicate numeric IDs at '+str(d)
   marker=next((p for p in [d/'complete.json',d/'generation_complete.json']if p.exists()),None)
   complete=json.loads(marker.read_text())if marker else{}
   timings=[]
   for p in (d/'metrics').glob('*.json'):
    m=json.loads(p.read_text());timings.append({'rows':m['rows'],'elapsed_seconds':m['elapsed_seconds'],'utc':m['utc']})
   secs=sum(m['elapsed_seconds']for m in timings);rate=complete.get('rows_per_hour',complete.get('effective_rows_per_hour'))
   if rate is None and secs>0:rate=sum(m['rows']for m in timings)/secs*3600
   out.append({'model':model,'family':family,'condition':cond,'N_saved':len(ids),'normal_complete':complete.get('N')==440 and len(ids)==440,'rows_per_hour':rate,'metric_seconds':secs,'metric_N':sum(m['rows']for m in timings),'marker_utc':complete.get('utc'),'directory_relative':str(d.relative_to(R)),'old_B8_excluded':model=='llama'and family in ['translate-ml','translate-ta'],'labels_read':False})
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root':str(R),'rows':out}))
