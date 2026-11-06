import json, os, sys, random
sys.path.insert(0,"/data/HZX/Def/client"); sys.path.insert(0,"/data/HZX/Def/stage1"); sys.path.insert(0,"/data/HZX/Def")
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from judge_outputs import is_refusal
ROOT="/data/HZX/Def"; REV="0e9e39f249a16976918f6564b8830bc894c89659"; LAYER=9
NAME=sys.argv[1]; VEC=sys.argv[2]
SCALE=float(os.environ.get("SCALE","1.0"))
vec=None if VEC=="none" else np.load(VEC).astype(np.float32)
if vec is not None: vec=vec/np.linalg.norm(vec)*5.21*SCALE
leg=[json.loads(l) for l in open(os.path.join(ROOT,"configs/stage0_data/legal_val.jsonl"))]
rng=random.Random(0); items=[]
for g in ("ord","sens","long","roleplay"):
    pool=[r for r in leg if r['group']==g]; rng.shuffle(pool); items+=[(g,r['text']) for r in pool[:100]]
SNAP=__import__("glob").glob("/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/*")[0]
tok=AutoTokenizer.from_pretrained(SNAP)
mdl=AutoModelForCausalLM.from_pretrained(SNAP, torch_dtype=torch.bfloat16, device_map={"":os.environ["DEVICE"]}).eval()
outpath=os.path.join(ROOT,f"results/audit/LEGALVAL_{NAME}.json")
out=json.load(open(outpath)) if os.path.exists(outpath) else {}
def gen(p):
    ids=tok.apply_chat_template([{"role":"user","content":p}],add_generation_prompt=True,return_tensors="pt").to(os.environ["DEVICE"])
    box={"done":False}
    def hook(mod,args,output):
        if box["done"] or vec is None: box["done"]=True; return output
        h=output[0].clone(); h[0,-1,:]=h[0,-1,:]+torch.tensor(vec,dtype=h.dtype,device=h.device)
        box["done"]=True; return (h,)+output[1:]
    hd=mdl.model.layers[LAYER].register_forward_hook(hook)
    with torch.no_grad(): o=mdl.generate(ids,max_new_tokens=120,do_sample=False,pad_token_id=tok.eos_token_id)
    hd.remove(); return tok.decode(o[0][ids.shape[1]:],skip_special_tokens=True)
for i,(g,p) in enumerate(items):
    k=f"{g}:{i}"
    if k in out: continue
    t=gen(p); sys.path.insert(0,"/data/HZX/Def/src")
    from judge.refusal import new_rule
    out[k]={"group":g,"refused":new_rule(t),"len":len(t),"text":t,"vec_sha256":__import__("hashlib").sha256(open(VEC,"rb").read()).hexdigest() if VEC!="none" else "none","scale":SCALE,"alpha":SCALE}
    print(NAME,k,out[k]["refused"],flush=True); json.dump(out,open(outpath,"w"))
print("done",NAME,len(out))