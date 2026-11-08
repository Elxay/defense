"""Portable frozen-snapshot classifier/hash/Guard; no effect-report entry."""
import argparse
from pathlib import Path
import os
import sys
import inspect

from prefix_support import ROOT,BASE,PREFIX,RUNTIME,load,save,sha,utc,node,verify_role,verify_code


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['classifier','hash','guard']);p.add_argument('--condition',action='append');a=p.parse_args()
    verify_code();cfg=load(RUNTIME);names=a.condition or cfg['condition_order']
    snapshot=load(BASE/'frozen_prompt_snapshot.json');allrows={r['id']:r for r in load(BASE/'rows.private.json')};rows={x['id']:allrows[x['id']] for x in snapshot['rows']}
    assert all(len(list((BASE/'canonical254/generation.private'/name).glob('*.json')))==len(rows) for name in names)
    import pair500_eval254 as old
    old.ROOT=ROOT;old.OUT=BASE;old.EVAL=BASE/'canonical254';old.CFG=RUNTIME
    config={'conditions':cfg['conditions'],'judge':cfg['models'][node()]['judge'],'guard':cfg['models'][node()].get('guard')}
    physical=os.environ.get('CUDA_VISIBLE_DEVICES','')
    def require_cards(pair=False):
        allowed=('1,2',) if node()=='node01' and pair else ('2,3',) if pair else ('2',)
        assert physical in allowed and os.environ['DEVICE']=='cuda:'+physical.split(',')[0]
        return physical
    old.require_cards=require_cards
    backend='hf_node01' if node()=='node01' else 'hf_innet'
    if a.stage=='guard':
        require_cards();verify_role('guard',full=True);old.guard(config,rows);return
    if a.stage=='classifier':
        require_cards(pair=True);verify_role('judge',full=True)
        original_gate=old.legacy_gate
        def gate(tok,mdl,torch):
            d=BASE/'canonical254/judge_launches'/(utc().replace(':','')+'_'+str(os.getpid()));d.mkdir(parents=True)
            save(d/'started.json',{'utc':utc(),'pid':os.getpid(),'backend':backend,'physical':physical,'conditions':names,'model_manifest_verified':True})
            previous=old.EVAL;old.EVAL=d
            try:original_gate(tok,mdl,torch)
            except Exception as exc:
                save(d/'failed.json',{'utc':utc(),'error_type':type(exc).__name__});raise
            finally:old.EVAL=previous
            save(BASE/'canonical254/judge20_gate.json',load(d/'judge20_gate.json'))
        old.legacy_gate=gate
    else:
        assert os.environ['DEVICE']=='cpu'
        import spacy
        from pair500_score import harmbench_scope
        original_load=spacy.load
        if node()=='node01':
            modelpath=ROOT/'models/spacy/en_core_web_sm/en_core_web_sm-3.8.0'
            spacy.load=lambda name,*args,**kwargs:original_load(str(modelpath) if name=='en_core_web_sm' else name,*args,**kwargs)
    # Change only the backend metadata literal; numerical/template code is frozen.
    scope=dict(old.__dict__);scope['backend_tag']=backend
    original_source=inspect.getsource(old.score)
    assert original_source.count('f"hf_innet_{kind}"')==1
    source=original_source.replace('f"hf_innet_{kind}"','f"{backend_tag}_{kind}"')
    exec(compile(source,'portable_frozen_score','exec'),scope)
    scope['score'](config,rows,names,a.stage)
    save(BASE/'canonical254'/(a.stage+'_complete_'+node()+'.json'),{'utc':utc(),'conditions':names,'n':len(rows),'backend':backend,'no_effect_report':True})


if __name__=='__main__':main()
