"""Resume WJB learned s3/s4 and rand1 with the frozen single-item protocol."""
from pathlib import Path
import argparse, hashlib, json, os, sys, time
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
ROOT=Path('/home/dell/Def')
sys.path.insert(0,str(ROOT/'src'));from gen.common import generate_with_injection
p=argparse.ArgumentParser();p.add_argument('--kind',choices=['learned','random'],required=True);p.add_argument('--seed',type=int,required=True);args=p.parse_args()
dev=os.environ['DEVICE'];torch.cuda.set_device(dev)
snap=sorted(Path('/data/ray/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots').iterdir())[0]
tok=AutoTokenizer.from_pretrained(str(snap),local_files_only=True)
mdl=AutoModelForCausalLM.from_pretrained(str(snap),torch_dtype=torch.bfloat16,device_map={'':dev},local_files_only=True).eval()
if args.kind=='learned':v=np.load(ROOT/f'results/audit/runs/block10_keep60_s{args.seed}/v.npy').astype('float32');tag=f'old_s{args.seed}_a1.0'
else:v=np.random.default_rng(args.seed).normal(size=4096).astype('float32');tag=f'rand{args.seed}'
v=v/np.linalg.norm(v)*5.21
rows=json.loads((ROOT/'configs/stage0_data/wjb300.json').read_text())
target=ROOT/f'results/audit/WJB_{tag}.json';meta=target.with_suffix('.meta.json')
details={'kind':args.kind,'seed':args.seed,'batch_size':1,'max_new_tokens':2400,'layer':9,'node':'node01','manifest_sha256':hashlib.sha256((ROOT/'configs/stage0_data/wjb300.json').read_bytes()).hexdigest(),'vector_sha256':hashlib.sha256(v.tobytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
if target.exists():assert meta.exists() and json.loads(meta.read_text())==details,'unattested resume'
else:meta.write_text(json.dumps(details,indent=2)+'\n')
out=json.loads(target.read_text()) if target.exists() else {}
start=time.time();new_n=0
for row in rows:
    key=row['id']
    if key in out:continue
    ids=tok.apply_chat_template([{'role':'user','content':row['adversarial']}],add_generation_prompt=True,return_tensors='pt').to(dev)
    result=generate_with_injection(mdl,tok,ids,v,layer=9,max_new_tokens=2400,device=dev,alpha=1)
    assert result['injection_count']==1 and result['injection_positions']==[ids.shape[1]-1]
    out[key]={'behavior':row['vanilla'],'host':'node01','rho_runtime':result['delta_norm_runtime'],**result}
    temp=target.with_suffix('.json.tmp');temp.write_text(json.dumps(out)+'\n');temp.replace(target)
    new_n+=1
    if new_n==25:
        estimate=(time.time()-start)*300/25;print('ESTIMATE_SECONDS',estimate,flush=True)
        if estimate>6*3600:raise RuntimeError('BUDGET_STOP: >6 hours/condition; drop rand1 then s4 then s3; no judged output read')
    if len(out)%25==0:print(tag,len(out),'/300',flush=True)
assert len(out)==300
print('GENERATION_DONE',tag,flush=True)
