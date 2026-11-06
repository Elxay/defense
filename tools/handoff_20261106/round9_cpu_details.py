from pathlib import Path
import json,hashlib,datetime,sys,numpy as np
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round9';sys.path.insert(0,str(B/'src'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths={'frozen':'results/audit/runs/block10_keep60_s3/v.npy','earlier_fit12_retrain':'results/audit/retrain_check/block10_keep60_s3/v.npy','round8_retrain':'results/style_intervention/fidelity_s3/v.npy'}
v={k:np.load(B/p).astype(float)for k,p in paths.items()};comparisons={}
for a,c in [('frozen','earlier_fit12_retrain'),('frozen','round8_retrain'),('earlier_fit12_retrain','round8_retrain')]:
 cos=float(v[a]@v[c]/np.linalg.norm(v[a])/np.linalg.norm(v[c]));comparisons[a+'__'+c]=dict(cosine=cos,angle_degrees=float(np.degrees(np.arccos(np.clip(cos,-1,1)))),difference_norm=float(np.linalg.norm(v[a]-v[c])))
old=json.loads((B/'results/audit/RERUN_oldseed_s3_a1.0_b8f62434.json').read_text());new=json.loads((B/'results/style_intervention/fidelity_s3/val70.json').read_text());gate=json.loads((B/'results/style_intervention/fidelity_gate.json').read_text());jold=json.loads((B/gate['reference_file']).read_text())['items'];jnew=json.loads((B/'results/style_intervention/fidelity_s3/judge.json').read_text())['items']
from transformers import AutoTokenizer
tok=AutoTokenizer.from_pretrained('/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659',local_files_only=True)
rows=[]
for k in gate['changed_ids']:
 a=old[k]['text'];c=new[k]['text'];at=tok.encode(a,add_special_tokens=False);ct=tok.encode(c,add_special_tokens=False)
 first=next((i for i,(x,y)in enumerate(zip(a,c))if x!=y),min(len(a),len(c)));firsttok=next((i for i,(x,y)in enumerate(zip(at,ct))if x!=y),min(len(at),len(ct)))
 rows.append(dict(id=k,direction='up'if jnew[k]['p_yes']>.5 else'down',old_p=jold[k]['p_yes'],new_p=jnew[k]['p_yes'],old_new_tokens=old[k]['new_tokens'],new_new_tokens=new[k]['new_tokens'],old_chars=len(a),new_chars=len(c),old_eos=old[k]['eos'],new_eos=new[k]['eos'],first_different_character_0based=first,first_different_retokenized_token_0based=firsttok))
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),paths={k:dict(file=p,sha256=sha(B/p))for k,p in paths.items()},same_vector_earlier_and_round8=sha(B/paths['earlier_fit12_retrain'])==sha(B/paths['round8_retrain']),comparisons=comparisons,rows=rows,old_harmful=sum(z['p_yes']>.5 for z in jold.values()),new_harmful=sum(z['p_yes']>.5 for z in jnew.values()),n=70)
(O/'historical_rebuild_details.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
