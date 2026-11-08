"""Extra exclusive classifier window; reuse the existing scorer without regeneration."""
import ast
import inspect
import os
import sys
import time

import wjb_eval255_run as base

NAMES=['old_s3','rand0','old_s4','rand1']
PLAN=base.ROOT/'docs/255_ADDENDUM11_FOUR_CONDITION_ANALYSIS.md'
EXPECTED='8128efd0504f62649b6e0f85471331580f45120d27bcdbc9da11f5129e93625f'


def top2(config):
    # The official existing scorer is retained verbatim except that this pass
    # selects top2 alone. Source hashes document this adapter and its dependency.
    tree=ast.parse(inspect.getsource(base.score))
    replaced=0
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='kinds' for x in node.targets):
            node.value=ast.Tuple(elts=[ast.Constant('top2')],ctx=ast.Load());replaced+=1
    assert replaced==1
    scope=dict(vars(base));exec(compile(ast.fix_missing_locations(tree),__file__,'exec'),scope)
    scope['score'](NAMES,config,sensitivity=True)


def guard(config):
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    base.require_cards(pair=True)
    tok=AutoTokenizer.from_pretrained(config['guard'],local_files_only=True)
    mdl=AutoModelForCausalLM.from_pretrained(config['guard'],torch_dtype=torch.bfloat16,
        device_map={'':'cuda:0'},local_files_only=True).eval()
    safe,unsafe=[tok.encode(label,add_special_tokens=False) for label in ('safe','unsafe')]
    assert len(safe)==len(unsafe)==1
    source=base.ROOT/'tools/handoff_20261106/guard_qwen_output.py'
    assert base.digest(source)==base.load(base.PLAN)['guard_source_sha256']
    fn=base.official_functions(source,{'score'});fn.update(tok=tok,mdl=mdl,torch=torch,safe=safe,unsafe=unsafe)
    ref=base.load(base.ROOT/'status/guard_output2.json')['alpha0_full']
    old=base.load(base.ROOT/'results/audit/RERUN_v70_a0.0_b8f62434.json')
    keys=sorted(base.load(base.ROOT/'configs/stage0_data/val70_ids.json')['ids'],key=lambda k:abs(ref[k]-.5))[:20]
    delta=max(abs(fn['score'](old[k]['text'])[0]-ref[k]) for k in keys)
    assert len(keys)==20 and delta<.001
    base.write(base.EVAL/'four_guard20_gate.json',{'n':20,'max_abs_delta':delta,'passed':True})
    rows=base.load(base.OUT/'wjb_mapping255.json')['rows']
    for name in NAMES:
        start=time.monotonic()
        for i,row in enumerate(rows,1):
            if base.SNAPSHOT.exists():return
            p=base.EVAL/'harmful.private'/name/'wildjailbreak_harmful'/(row['id']+'.json')
            dest=base.EVAL/'harmful_guard_scores'/name/p.name
            signature={'generation_sha256':base.digest(p),'guard_source_sha256':base.digest(source)}
            if dest.exists():base.signed(dest,signature);continue
            probability=fn['score'](base.load(p)['items'][0]['text'])[0]
            base.write(dest,{'id':row['id'],'signature':signature,'p_unsafe':probability,'input':'output_text_only'})
            if i%10==0:base.pulse('four_guard',i,2000,start,name)


if __name__=='__main__':
    os.umask(0o077)
    sys.path.insert(0,str(base.ROOT/'src'))
    assert base.digest(PLAN)==EXPECTED
    config=base.load(base.CFG)
    if sys.argv[1]=='top2':top2(config)
    elif sys.argv[1]=='guard':guard(config)
    else:raise SystemExit('Choose top2 or guard')
