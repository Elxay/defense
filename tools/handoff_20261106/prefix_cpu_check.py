"""CPU-only adapter checks using benign synthetic text and temporary fixtures."""
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))


def main():
    import spacy
    import numpy as np
    from pair500_score import harmbench_scope
    if str(ROOT)!='/data/HZX/Def':
        original=spacy.load
        spacy.load=lambda name,*a,**k:original(str(ROOT/'models/spacy/en_core_web_sm/en_core_web_sm-3.8.0') if name=='en_core_web_sm' else name,*a,**k)
    scope=harmbench_scope(ROOT/'repos/HarmBench/eval_utils.py','hash')
    samples=[]
    for i in range(20):
        text=('A garden notebook records sunshine, rain, soil, and the seasons. '+
              "The reader's café opens at 8:30; its blue door is beside the library. ")*(i+1)
        fingerprints=[]
        for window,overlap in [(300,200),(50,40)]:
            values=scope['compute_hashes_with_sliding_window'](text,window,overlap)
            fingerprints.append([hashlib.sha256(v.hashvalues.astype('<u8').tobytes()).hexdigest() for v in values])
        samples.append({'id':i,'tokens_sha256':hashlib.sha256(json.dumps(scope['tokenize'](text),ensure_ascii=False).encode()).hexdigest(),'minhash':fingerprints})
    import prefix_support as support
    import prefix_controller as controller
    import prefix_compare_gate as compare
    from unittest.mock import patch
    temporary_checks=[]
    with tempfile.TemporaryDirectory() as directory:
        base=Path(directory);runtime=base/'runtime.json';runtime.write_text('{}')
        cfg={'core_sha256':'fixture'};item={'id':'benign_fixture','prompt_sha256':'fixture_prompt','row_sha256':'fixture_row'}
        with patch.object(support,'RUNTIME',runtime):
            sig=support.signature('alpha0',item,cfg)
            record=base/'row.json';support.save(record,{'id':item['id'],'signature':sig,'result':{'injection_count':1}})
            support.verify_record(record,'alpha0',item,cfg);temporary_checks.append('valid_signature_accepted')
            bad=dict(item,prompt_sha256='changed')
            try:support.verify_record(record,'alpha0',bad,cfg)
            except AssertionError:temporary_checks.append('changed_prompt_rejected')
            else:raise AssertionError('changed prompt accepted')
        source=(ROOT/'tools/handoff_20261106/pair500_eval254.py').read_text()
        assert source.count('method = f"hf_innet_{kind}"')==1
        temporary_checks.append('backend_metadata_replacement_unique')
        for name in ['prefix_support.py','prefix_generate.py','prefix_controller.py','prefix_evaluate.py','prefix_compare_gate.py']:
            ast.parse((ROOT/'tools/handoff_20261106'/name).read_text())
        temporary_checks.append('all_adapter_sources_parse')
        cfgpath=base/'gate_runtime.json';support.save(cfgpath,{'core_sha256':'fixture'})
        prefix=base/'prefix';items=[];references={}
        with patch.object(support,'RUNTIME',cfgpath),patch.object(compare,'RUNTIME',cfgpath),patch.object(compare,'PREFIX',prefix):
            for i in range(20):
                item={'id':str(i),'prompt_sha256':'fixture','row_sha256':'fixture'};items.append(item)
                value={'id':item['id'],'signature':support.signature('alpha0',item,{'core_sha256':'fixture'}),'result':{'injection_count':1,'text':'A garden.','input_ids_sha256':'fixture'}}
                ref=prefix/'generation.private/alpha0'/f'{i}.json';support.save(ref,value)
                support.save(prefix/'node_gate_generated/alpha0'/f'{i}.json',value);references[str(i)]=support.sha(ref)
            task=base/'task.json';support.save(task,{'condition':'alpha0','items':items,'reference_sha256':references})
            with patch.object(sys,'argv',['prefix_compare_gate.py','--task',str(task)]):compare.main()
            assert support.load(prefix/'node_gate_results/alpha0.json')['passed'];temporary_checks.append('node_gate_20_identical_passed')
            altered=prefix/'node_gate_generated/alpha0/0.json';value=support.load(altered);value['result']['text']='Different.';support.save(altered,value)
            with patch.object(sys,'argv',['prefix_compare_gate.py','--task',str(task)]):
                try:compare.main()
                except SystemExit as exc:assert exc.code==75;temporary_checks.append('node_gate_one_difference_stopped')
                else:raise AssertionError('node gate accepted a byte difference')
    print(json.dumps({'n_benign_fixtures':20,'samples':samples,'temporary_checks':temporary_checks,
        'versions':{p:importlib.metadata.version(p) for p in ['numpy','spacy','thinc','datasketch','typer','pydantic']}},ensure_ascii=False))


if __name__=='__main__':main()
