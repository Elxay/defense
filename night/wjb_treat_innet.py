import json, glob, sys, os, time
sys.path.insert(0,'/home/dell/Def/src')
sys.path.insert(0,'/data/HZX/Def/src')
from gen.common import generate_with_injection
from transformers import AutoTokenizer, AutoModelForCausalLM
import numpy as np, torch
R="/data/HZX/Def"; DEV=sys.argv[1]; SEED=int(sys.argv[2]); ALPHA=float(sys.argv[3]); TAG=sys.argv[4]
SNAP=glob.glob("/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/*")[0]
tok=AutoTokenizer.from_pretrained(SNAP)
mdl=AutoModelForCausalLM.from_pretrained(SNAP,torch_dtype=torch.bfloat16,device_map={"":DEV}).eval()
v=np.load(f'{R}/results/audit/runs/block10_keep60_s{SEED}/v.npy').astype('float32'); v=v/np.linalg.norm(v)*(5.21*ALPHA)
rows=json.load(open(R+'/configs/stage0_data/wjb300.json'))
out={}; t0=time.time()
for i,r in enumerate(rows):
    ids=tok.apply_chat_template([{"role":"user","content":r['adversarial']}],add_generation_prompt=True,return_tensors="pt").to(DEV)
    res=generate_with_injection(mdl,tok,ids,v,layer=9,max_new_tokens=2400,device=DEV)
    out[r['id']]={"behavior":r['vanilla'],"text":res['text'],"new_tokens":res.get('new_tokens'),
                  "injection_count":res.get('injection_count'),"rho_runtime":res.get('delta_norm_runtime'),"host":"node01"}
    if i==24:
        print("SPEED_25 %.1fs"%(time.time()-t0),flush=True)
    if (i+1)%25==0: json.dump(out,open(f'{R}/results/audit/WJB_{TAG}.json','w'))
json.dump(out,open(f'{R}/results/audit/WJB_{TAG}.json','w'))
print("WJB_DONE",TAG,len(out),flush=True)