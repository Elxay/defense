"""Resumable output-only Guard for original public/harmful records, no report."""
from pathlib import Path
import argparse,os,sys,time
from lease_priority_support import ROOT,BASE,STATE,load,save,sha,utc,verify,auxiliary_yield

def main():
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=400);a=p.parse_args();verify()
    card=os.environ['DEVICE'].split(':')[1];assert card in ['0','2','3'] and os.environ['CUDA_VISIBLE_DEVICES']==card
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from pair500_generate import official_functions
    from prefix_support import verify_role,RUNTIME
    verify_role('guard',full=True);cfg=load(RUNTIME);root=cfg['models']['innet']['guard'];source=ROOT/'tools/handoff_20261106/guard_qwen_output.py'
    tok=AutoTokenizer.from_pretrained(root,local_files_only=True);mdl=AutoModelForCausalLM.from_pretrained(root,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval();safe,unsafe=[tok.encode(x,add_special_tokens=False) for x in ['safe','unsafe']];assert len(safe)==len(unsafe)==1
    scope=official_functions(source,{'score'});scope.update(tok=tok,mdl=mdl,torch=torch,safe=safe,unsafe=unsafe)
    ref=load(ROOT/'status/guard_output2.json')['alpha0_full'];old=load(ROOT/'results/audit/RERUN_v70_a0.0_b8f62434.json');keys=sorted(load(ROOT/'configs/stage0_data/val70_ids.json')['ids'],key=lambda k:abs(ref[k]-.5))[:20]
    error=max(abs(scope['score'](old[k]['text'])[0]-ref[k]) for k in keys);assert len(keys)==20 and error<.001
    gate=STATE/'guard_windows'/f'{os.getpid()}.json';save(gate,{'utc':utc(),'pid':os.getpid(),'max_abs_delta':error,'n':20,'passed':True,'model_manifest_sha256':sha(BASE/'prefix254_asset_manifest.json'),'source_sha256':sha(source),'card':card})
    started=time.monotonic();done=0;names=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']
    for name in names:
        for kind in ['public','harmful']:
            if kind=='harmful' and name=='alpha0':
                from wjb_eval255_run import baseline_source,baseline_text
                paths=[baseline_source(key) for key in load(BASE/'wjb2000_alpha0_plan.json')['ids']] if (BASE/'wjb2000_alpha0_plan.json').exists() else []
                if not paths:
                    from public_wjb_alpha0_gate import PLAN
                    paths=[baseline_source(key) for key in load(PLAN)['ids']]
            else:paths=sorted((BASE/'public255'/f'{kind}.private'/name).glob('*/*.json'))
            for p in paths:
                record=load(p)
                if kind=='harmful' and name=='alpha0':record={'signature':{'dataset':'wildjailbreak_harmful'},'items':[{'id':p.stem,'text':baseline_text(record)}]}
                for item in record['items']:
                    if done>=a.limit or auxiliary_yield(card,started):return
                    dest=BASE/'public255/output_guard_all'/kind/name/record['signature']['dataset']/(item['id']+'.json');sig={'generation_sha256':sha(p),'item_id':item['id'],'guard_source_sha256':sha(source),'model_manifest_sha256':sha(BASE/'prefix254_asset_manifest.json')}
                    if dest.exists():assert load(dest)['signature']==sig;continue
                    probability,tokens=scope['score'](item['text']);save(dest,{'id':item['id'],'signature':sig,'p_unsafe':probability,'input_tokens':tokens,'method':'frozen_output_only_guard','gate_sha256':sha(gate),'device_uuid':str(torch.cuda.get_device_properties(0).uuid)});done+=1
                    save(STATE/f'guard_live_gpu{card}.json',{'utc':utc(),'pid':os.getpid(),'condition':name,'kind':kind,'new_scores':done,'seconds':time.monotonic()-started,'effects_read':False})

if __name__=='__main__':main()
