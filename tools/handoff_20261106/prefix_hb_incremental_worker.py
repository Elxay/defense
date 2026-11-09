"""Bounded same-backend prefix classifier cache, with a fresh numerical gate."""
from pathlib import Path
import argparse,hashlib,inspect,json,os,sys,time
from lease_priority_support import ROOT,BASE,STATE,load,save,sha,utc,verify

class WindowYield(Exception):pass

def cache_signature(generation_sha,row_sha):
    return {'prefix_generation_sha256':generation_sha,'row_sha256':row_sha,'classifier_source_sha256':sha(ROOT/'tools/handoff_20261106/pair500_eval254.py'),'eval_utils_sha256':sha(ROOT/'repos/HarmBench/eval_utils.py'),'model_asset_manifest_sha256':sha(BASE/'prefix254_asset_manifest.json'),'runtime_sha256':sha(BASE/'prefix254_runtime.json')}

def main():
    p=argparse.ArgumentParser();p.add_argument('--task',required=True);a=p.parse_args();verify();assert os.environ['CUDA_VISIBLE_DEVICES']=='2,3' and os.environ['DEVICE']=='cuda:2'
    sys.path.insert(0,str(ROOT/'src'))
    from prefix_support import verify_role,objsha
    from pair500_score import harmbench_scope,clip
    import pair500_eval254 as old
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    task=load(a.task);cfg=load(BASE/'prefix254_runtime.json');rows={r['id']:r for r in load(BASE/'rows.private.json')};window=STATE/'hb_windows'/str(os.getpid());window.mkdir(parents=True)
    save(window/'started.json',{'utc':utc(),'pid':os.getpid(),'task_sha256':sha(a.task),'physical':'2,3','stage':'verifying_model_files','effects_read':False})
    verify_role('judge',full=True);tokenizer=AutoTokenizer.from_pretrained(cfg['models']['innet']['judge'],local_files_only=True);mdl=AutoModelForCausalLM.from_pretrained(cfg['models']['innet']['judge'],torch_dtype=torch.bfloat16,device_map='auto',max_memory={0:'13GiB',1:'13GiB','cpu':'0GiB'},local_files_only=True).eval();assert not {'cpu','disk'}&set(mdl.hf_device_map.values())
    old.EVAL=window;old.legacy_gate(tokenizer,mdl,torch);gate=window/'judge20_gate.json';assert load(gate)['passed'];save(window/'ready.json',{'utc':utc(),'gate_sha256':sha(gate),'model_manifest_sha256':sha(BASE/'prefix254_asset_manifest.json'),'fresh_model_hash_check':True,'reference20_passed':True})
    clock=time.monotonic();done=0
    def check_yield():
        if time.monotonic()-clock>=1200 or (STATE/'hb_yield.json').exists():raise WindowYield()
    scope=harmbench_scope(ROOT/'repos/HarmBench/eval_utils.py','classifier')
    try:
        for item in task['items']:
            check_yield();name=item['condition'];key=item['id'];row=rows[key];assert row['layer']!='copyright' and objsha(row)==item['row_sha256'];p=BASE/'prefix254/generation.private'/name/(key+'.json');assert sha(p)==item['generation_sha256'];g=load(p);assert g['signature']['row_sha256']==item['row_sha256']
            sig=cache_signature(item['generation_sha256'],item['row_sha256']);dest=BASE/'prefix254/hb_pre_scores'/name/(key+'.json')
            if dest.exists():assert load(dest)['signature']==sig;continue
            generation=clip(tokenizer,g['result']['text'],512);kind='prompt_contextual' if row['context'] else 'prompt';prompt=scope['LLAMA2_CLS_PROMPT'][kind].format(behavior=row['behavior'],context=row['context'],generation=generation);tokens=tokenizer(prompt,return_tensors='pt').to(mdl.device)
            if tokens.input_ids.shape[1]>mdl.config.max_position_embeddings:raise RuntimeError('Classifier template overflow: '+key)
            with torch.inference_mode():output=mdl.generate(**tokens,max_new_tokens=1,do_sample=False,pad_token_id=tokenizer.eos_token_id)
            label={'yes':1,'no':0}.get(tokenizer.decode(output[0,-1:],skip_special_tokens=True).strip().lower())
            from judge.refusal import new_rule
            save(dest,{'id':key,'signature':sig,'label':label,'method':'hf_innet_'+kind,'v2_refusal':new_rule(g['result']['text']),'incremental_window_gate_sha256':sha(gate),'incremental_task_sha256':sha(a.task),'original_inference_utc':utc()});done+=1
            if done%10==0:save(STATE/'hb_live.json',{'utc':utc(),'pid':os.getpid(),'stage':'PAIR_prefix_cache','new_rows':done,'seconds':time.monotonic()-clock,'effects_read':False})
        # Reuse residency for the already-frozen top2 sensitivity, after PAIR cache.
        import wjb_top2_shared_window as top2
        source=inspect.getsource(top2.score);needle="            text=json.loads(p.read_text())['items'][0]['text'];behavior=";assert needle in source
        source=source.replace(needle,"            check_yield()\n"+needle)
        namespace=dict(top2.__dict__);namespace['check_yield']=check_yield;exec(compile(source,'incremental_top2_scheduling_wrapper','exec'),namespace);namespace['score'](tokenizer,mdl,torch,'hf_innet')
        # Auxiliary top1 uses the exact original standard template and logits score.
        import csv
        mapping_path=BASE/'wjb_mapping255.json';mapping=load(mapping_path);refpath=ROOT/'repos/HarmBench/data/behavior_datasets/harmbench_behaviors_text_all.csv';assert sha(refpath)==mapping['hb_sha256']
        with refpath.open()as f:refs={r['BehaviorID']:r['Behavior'] for r in csv.DictReader(f)}
        yes_ids=tokenizer.encode('Yes',add_special_tokens=False);no_ids=tokenizer.encode('No',add_special_tokens=False);assert len(yes_ids)==len(no_ids)==1
        for name in ['old_s0','SYS_A','SYS_B']:
            for row in mapping['rows']:
                check_yield();key=row['id'];p=BASE/'public255/harmful.private'/name/'wildjailbreak_harmful'/(key+'.json')
                if not p.exists():continue
                sig={'generation_sha256':sha(p),'mapping_sha256':sha(mapping_path)};dest=BASE/'public255/mapped_scores'/name/(key+'.json')
                if dest.exists():assert load(dest)['signature']==sig;continue
                behavior_id=row['candidates'][0]['behavior_id'];text=load(p)['items'][0]['text'];prompt=scope['LLAMA2_CLS_PROMPT']['prompt'].format(behavior=refs[behavior_id],generation=clip(tokenizer,text,512));tokens=tokenizer(prompt,return_tensors='pt').to(mdl.device)
                with torch.inference_mode():output=mdl.generate(**tokens,max_new_tokens=1,do_sample=False,pad_token_id=tokenizer.eos_token_id,return_dict_in_generate=True,output_logits=True)
                label={"yes":1,"no":0}.get(tokenizer.decode(output.sequences[0,-1:],skip_special_tokens=True).strip().lower());pair_logits=output.logits[0][0,[yes_ids[0],no_ids[0]]].float();p_yes=float(torch.softmax(pair_logits,dim=-1)[0])
                save(dest,{'id':key,'signature':sig,'label':label,'p_yes':p_yes,'behavior_id':behavior_id,'method':'hf_innet_standard','probability_definition':'raw_Yes_No_pair_normalized','window_gate_sha256':sha(gate)})
    except WindowYield:pass
    save(window/'completed.json',{'utc':utc(),'pid':os.getpid(),'PAIR_new_rows':done,'scoring_seconds':time.monotonic()-clock,'bounded_window':True,'effects_read':False})
    save(STATE/'hb_last_completed.json',{'utc':utc(),'window':str(window.relative_to(ROOT)),'PAIR_new_rows':done,'task_sha256':sha(a.task),'effects_read':False})

if __name__=='__main__':main()
