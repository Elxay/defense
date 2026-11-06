from pathlib import Path
import os
os.environ.update(OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',USE_TF='0',USE_FLAX='0')
import json,datetime,hashlib,sys,numpy as np,torch
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round9';sys.path.insert(0,str(B/'src'));from judge.refusal import new_rule
v=json.loads((B/'results/audit/handoff_round8/doc250_vanilla20_review.json').read_text());drop=[r for r in v['items']if r['partition']!='baseline_content_response_to_refusal_form'];assert len(drop)==11
ids=sorted({r['id']for r in drop});spec=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),post_hoc=True,n_condition_rows=11,shared_exclusion_ids=ids,primary_sensitivity='exclude union of pair IDs in all five seed datasets; fixed common subset',secondary='exclude only reviewed condition-item rows, seed-specific subsets; diagnostic only')
(O/'doc250_posthoc_exclusion_spec.json').write_text(json.dumps(spec,indent=2)+'\n')
base=json.loads((B/'results/audit/WJB_BENIGN246_alpha0.json').read_text());print('BASE_SCHEMA',list(base),flush=True)
# Files are id-> {vanilla/adversarial} outputs; normalize from observed schema below.

base=base['items'];eligible=[k for k in json.loads((B/'configs/stage0_data/wjb_benign246_pairs300.json').read_text())if not any(new_rule(base[k['id']+'|'+side]['text'])for side in['vanilla','adversarial'])];assert len(eligible)==292
rows=[]
for seed in range(3,8):
 d=json.loads((B/f'results/audit/WJB_BENIGN246_old_s{seed}.json').read_text())['items'];out={'seed':seed}
 for label,ex in [('shared_union',set(ids)),('condition_rows',{r['id']for r in drop if r['seed']==seed})]:
  keep=[r['id']for r in eligible if r['id']not in ex];adv=sum(new_rule(d[k+'|adversarial']['text'])for k in keep);van=sum(new_rule(d[k+'|vanilla']['text'])for k in keep);out[label]=dict(n=len(keep),adversarial_new=adv,vanilla_new=van,DD_pp=100*(adv-van)/len(keep))
 rows.append(out)
(O/'doc250_posthoc_sensitivity.json').write_text(json.dumps(dict(spec=spec,rows=rows),indent=2)+'\n');print('SENSITIVITY',json.dumps(rows),flush=True)
from sentence_transformers import SentenceTransformer
torch.set_num_threads(4);audit=json.loads((B/'results/audit/handoff_round8/style_data_audit.json').read_text());pool=json.loads((B/'results/audit/handoff_round8/style_audited_candidate_pool.json').read_text());model=SentenceTransformer(audit['embedding_model'],device='cpu',local_files_only=True);model.max_seq_length=256;tok=model.tokenizer;texts=[];owners=[]
for i,r in enumerate(pool):
 for side in ['vanilla','adversarial']:
  tokens=tok.encode(r[side],add_special_tokens=False)
  for start in range(0,len(tokens),200):texts.append(tok.decode(tokens[start:start+254],skip_special_tokens=True));owners.append(dict(group=i,id=r['id'],side=side,range=[start,min(start+254,len(tokens))]))
emb=model.encode(texts,normalize_embeddings=True,batch_size=64,convert_to_numpy=True,show_progress_bar=False);sim=emb@emb.T;pairs=[]
for i in range(len(pool)):
 for j in range(i+1,len(pool)):
  a=[k for k,r in enumerate(owners)if r['group']==i];c=[k for k,r in enumerate(owners)if r['group']==j];m=sim[np.ix_(a,c)];u,v=np.unravel_index(m.argmax(),m.shape);pairs.append(dict(cosine=float(m[u,v]),a=owners[a[u]],b=owners[c[v]],vanilla_a=pool[i]['vanilla'],vanilla_b=pool[j]['vanilla']))
pairs.sort(key=lambda r:-r['cosine']);assert abs(pairs[0]['cosine']-audit['max_other_selected_cosine'])<1e-5
old=json.loads((B/'results/style_intervention/style_training_targets.json').read_text());finalids={r['id']for r in old['items']};nearest=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pool_top5=pairs[:5],prior60_top5=[r for r in pairs if r['a']['id']in finalids and r['b']['id']in finalids][:5],all_pairs=pairs,rejected_reference_neighbors=[dict(id=r['id'],cosine=r['max_reference_cosine'],top5=r['top5'])for r in audit['rejected']if r['reason']=='embedding_reference'],source_audit_sha256=hashlib.sha256((B/'results/audit/handoff_round8/style_data_audit.json').read_bytes()).hexdigest())
(O/'style_top_neighbors.json').write_text(json.dumps(nearest,ensure_ascii=False,indent=2)+'\n');print('NEIGHBORS',json.dumps(nearest['pool_top5'],ensure_ascii=False),flush=True)
