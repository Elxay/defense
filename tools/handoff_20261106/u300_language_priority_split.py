from pathlib import Path
import copy,json
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
source=T/'u300_language_preprocess_worker.py';code=source.read_text().replace('language_preprocess_execution_v1.json','language_preprocess_execution_v2.json')
code=code.replace("for cell in P['cells']:","group=sys.argv[1];assert group in ['CF','India']\ncells=[c for c in P['cells'] if (c['family'] in ['translate-zh-cn','translate-fr'])==(group=='CF')]\nfor cell in cells:")
code=code.replace("D/'all_complete.json'","D/('complete_'+group+'.json')").replace("len(P['cells'])","len(cells)")
worker=T/'u300_language_preprocess_worker_v2.py';worker.write_text(code);compile(code,str(worker),'exec')
p=copy.deepcopy(L(U/'language_preprocess_execution_v1.json'));p.update(utc_frozen=utc(),worker_sha256=H(worker),
    source_worker_sha256=H(source),change='Scheduling split only: CF before encoding; India after encoding. Same input rows/helper/numerical path.')
pp=U/'language_preprocess_execution_v2.json';save(pp,p)
commit=publish([worker,pp,Path(__file__)], 'Split Chinese/French reply processing ahead of encoding and Indian-language queue')
receipt=U/'language_preprocess_priority_publication.json';save(receipt,dict(utc=utc(),published=True,commit=commit))
C=U/'ready_queue_catalog.json';cat=L(C);S=L(U/'ready_queue/state.json')['tasks'];oldid='language_alpha0_reply_preprocessing_v1'
assert S.get(oldid,{}).get('state')!='running'
old=next(t for t in cat['tasks'] if t['id']==oldid)
cat.setdefault('retired_prelaunch_tasks',[]).append(dict(utc=utc(),task=old,reason='Split priorities before any reply processing output'))
cat['tasks']=[t for t in cat['tasks'] if t['id']!=oldid]
for group,priority in [('CF',13),('India',90)]:
 t=copy.deepcopy(old);t.update(id='language_alpha0_reply_preprocessing_v2_'+group,priority=priority)
 t['argv'][-1]='{ROOT}/tools/handoff_20261106/u300_language_preprocess_worker_v2.py';t['argv'].append(group)
 t['requires']=[dict(path=str(receipt.relative_to(R)),key='published',value=True)];cat['tasks'].append(t)
for t in cat['tasks']:
 if t.get('kind')=='alpha0_family_generate' and 'translate-' in t['id'] and not any(k in t['id'] for k in ['translate-fr','translate-zh-cn']):
  if S.get(t['id'],{}).get('state')!='running':t['priority']=200
for p in [worker,pp,receipt]:
 rel=str(p.relative_to(R))
 if rel not in cat['node_deploy_files']:cat['node_deploy_files'].append(rel)
save(C,cat)
print(json.dumps(dict(commit=commit,plan_sha256=H(pp),order='English scoring, Chinese/French, encoding, Indian languages')))
