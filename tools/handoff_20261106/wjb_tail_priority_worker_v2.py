"""Run the original WJB generator with cooperative preemption and observed metadata."""
from pathlib import Path
import argparse,hashlib,json,os,sys,time
from lease_priority_support import ROOT,BASE,STATE,load,save,sha,utc,verify,auxiliary_yield

def main():
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['harmful','public']);p.add_argument('condition',choices=['old_s0','SYS_A','SYS_B']);p.add_argument('--shard',type=int,choices=[0,1],required=True);a=p.parse_args()
    verify();assert sha(Path(__file__))==load(BASE/"lease_priority_v2_publication.json")["tail_wrapper_sha256"];card=os.environ['DEVICE'].split(':')[1];assert card in ['0','2','3'] and os.environ['CUDA_VISIBLE_DEVICES']==card
    sys.path.insert(0,str(ROOT/'src'))
    import wjb_eval255_run as original
    config=load(original.CFG);spec=config['conditions'][a.condition]
    started=time.monotonic();original.snapshot_preempts=lambda *_:auxiliary_yield(card,started)
    original.require_cards=lambda pair=False: (_ for _ in ()).throw(AssertionError('single-card generator')) if pair else card
    prompts=original.public_rows() if a.kind=='public' else {'wildjailbreak_harmful':list(original.harmful_rows(load(original.PLAN)).items())}
    prompts={d:dict(v) for d,v in prompts.items()}
    import torch,numpy as np,transformers
    captured={};factory=transformers.AutoModelForCausalLM.from_pretrained
    def observe_model(*args,**kwargs):
        model=factory(*args,**kwargs);generate=model.generate
        def observe(*args,**kwargs):
            output=generate(*args,**kwargs)
            ids=kwargs.get('input_ids',args[0] if args else None);mask=kwargs.get('attention_mask')
            captured.update(ids=ids.detach().cpu(),mask=mask.detach().cpu() if mask is not None else None,output=output.detach().cpu(),eos=model.generation_config.eos_token_id,max_new_tokens=kwargs['max_new_tokens'])
            return output
        model.generate=observe;return model
    transformers.AutoModelForCausalLM.from_pretrained=observe_model
    writer=original.write;writes=0
    def observed_write(path,record):
        nonlocal writes
        if f'{a.kind}.private' in str(path) and 'items' in record:
            rows=[];eos=captured['eos'];eos=set(eos if isinstance(eos,list) else [eos]);prompt_len=captured['ids'].shape[1]
            for i,item in enumerate(record['items']):
                tokens=captured['output'][i,prompt_len:].tolist();stop=next((j for j,t in enumerate(tokens) if t in eos),None)
                input_ids=captured['ids'][i]
                if captured['mask'] is not None:input_ids=input_ids[captured['mask'][i].bool()]
                prompt=prompts[record['signature']['dataset']][item['id']]
                hardware={'id':item['id'],'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'input_ids_sha256':hashlib.sha256(input_ids.numpy().astype('<i8').tobytes()).hexdigest(),'device_uuid':str(torch.cuda.get_device_properties(0).uuid),'physical_device':os.environ['DEVICE'],'condition':a.condition,'vector_sha256':spec.get('file_sha256')}
                item.update(hardware,new_tokens=(stop+1 if stop is not None else len(tokens)),eos_hit_generation_config=stop is not None,hit_max_new_tokens=stop is None and len(tokens)==captured['max_new_tokens'])
                raw=record.get('generation',{});hook_count=raw.get('injection_count',item.get('prefill_hook_count'));rho=raw.get('rho_runtime',item.get('rho_runtime'));assert hook_count==1
                item.update(prefill_hook_count=hook_count,nonzero_vector_injection_count=(hook_count if spec.get('vector') else 0),rho_runtime=rho,eos=stop is not None)
                if a.condition in ['SYS_A','SYS_B']:assert rho==0.0 and item['nonzero_vector_injection_count']==0
                if a.condition in ['SYS_A','SYS_B']:
                    from prefix_support import render_audit
                    # Tokenizer construction is CPU-only; compare actual inputs, not labels.
                    tok=transformers.AutoTokenizer.from_pretrained(original.LLAMA,local_files_only=True);ids,audit=render_audit(tok,prompt,a.condition,spec['system_prompt']);assert audit['input_ids_sha256']==hardware['input_ids_sha256'];item.update(audit)
                item['execution_signature']=hardware;item['execution_signature_sha256']=hashlib.sha256(json.dumps(hardware,sort_keys=True,separators=(',',':')).encode()).hexdigest();rows.append(item['id'])
            record['execution_observation']={'source_generator_sha256':sha(Path(original.__file__)),'wrapper_sha256':sha(Path(__file__)),'physical_card':card,'ids':rows,'recorded_after_unchanged_generate_return':True};writes+=len(rows)
        writer(path,record)
        if f'{a.kind}.private' in str(path):save(STATE/f'tail_live_gpu{card}.json',{'utc':utc(),'pid':os.getpid(),'kind':a.kind,'condition':a.condition,'shard':a.shard,'new_rows':writes,'wall_seconds':time.monotonic()-started,'effects_read':False})
    original.write=observed_write
    save(STATE/f'tail_start_gpu{card}.json',{'utc':utc(),'pid':os.getpid(),'kind':a.kind,'condition':a.condition,'shard':a.shard,'card':card})
    original.generate(a.kind,a.condition,a.shard,config)
    save(STATE/f'tail_done_gpu{card}_{os.getpid()}.json',{'utc':utc(),'pid':os.getpid(),'kind':a.kind,'condition':a.condition,'shard':a.shard,'new_rows':writes,'elapsed_seconds':time.monotonic()-started,'yielded':auxiliary_yield(card,started),'effects_read':False})

if __name__=='__main__':main()
