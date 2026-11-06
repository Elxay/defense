"""Post-failure diagnostic only: replay frozen vector on the five changed prompts; never releases training gate."""
from pathlib import Path
import os,json,hashlib,datetime,sys,ast
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round8'
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='2'and os.environ.get('DEVICE')=='cuda:0'
gate=json.loads((B/'results/style_intervention/fidelity_gate.json').read_text());assert not gate['passed']
src=B/'stage136/keep60_seed.py';text=src.read_text();prefix=text[:text.index('ref_targets=[gen(')].replace('map_location="cpu")','map_location="cpu",weights_only=False)').replace('"meta-llama/Llama-3.1-8B-Instruct", revision=REV','"/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659", local_files_only=True')
sys.argv=[str(src),'3'];ns={};exec(compile(prefix,str(src),'exec'),ns);ns['mdl'].config.use_cache=True
sys.path.insert(0,str(B/'src'));from gen.common import generate_with_injection
v=ns['np'].load(B/'results/audit/runs/block10_keep60_s3/v.npy');v=v/ns['np'].linalg.norm(v)*5.21
prompts={}
for n in ['STAGE0_VAL_PAIR.json','STAGE0_VAL_HB_PAIR.json','STAGE0_VAL_HB_PAIR2.json','STAGE0_VAL_HB_PAIR3.json']:
 for r in json.loads((B/'results/audit'/n).read_text()):
  if r['result'].get('success'):prompts[r['behavior_id']]=r['result']['best_prompt']
old=json.loads((B/'results/audit/RERUN_oldseed_s3_a1.0_b8f62434.json').read_text());items=[]
for k in gate['changed_ids']:
 ids=ns['tok'].apply_chat_template([{'role':'user','content':prompts[k]}],add_generation_prompt=True,return_tensors='pt').to('cuda:0');z=generate_with_injection(ns['mdl'],ns['tok'],ids,v,layer=9,max_new_tokens=2400,device='cuda:0');items.append(dict(id=k,byte_equal=z['text'].encode()==old[k]['text'].encode(),generated=z));print('DIAGNOSTIC',k,items[-1]['byte_equal'],flush=True)
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),purpose='post_failure_diagnostic_not_gate_retry',n=5,n_byte_equal=sum(r['byte_equal']for r in items),items=items,frozen_gate_unchanged=True)
(O/'fidelity_failure_replay5.json').write_text(json.dumps(out,indent=2)+'\n')
