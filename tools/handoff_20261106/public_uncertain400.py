"""Replay the same public batch compositions at120 and400 tokens; retain old labels."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import os
import sys
import time

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'public_followup_20261109'
sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
from borrowed_gpu_support import verify_extension,gpu0_must_yield
from pair500_generate import load,write,official_functions,digest
from wjb_eval255_run import CFG,EVAL,LLAMA,public_rows,vector_for,observed_public_batch

def main():
    verify_extension();assert os.environ['DEVICE']=='cuda:0' and os.environ['CUDA_VISIBLE_DEVICES']=='0';assert load(BASE/'gpu0_zero20_result.json')['passed']
    plan=load(OUT/'uncertain400_plan.json');assert digest(Path(__file__))==plan['worker_sha256']
    selection=load(BASE/'public_read_20261109/08_recall_group6.json');selected=[r for r in selection['coded_rows'] if r['category']=='U'];assert len(selected)==5
    assert [r['review_index'] for r in selected]==plan['review_indices']
    import numpy as np,torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    tok=AutoTokenizer.from_pretrained(LLAMA,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
    model=AutoModelForCausalLM.from_pretrained(LLAMA,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval()
    source=ROOT/'src/eval/legal_val_batch.py';tree=ast.parse(source.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_batch')
    run120=official_functions(source,{'run_batch'});run120.update(tok=tok,mdl=model,DEV='cuda:0',LAYER=9,torch=torch)
    node400=__import__('copy').deepcopy(node);changed=0
    for n in ast.walk(node400):
        if isinstance(n,ast.keyword) and n.arg=='max_new_tokens':assert isinstance(n.value,ast.Constant) and n.value.value==120;n.value=ast.Constant(400);changed+=1
    assert changed==1;ast.fix_missing_locations(node400);run400={};exec(compile(ast.Module(body=[node400],type_ignores=[]),str(source),'exec'),run400);run400.update(tok=tok,mdl=model,DEV='cuda:0',LAYER=9,torch=torch)
    sources=public_rows();cfg=load(CFG);summary=[];cache={};started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for sample in selected:
        if gpu0_must_yield():raise SystemExit(75)
        condition=sample['condition'];dataset=sample['dataset'];key=sample['original_id'];pairs=sources[dataset];offset=next(i for i,(k,_) in enumerate(pairs) if k==key);start=offset//8*8;batch=pairs[start:start+8];first=batch[0][0]
        original=EVAL/'public.private'/condition/dataset/(first+'.json');old=load(original);assert [r['id'] for r in old['items']]==[k for k,_ in batch]
        group=(condition,first)
        if group not in cache:
            vector=vector_for(cfg['conditions'][condition]);run120['vec']=vector;run400['vec']=vector;args=[(i,dataset,p) for i,(_,p) in enumerate(batch)]
            start_timer=time.monotonic();text120,norm120=observed_public_batch(run120,args);text400,norm400=observed_public_batch(run400,args)
            assert all(abs(x-5.21)<.01 for x in norm120+norm400)
            cache[group]=(dict(zip([k for k,_ in batch],text120)),dict(zip([k for k,_ in batch],text400)))
            write(OUT/'uncertain400.private'/f'{condition}_{first}.json',{'signature':{'original_batch_sha256':digest(original),'config_sha256':digest(CFG),'hook_sha256':digest(source),'only_max_new_tokens_changed':True,'physical_device':'cuda:0','device_uuid':str(torch.cuda.get_device_properties(0).uuid)},'batch_ids':[k for k,_ in batch],'at120':cache[group][0],'at400':cache[group][1],'seconds':time.monotonic()-start_timer})
        a,b=cache[group];original_text=next(r['text'] for r in old['items'] if r['id']==key)
        private={'review_index':sample['review_index'],'condition':condition,'original_id':key,'task':dict(pairs)[key],'stored120':original_text,'replay120':a[key],'replay400':b[key]}
        write(OUT/'uncertain400_rows.private'/f'{sample["review_index"]}.json',private)
        summary.append({'review_index':sample['review_index'],'condition':condition,'original_id':key,'original_batch_sha256':digest(original),'stored120_vs_replay120_byte_equal':original_text.encode()==a[key].encode(),'replay400_starts_with_replay120':b[key].startswith(a[key]),'replay400_starts_with_stored120':b[key].startswith(original_text),'stored120_sha256':hashlib.sha256(original_text.encode()).hexdigest(),'replay120_sha256':hashlib.sha256(a[key].encode()).hexdigest(),'replay400_sha256':hashlib.sha256(b[key].encode()).hexdigest(),'400_retokenized_length':len(tok.encode(b[key],add_special_tokens=False))})
        write(OUT/'uncertain400_live.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'done':len(summary),'total':5})
    result={'started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':summary,'original120_labels_unchanged':True,'physical_gpu':'cuda:0','scope':'same original batch8 composition; fresh120 replay checks physical-card reproducibility;400 is posthoc follow-up, not replacement of frozen120-token guard'}
    write(OUT/'uncertain400_generation_check.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
