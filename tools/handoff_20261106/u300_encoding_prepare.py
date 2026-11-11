"""Encoding alpha0 generation admission, independent of response decoders."""
from pathlib import Path
import copy,datetime,hashlib,json,subprocess
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish

source=T/'unified300_prepare_static_alpha0.py'
head=source.read_text().split("p=U/'static_alpha0_inputs.private.json'")[0]
head=head.replace('p.read_text().splitlines()]', "p.read_text().split('\\n') if x.strip()]")
start=head.index('families=[');end=head.index(';base=',start)
head=head[:start]+"families=['ascii','caesar','morse','atbash']"+head[end:]
ns={};exec(compile(head,'encoding_render_same_frozen_templates','exec'),ns)
private=ns['private'];models=ns['models'];families=ns['families']
ip=U/'encoding_alpha0_inputs.private.json';assert not ip.exists();save(ip,private)
parent=L(U/'ready_generation_plan.json');plan=copy.deepcopy(parent)
plan.update(utc_frozen=utc(),family_order=families,condition_order={m:['alpha0'] for m in ['llama','qwen']},
            scope='encoded alpha0 generation only; decoder gates required before scoring or nonzero',
            numerical_parent_sha256=H(U/'ready_generation_plan.json'))
for model in ['llama','qwen']:
    spec=plan['models'][model];spec['families']={}
    for family in families:
        cfg=copy.deepcopy(models[model]['families'][family])
        cfg.update(home_site='node01',input_file=ip.name,input_sha256=H(ip),
                   output_root='encoding_alpha0_generated',SORRY_gate='locked_until_decoder')
        spec['families'][family]=cfg
worker=T/'unified300_encoding_alpha0_v1.py';assert not worker.exists()
code=(T/'unified300_ready_generate_v3.py').read_text().replace('ready_worker_operational_binding_v3.json','encoding_alpha0_binding_v1.json')
worker.write_text(code);compile(code,str(worker),'exec')
pp=U/'encoding_alpha0_plan_v1.json';save(pp,plan)
binding=U/'encoding_alpha0_binding_v1.json'
save(binding,dict(utc=utc(),worker_sha256=H(worker),allowed_numerical_plan_sha256=[H(pp)],
    source_worker_sha256=H(T/'unified300_ready_generate_v3.py'),change='Only binding name; numerical functions unchanged'))
receipt=U/'encoding_alpha0_publication.json'
commit=publish([Path(__file__),worker,pp,binding,T/'u300_score_dispatcher.py'],
               'Admit encoded alpha0 generation separately from decoder and publish score dispatcher')
save(receipt,dict(utc=utc(),published=True,commit=commit,plan_sha256=H(pp)))
C=U/'ready_queue_catalog.json';cat=L(C)
rels=[str(p.relative_to(R)) for p in [worker,pp,binding,ip,receipt]]
for rel in rels:
    if rel not in cat['node_deploy_files']:cat['node_deploy_files'].append(rel)
for model in ['llama','qwen']:
    for fi,family in enumerate(families):
        root='results/audit/unified300';gate=f'{root}/ready_family_gates/node01/{model}/{family}/zero20.json'
        for mode in ['gate','generate']:
            tid=f'encoding_{model}_{family}_{mode}_v1'
            assert not any(t['id']==tid for t in cat['tasks'])
            req=[dict(path=str(receipt.relative_to(R)),key='published',value=True)]
            if mode=='generate':req.append(dict(path=gate,key='passed',value=True))
            args=['/usr/bin/env','DEF_GENERATION_PLAN_RELATIVE='+str(pp.relative_to(R)),
                  '/data/ray/env/bin/python','{ROOT}/tools/handoff_20261106/unified300_encoding_alpha0_v1.py',
                  model,family,'alpha0',mode,'2']
            # kind intentionally separate: worker physical card is fixed, no argv-index
            # assumptions from the existing language task remapper.
            cat['tasks'].append(dict(id=tid,priority=70+fi,site='node01',gpus=[2],
                kind='encoding_alpha0_'+mode,argv=args,requires=req,yieldable=mode=='generate',
                sync_relpath=f'{root}/encoding_alpha0_generated/{model}/{family}/alpha0' if mode=='generate'
                  else f'{root}/ready_family_gates/node01/{model}/{family}'))
save(C,cat)
print(json.dumps(dict(utc=utc(),encoding_plan_sha256=H(pp),commit=commit,tasks_added=16,
                      generation_outputs_before_admission=0,decoding_and_nonzero_still_locked=True)))
