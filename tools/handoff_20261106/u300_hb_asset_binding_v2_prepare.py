from pathlib import Path
import copy,json
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
S=L(U/'ready_queue/state.json')['tasks'];assert S.get('score_HB_0001',{}).get('state')!='running'
old=T/'u300_hb_cache_worker_v1.py'
code=old.read_text().replace('HB_scoring_schedule_v1.json','HB_scoring_schedule_v2.json')
oldline="    A=L(R/'results/audit/pair500/hb_judge_model_sha256.json'); mp=Path(A['model_root'])"
newline="    asset_manifest=R/'results/audit/pair500/hb_judge_model_sha256.json'\n    assert H(asset_manifest)==P['HB_model_manifest_sha256']\n    A=L(asset_manifest); mp=Path(A['model_root'])"
assert oldline in code;code=code.replace(oldline,newline)
code=code.replace("sigbase=dict(worker_sha256=H(__file__),", "sigbase=dict(model_asset_manifest_sha256=H(asset_manifest),worker_sha256=H(__file__),")
worker=T/'u300_hb_cache_worker_v2.py';worker.write_text(code);compile(code,str(worker),'exec')
p=copy.deepcopy(L(U/'HB_scoring_schedule_v1.json'));p.update(utc_frozen=utc(),worker_sha256=H(worker),
 HB_model_manifest_sha256=L(U/'human_reference_plan.json')['HB_model_manifest_sha256'],
 change='Preflight binding only: require the already frozen S0 model manifest hash and serialize it. Numerical classifier/chunk methods unchanged; main HB scores still zero.')
pp=U/'HB_scoring_schedule_v2.json';save(pp,p)
assert H(R/'results/audit/pair500/hb_judge_model_sha256.json')==p['HB_model_manifest_sha256']
commit=publish([worker,pp,Path(__file__)], 'Tighten pre-launch HB asset manifest binding without changing classification')
receipt=U/'HB_scoring_asset_binding_v2_publication.json';save(receipt,dict(utc=utc(),published=True,commit=commit))
cat=L(U/'ready_queue_catalog.json')
for t in cat['tasks']:
 if t['id']=='score_HB_0001':
  t['argv'][1]='{ROOT}/tools/handoff_20261106/u300_hb_cache_worker_v2.py'
  t['requires'].append(dict(path=str(receipt.relative_to(R)),key='published',value=True))
save(U/'ready_queue_catalog.json',cat)
print(json.dumps(dict(commit=commit,HB_plan_sha256=H(pp),main_HB_scores_before_binding=0)))
