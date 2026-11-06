import json, sys, numpy as np, torch, glob
sys.path.insert(0,'/home/dell/Def/src')
from transformers import AutoTokenizer, AutoModelForCausalLM
from gen.common import generate_with_injection
R="/home/dell/Def"
SNAP=sorted(glob.glob('/data/ray/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/*'))[0]
tok=AutoTokenizer.from_pretrained(SNAP)
mdl=AutoModelForCausalLM.from_pretrained(SNAP,torch_dtype=torch.bfloat16,device_map={'':'cuda:2'}).eval()
rows=json.load(open(R+'/configs/stage0_data/wjb_benign246_pairs300.json'))[:20]
ref=json.load(open(R+'/results/audit/WJB_BENIGN246_alpha0.json'))
zero=np.zeros(4096,dtype=np.float32)
same=0; n=0
for row in rows:
    for side in ('vanilla','adversarial'):
        key=row['id']+'|'+side
        if key not in ref['items']: continue
        ids=tok.apply_chat_template([{'role':'user','content':row[side]}],add_generation_prompt=True,return_tensors='pt').to('cuda:2')
        r=generate_with_injection(mdl,tok,ids,zero,layer=9,max_new_tokens=120,device='cuda:2',alpha=0)
        n+=1; same += (r['text']==ref['items'][key]['text'])
print("alpha0 cross-node 20 items:",same,"/",n)