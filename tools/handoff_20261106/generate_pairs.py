"""Doc246 single-item generation, with immutable preflight and atomic resume."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, socket, subprocess, sys, time
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT=Path('/data/HZX/Def')
sys.path.insert(0,str(ROOT/'src'))
from gen.common import generate_with_injection
parser=argparse.ArgumentParser()
parser.add_argument('--device',required=True)
parser.add_argument('--conditions',nargs='+',default=['alpha0','old_s0','rand0','rand1'],choices=['alpha0','old_s0','rand0','rand1'])
args=parser.parse_args()
torch.cuda.set_device(args.device)
OUT=ROOT/'results/audit/handoff_20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,obj):
    temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(obj,ensure_ascii=False)+'\n');temp.replace(p)
pre=json.loads((OUT/'doc246_pre_generation_stat.json').read_text())
for r in pre['files']:assert sha(ROOT/r['file'])==r['sha256'],r['file']
manifest=ROOT/'configs/stage0_data/wjb_benign246_pairs300.json'
rows=json.loads(manifest.read_text());assert len(rows)==300
model_path=ROOT/'models'
snapshot=sorted(Path('/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots').iterdir())[0]
tok=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True)
mdl=AutoModelForCausalLM.from_pretrained(str(snapshot),torch_dtype=torch.bfloat16,device_map={'':args.device},local_files_only=True).eval()
vp=ROOT/'results/audit/runs/block10_keep60_s0/v.npy'
old=np.load(vp).astype(np.float32);old=old/np.linalg.norm(old)*5.21
vectors={'alpha0':np.zeros(4096,dtype=np.float32),'old_s0':old}
for seed in [0,1]:
    v=np.random.default_rng(seed).normal(size=4096).astype(np.float32);vectors[f'rand{seed}']=v/np.linalg.norm(v)*5.21
for cond in args.conditions:
    p=ROOT/f'results/audit/WJB_BENIGN246_{cond}.json'
    meta={'condition':cond,'manifest_sha256':sha(manifest),'generator_sha256':sha(Path(__file__)),
      'common_generator_sha256':sha(ROOT/'src/gen/common.py'),'model_snapshot':str(snapshot),
      'max_new_tokens':120,'batch_size':1,'layer':9,'host':socket.gethostname(),'device':args.device,
      'vector_sha256':hashlib.sha256(vectors[cond].tobytes()).hexdigest(),'source_vector_sha256':sha(vp) if cond=='old_s0' else None}
    out=json.loads(p.read_text()) if p.exists() else {'metadata':meta,'items':{}}
    assert out['metadata']==meta,'resume metadata differs'
    for row in rows:
        for side in ['vanilla','adversarial']:
            key=row['id']+'|'+side
            if key in out['items']:continue
            ids=tok.apply_chat_template([{'role':'user','content':row[side]}],add_generation_prompt=True,return_tensors='pt').to(args.device)
            result=generate_with_injection(mdl,tok,ids,vectors[cond],layer=9,max_new_tokens=120,device=args.device,alpha=0 if cond=='alpha0' else 1)
            assert result['injection_count']==1 and result['injection_positions']==[ids.shape[1]-1]
            assert abs(result['delta_norm_runtime']-(0 if cond=='alpha0' else 5.21))<.05
            out['items'][key]={'pair_id':row['id'],'side':side,**result}
            atomic(p,out)
            first=OUT/'doc246_first_generation_stat.json'
            if not first.exists():
                st=p.stat();assert all(r['mtime_ns']<st.st_mtime_ns for r in pre['files'])
                atomic(first,{'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'first_output':str(p.relative_to(ROOT)),'first_output_mtime_ns':st.st_mtime_ns,
                  'first_output_sha256':sha(p),'first_output_items':len(out['items']),
                  'prereg_files':pre['files'],'all_prereg_files_earlier':True})
                with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:
                    f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+' docs/246 FIRST_GENERATION stat=results/audit/handoff_20261106/doc246_first_generation_stat.json; original/addendum/manifest/embedding-audit all predate first output; same-node single-item 120-token protocol.\n')
            if len(out['items'])%20==0:print(cond,len(out['items']),'/600',flush=True)
    assert len(out['items'])==600
    print('CONDITION_DONE',cond,flush=True)
print('ALL_DONE',flush=True)
