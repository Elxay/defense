from pathlib import Path
import os,fcntl,subprocess,datetime,json,sys,hashlib
b=Path('/data/HZX/Def');o=b/'results/audit/handoff_round5'
with(b/'logs/pid_registry.txt').open('a')as f:
 fcntl.flock(f,fcntl.LOCK_EX);f.write(str(os.getpid())+'|'+subprocess.check_output(['ps','-p',str(os.getpid()),'-o','lstart='],text=True).strip()+'|'+str(Path(__file__))+'\n');f.flush()
import numpy as np,torch
torch.set_num_threads(4)
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(b/'src'));from judge.refusal import new_rule
rows=json.loads((b/'configs/stage0_data/wjb_benign246_pairs300.json').read_text());a=json.loads((b/'results/audit/WJB_BENIGN246_alpha0.json').read_text())['items'];data={tag:json.loads((b/f'results/audit/WJB_BENIGN246_{tag}.json').read_text())['items']for tag in['old_s0','rand0','rand1']}
el=[r['id']for r in rows if not any(new_rule(a[r['id']+'|'+s]['text'])for s in['vanilla','adversarial'])];assert len(el)==292
snap='/data/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
model=SentenceTransformer(snap,device='cpu');emb=model.encode([r[s]for r in rows for s in['vanilla','adversarial']],normalize_embeddings=True,batch_size=32,show_progress_bar=False)
cos=(emb[::2]*emb[1::2]).sum(1);within=[{'id':r['id'],'cosine':float(c)}for r,c in zip(rows,cos)if r['id']in el];within.sort(key=lambda x:-x['cosine']);within=within[:5]
aud=json.loads((b/'results/audit/handoff_20261106/doc246_nearest_neighbor_audit.json').read_text());refs=sorted(aud['checks'],key=lambda x:-x['max_reference_cosine'])[:5]
sets={'primary292':el,'exclude_preread_reference_top5':[k for k in el if k not in {r['id']for r in refs}],'exclude_posthoc_withinpair_top5':[k for k in el if k not in {r['id']for r in within}]};summ={}
for name,keys in sets.items():
 n=len(keys);rng=np.random.default_rng(20261106);ix=rng.integers(0,n,(2000,n));out={}
 for tag,d in data.items():
  van=np.array([new_rule(d[k+'|vanilla']['text'])for k in keys],int);adv=np.array([new_rule(d[k+'|adversarial']['text'])for k in keys],int);diff=adv-van
  out[tag]={'n':n,'vanilla_new':int(van.sum()),'adversarial_new':int(adv.sum()),'dd_pp':float(diff.mean()*100),'ci95':(np.quantile(diff[ix].mean(1),[.025,.975])*100).tolist()}
 summ[name]=out
excluded=[]
for r in rows:
 if r['id']in el:continue
 flags={s:new_rule(a[r['id']+'|'+s]['text'])for s in['vanilla','adversarial']};excluded.append({'id':r['id'],'alpha0_rule_flags':flags,'reason':'alpha0 at least one side v2-refused; preregistered eligibility only','other_exclusion':False})
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_top5':refs,'withinpair_top5':within,'sensitivity':summ,'excluded8':excluded,'audit_threshold_definition':aud['comparison'],'audit_max_reference':aud['max_reference_cosine'],'audit_max_across_selected_pairs':aud['max_selected_pair_cosine'],'within_pair_partner_not_in_dedup_comparison':True,'embedding_model':snap,'embedding_max_length':model.max_seq_length,'device':'CPU','note':'Two distinct cosine metrics. Posthoc within-pair top5 is not the pre-read reference-neighbor sensitivity; no change to original audit exclusion threshold.'}
(o/'cosine_and_exclusions.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
