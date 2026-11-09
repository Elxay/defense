"""CPU render/hash audit and operational per-shard timing; no judge outcomes."""
from pathlib import Path
import datetime,hashlib,json,os,sys
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';S=B/'lease_priority';O=B/'argument_revision_20261109';sys.path.insert(0,str(R/'tools/handoff_20261106'));os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['HF_HUB_OFFLINE']='1';os.environ['USE_TF']='0';os.environ['USE_FLAX']='0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
    from transformers import AutoTokenizer
    import numpy as np
    import wjb_eval255_run as original
    from prefix_support import system_texts
    tok=AutoTokenizer.from_pretrained(original.LLAMA,local_files_only=True);texts=system_texts();old=B/'llama_system_render_audit.json';index={(x['id'],x['condition']):x for x in load(old)['records']};prompts=original.harmful_rows(load(original.PLAN));checked=0;segment_hashes={};header_hashes=set();exact_prefix_matches=0;header_keys=set()
    start='<|start_header_id|>system<|end_header_id|>\n\n';user_marker='<|start_header_id|>user<|end_header_id|>\n\n'
    for key,prompt in prompts.items():
        base=tok.apply_chat_template([{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True);base_segment=base.split(start,1)[1].split('<|eot_id|>',1)[0]
        for name,system in texts.items():
            messages=[{'role':'system','content':system},{'role':'user','content':prompt}];rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True);segment=rendered.split(start,1)[1].split('<|eot_id|>',1)[0];assert segment.endswith(system);header=segment[:-len(system)];assert header.rstrip()==base_segment.rstrip();assert rendered.split(user_marker,1)[1]==base.split(user_marker,1)[1]
            if header==base_segment:exact_prefix_matches+=1
            for k in ['Cutting Knowledge Date:','Today Date:']:
                if k in header:header_keys.add(k)
            header_hashes.add(hashlib.sha256(header.encode()).hexdigest());segment_hashes.setdefault(name,set()).add(hashlib.sha256(segment.encode()).hexdigest());ids=tok.apply_chat_template(messages,add_generation_prompt=True,tokenize=True);digest=hashlib.sha256(np.array(ids,dtype='<i8').tobytes()).hexdigest();assert digest==index[key,name]['input_ids_sha256'];checked+=1
    render={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prompts':len(prompts),'rendered_inputs_checked':checked,'input_ids_match_original_render_audit':checked,'default_header_preserved':True,'exact_header_prefix_matches':exact_prefix_matches,'header_keys':sorted(header_keys),'custom_system_body_after_default_header':True,'header_sha256':sorted(header_hashes),'effective_system_segment_sha256':{n:sorted(v)for n,v in segment_hashes.items()},'custom_body_sha256':{n:hashlib.sha256(t.encode()).hexdigest()for n,t in texts.items()},'tokenizer_chat_template_sha256':hashlib.sha256(tok.chat_template.encode()).hexdigest(),'original_render_audit_sha256':sha(old),'path_scope':'Same Llama role-based template for public batch8 and harmful single-row; report their refusal rates separately. Not Qwen replace/append variants.'}
    O.mkdir(exist_ok=True);p=O/'llama_system_header_audit.json';p.write_text(json.dumps(render,indent=2)+'\n')
    now=datetime.datetime.now(datetime.timezone.utc);done=[load(p)for p in S.glob('tail_done_*.json')];done=[x for x in done if x['kind']=='harmful'and x['condition']=='old_s0'and x['new_rows']>0];active=[];donepids={x['pid']for x in done}
    for p in S.glob('tail_live_gpu*.json'):
        x=load(p)
        if x['kind']=='harmful'and x['condition']=='old_s0'and x['pid']not in donepids and Path('/proc',str(x['pid'])).exists():active.append({**x,'elapsed_seconds':x['wall_seconds']})
    intervals=done+active
    for x in intervals:x['inferred_start_utc']=(datetime.datetime.fromisoformat(x['utc'])-datetime.timedelta(seconds=x['elapsed_seconds'])).isoformat()
    recent=sorted(done,key=lambda x:x['utc'])[-3:];rows=[]
    for x in recent:
        later=[a for a in intervals if a['shard']==x['shard']and a['inferred_start_utc']>x['utc']];nxt=min(later,key=lambda x:x['inferred_start_utc'])if later else None;wait=(datetime.datetime.fromisoformat(nxt['inferred_start_utc'])-datetime.datetime.fromisoformat(x['utc'])).total_seconds()if nxt else(now-datetime.datetime.fromisoformat(x['utc'])).total_seconds();rows.append({k:x[k]for k in ['pid','utc','shard','new_rows','elapsed_seconds','yielded']}|{'seconds_per_row':x['elapsed_seconds']/x['new_rows'],'until_same_shard_next_start_or_now_seconds':wait,'wait_ongoing':nxt is None})
    out={'utc':now.isoformat(),'recent_three_completed_batches':rows,'timing_scope':'Per-worker card time includes model/startup; shards0/1 can execute concurrently. Gaps include scheduler/priority waits and reload, not necessarily idle GPU.','GPU0_release':'2026-11-09T09:00:00+00:00; no new leases; finish current row or original batch then yield; continue on eligibleGPU2/3 by leases, not automatically halve a per-card speed.','render_audit_sha256':sha(O/'llama_system_header_audit.json')};p=O/'s0_recent_three_and_release.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'render':{k:v for k,v in render.items()if k not in ['tokenizer_chat_template_sha256','original_render_audit_sha256']},'ETA_audit':out,'ETA_sha256':sha(p)}))
if __name__=='__main__':main()
