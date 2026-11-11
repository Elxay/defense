from pathlib import Path
import copy,json
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
parent=U/'language_preprocessing_plan.json';base=L(U/'language_alpha0_inputs.private.json')
matrix=L(U/'family_condition_status_20261111.json')['rows'];data={};cells=[]
order=['translate-zh-cn','translate-fr','translate-ta','translate-ml','translate-mr']
for family in order:
 for model in ['llama','qwen']:
  r=next(x for x in matrix if x['model']==model and x['family']==family and x['condition']=='alpha0')
  if not r['normal_complete']:continue
  folder=R/r['directory_relative'];marker=next(p for p in [folder/'complete.json',folder/'generation_complete.json'] if p.exists())
  meta=L(marker);assert meta['N']==440
  source={str(z['id']):z for z in base[model][family]};key=model+'_'+family;rows=[]
  for k in sorted(source,key=int):
   z=source[k];p=folder/'generation.private'/f'{int(k):04d}.json';g=L(p);gh=H(p)
   assert gh==meta['record_sha256'][k] and g['prompt_sha256']==z['prompt_sha256']
   rows.append(dict(id=int(k),model=model,family=family,condition='alpha0',prompt=z['prompt'],behavior=z['behavior'],
    response=z['prefill']+g['result']['text'],generation_sha256=gh,prompt_sha256=z['prompt_sha256'],
    behavior_sha256=z['behavior_sha256'],response_sha256=g['full_response_sha256']))
  data[key]=rows;cells.append(dict(key=key,model=model,family=family,N=440))
ip=U/'language_preprocess_inputs.private.json';assert not ip.exists();save(ip,data)
worker=T/'u300_language_preprocess_worker.py';pp=U/'language_preprocess_execution_v1.json'
save(pp,dict(utc_frozen=utc(),worker_sha256=H(worker),helper_sha256=H(T/'language300_local_translation.py'),
 parent_plan_sha256=H(parent),inputs_sha256=H(ip),cells=cells,batch_size=1,source_only_alpha0=True,
 first_cells='Chinese, French, then existing Indian alpha0; missing Tamil waits valid generation',
 new_main_labels_or_effect_reads_allowed=False))
source=T/'u300_score_cache_worker.py';code=source.read_text().replace('scoring_schedule_v1.json','language_scoring_schedule_v1.json')
old="""    if pending:
        for r,p,z in zip(pending,paths,classify(pending)):
            save(p,dict(id=r['id'],model=r['model'],family=r['family'],condition=r['condition'],
                        generation_sha256=r['generation_sha256'],prompt_sha256=r['prompt_sha256'],
                        response_sha256=r['response_sha256'],signature=sigbase,**z))"""
new="""    if pending:
        valid=[r for r in pending if not r.get('primary_preprocessing_INVALID')]
        scored=iter(classify(valid))
        for r,p in zip(pending,paths):
            z=(dict(label=None,output='',input_tokens=None,invalid_reason='preprocessing_INVALID')
               if r.get('primary_preprocessing_INVALID') else next(scored))
            save(p,dict(id=r['id'],model=r['model'],family=r['family'],condition=r['condition'],
                        generation_sha256=r['generation_sha256'],prompt_sha256=r['prompt_sha256'],
                        response_sha256=r['response_sha256'],preprocessing_sha256=r['preprocessing_sha256'],signature=sigbase,**z))"""
assert old in code;code=code.replace(old,new)
sw=T/'u300_language_SORRY_cache_v1.py';sw.write_text(code);compile(code,str(sw),'exec')
sp=U/'language_scoring_schedule_v1.json';s=copy.deepcopy(L(U/'scoring_schedule_v1.json'));s.update(utc_frozen=utc(),worker_sha256=H(sw),preprocessing_plan_sha256=H(parent));save(sp,s)
commit=publish([worker,pp,sw,sp,Path(__file__)], 'Bind frozen alpha0 response-translation queue and invalid-preserving SORRY cache adapter')
receipt=U/'language_preprocess_publication.json';save(receipt,dict(utc=utc(),published=True,commit=commit))
C=U/'ready_queue_catalog.json';cat=L(C)
for p in [worker,pp,ip,parent,receipt,T/'language300_local_translation.py',U/'translator_Qwen3_asset_manifest.json']:
 rel=str(p.relative_to(R))
 if rel not in cat['node_deploy_files']:cat['node_deploy_files'].append(rel)
cat['tasks'].append(dict(id='language_alpha0_reply_preprocessing_v1',priority=13,site='node01',gpus=[2],
 kind='alpha0_reply_preprocessing',yieldable=True,sync_relpath='results/audit/unified300/language_processed_alpha0_v1',
 argv=['/data/ray/env/bin/python','{ROOT}/tools/handoff_20261106/u300_language_preprocess_worker.py'],
 requires=[dict(path=str(receipt.relative_to(R)),key='published',value=True)]))
# Keep this fixed physical card lower priority than the WG cache backlog; it
# cooperatively yields at reply boundaries, never interrupts a search target.
save(C,cat)
print(json.dumps(dict(commit=commit,plan_sha256=H(pp),cells=len(cells),rows=sum(len(v) for v in data.values()),
 missing_cells=10-len(cells),scheduled_card='node01 GPU2',scores_read=False)))
