import json, glob, sys, numpy as np, torch
sys.path.insert(0,'/data/HZX/Def/src')
from gen.common import generate_with_injection
from transformers import AutoTokenizer, AutoModelForCausalLM
R="/data/HZX/Def"
SNAP=glob.glob("/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/*")[0]
tok=AutoTokenizer.from_pretrained(SNAP)
mdl=AutoModelForCausalLM.from_pretrained(SNAP,torch_dtype=torch.bfloat16,device_map={"":"cuda:2"}).eval()
v=np.load(R+'/results/audit/runs/block10_keep60_s0/v.npy').astype('float32'); v=v/np.linalg.norm(v)*5.21
rows=json.load(open(R+'/configs/stage0_data/wjb300.json'))
ref=json.load(open(R+'/results/audit/WJB_old_s0_a1.0.json'))
same=0; n=0
for r in rows[:20]:
    ids=tok.apply_chat_template([{"role":"user","content":r['adversarial']}],add_generation_prompt=True,return_tensors="pt").to("cuda:2")
    res=generate_with_injection(mdl,tok,ids,v,layer=9,max_new_tokens=2400,device="cuda:2")
    n+=1; same += (res['text']==ref[r['id']]['text'])
print("innet s0 WJB 20 items byte-identical:",same,"/",n)