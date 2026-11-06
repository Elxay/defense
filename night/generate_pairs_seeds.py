"""Doc250 seed reproduction on the 300 benign pairs (single-item, atomic resume)."""
from pathlib import Path
import argparse, hashlib, json, os, socket, sys, time
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT=Path('/data/HZX/Def')
sys.path.insert(0,str(ROOT/'src')); sys.path.insert(0,'/home/dell/Def/src')
from gen.common import generate_with_injection
parser=argparse.ArgumentParser()
parser.add_argument('--device',required=True)
parser.add_argument('--seeds',nargs='+',type=int,required=True)
args=parser.parse_args()
torch.cuda.set_device(args.device)
OUT=ROOT/'results/audit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,obj):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(obj,ensure_ascii=False)+'\n');t.replace(p)
manifest=ROOT/'configs/stage0_data/wjb_benign246_pairs300.json'
rows=json.loads(manifest.read_text());assert len(rows)==300
snapshot=sorted(Path('/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots').iterdir())[0]
tok=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True)
mdl=AutoModelForCausalLM.from_pretrained(str(snapshot),torch_dtype=torch.bfloat16,device_map={'':args.device},local_files_only=True).eval()
for seed in args.seeds:
    vp=ROOT/f'results/audit/runs/block10_keep60_s{seed}/v.npy'
    v=np.load(vp).astype(np.float32);v=v/np.linalg.norm(v)*5.21
    cond=f'old_s{seed}'
    p=OUT/f'WJB_BENIGN246_{cond}.json'
    meta={'condition':cond,'manifest_sha256':sha(manifest),'generator_sha256':sha(Path(__file__)),
      'common_generator_sha256':sha(ROOT/'src/gen/common.py'),'model_snapshot':str(snapshot),
      'max_new_tokens':120,'batch_size':1,'layer':9,'host':socket.gethostname(),'device':args.device,
      'vector_sha256':hashlib.sha256(v.tobytes()).hexdigest(),'source_vector_sha256':sha(vp),
      'prereg_sha256':sha(ROOT/'docs/250_BENIGN_SEEDS_PREREG.md')}
    out=json.loads(p.read_text()) if p.exists() else {'metadata':meta,'items':{}}
    assert out['metadata']==meta,'resume metadata differs'
    for row in rows:
        for side in ['vanilla','adversarial']:
            key=row['id']+'|'+side
            if key in out['items']:continue
            ids=tok.apply_chat_template([{'role':'user','content':row[side]}],add_generation_prompt=True,return_tensors='pt').to(args.device)
            r=generate_with_injection(mdl,tok,ids,v,layer=9,max_new_tokens=120,device=args.device,alpha=1)
            assert r['injection_count']==1 and r['injection_positions']==[ids.shape[1]-1]
            assert abs(r['delta_norm_runtime']-5.21)<.05
            out['items'][key]={'pair_id':row['id'],'side':side,**r}
            atomic(p,out)
            if len(out['items'])%60==0:print(cond,len(out['items']),'/600',flush=True)
    assert len(out['items'])==600
    print('CONDITION_DONE',cond,flush=True)
print('ALL_DONE',flush=True)