"""Batched legal-val evaluation (left padding, per-row last-token injection)."""
import json, os, sys, random
sys.path.insert(0,"/data/HZX/Def/client"); sys.path.insert(0,"/data/HZX/Def/stage1"); sys.path.insert(0,"/data/HZX/Def")
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
sys.path.insert(0,"/data/HZX/Def/src")
from judge.refusal import new_rule
ROOT="/data/HZX/Def"; LAYER=9; BS=8
NAME=sys.argv[1]; VEC=sys.argv[2] if len(sys.argv)>2 and sys.argv[2]!="none" else None
SCALE=float(os.environ.get('SCALE','1.0'))
DEV=os.environ['DEVICE']
vec=None if not VEC else np.load(VEC).astype(np.float32)
if vec is not None: vec=vec/np.linalg.norm(vec)*5.21*SCALE
leg=[json.loads(l) for l in open(os.path.join(ROOT,"configs/stage0_data/legal_val.jsonl"))]
rng=random.Random(0); items=[]
for g in ("ord","sens","long","roleplay"):
    pool=[r for r in leg if r['group']==g]; rng.shuffle(pool); items+=[(g,r['text']) for r in pool[:100]]
SNAP=__import__("glob").glob("/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/*")[0]
tok=AutoTokenizer.from_pretrained(SNAP); tok.padding_side="left"; tok.pad_token=tok.eos_token
mdl=AutoModelForCausalLM.from_pretrained(SNAP, torch_dtype=torch.bfloat16, device_map={"":DEV}).eval()
outpath=os.path.join(ROOT,f"results/audit/LEGALVALB_{NAME}.json")
out=json.load(open(outpath)) if os.path.exists(outpath) else {}
todo=[(i,g,p) for i,(g,p) in enumerate(items) if f"{g}:{i}" not in out]
def run_batch(batch):
    rendered=[tok.apply_chat_template([{"role":"user","content":p}],add_generation_prompt=True, tokenize=False) for _,_,p in batch]
    enc=tok(rendered,return_tensors="pt",padding=True,add_special_tokens=False).to(DEV)
    n_p=enc.input_ids.shape[1]; L=n_p; pos=torch.arange(L,device=DEV).unsqueeze(0); idx=((enc.attention_mask*pos).max(1).values)
    box={"done":False}
    def hook(mod,args,output):
        if box["done"]: box["done"]=True; return output
        h=output[0].clone()
        for b in range(h.shape[0]):
            if vec is not None: h[b,int(idx[b]),:]=h[b,int(idx[b]),:]+torch.tensor(vec,dtype=h.dtype,device=h.device)
        box["done"]=True; return (h,)+output[1:]
    hd=mdl.model.layers[LAYER].register_forward_hook(hook)
    with torch.no_grad(): o=mdl.generate(**enc,max_new_tokens=120,do_sample=False,pad_token_id=tok.eos_token_id)
    hd.remove()
    return [tok.decode(o[b][n_p:],skip_special_tokens=True) for b in range(o.shape[0])]
for s in range(0,len(todo),BS):
    batch=todo[s:s+BS]; texts=run_batch(batch)
    for (i,g,p),t in zip(batch,texts):
        out[f"{g}:{i}"]={"group":g,"refused":new_rule(t),"len":len(t),"text":t,"alpha":SCALE,"rho":5.21,"vec_sha256":__import__("hashlib").sha256(open(VEC,"rb").read()).hexdigest() if VEC else "none","delta_norm_runtime":float(np.linalg.norm(vec)) if vec is not None else 0.0}
    json.dump(out,open(outpath,"w"))
    print(NAME,"done",len(out),flush=True)
print("done",NAME,len(out))