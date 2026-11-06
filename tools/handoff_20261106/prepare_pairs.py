"""Select and audit doc246 pairs before any generation."""
from pathlib import Path
import csv, datetime, hashlib, json, os, re, sys, unicodedata
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
ROOT=Path('/data/HZX/Def')
OUT=ROOT/'results/audit/handoff_20261106'
torch.set_num_threads(4)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def norm(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s).lower()).strip()
doc=ROOT/'docs/246_WJB_BENIGN_PAIR_PREREG.md'
assert sha(doc)=='44629af52476026ee94ae4b3faf38e522fb259ba4b19186b94c82f5096ed81b0'
assert not list((ROOT/'results/audit').glob('WJB_BENIGN246_*.json')),'generation already exists'
val=json.loads((ROOT/'data/wjb_val_pairs.json').read_text())
base=json.loads((ROOT/'results/audit/LEGALVALB_none.json').read_text())
val=[x for x in val if not base[x['key']]['refused']]
assert len(val)==296
keep=json.loads((ROOT/'configs/keep60_ids.json').read_text())['keep60'];assert len(keep)==60
train=json.loads((ROOT/'configs/stage0_data/b8_train_strat.json').read_text())['items'];assert len(train)==97
refs=[]
for x in val:
    for field in ['vanilla','adversarial']:refs.append({'id':'val:'+x['key']+':'+field,'text':x[field]})
for x in keep:refs.append({'id':'keep60:'+x['id'],'text':x['text']})
for i,x in enumerate(train):
    for j,text in enumerate(x['texts']):refs.append({'id':f'train_strat:{i}:{j}','text':text})
snapshot=sorted(Path('/data/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots').iterdir())[0]
model=SentenceTransformer(str(snapshot),device='cpu',local_files_only=True)
model.max_seq_length=256
ref_emb=model.encode([x['text'] for x in refs],normalize_embeddings=True,batch_size=64,convert_to_numpy=True,show_progress_bar=False)
source=sorted(Path('/data/huggingface/hub/datasets--allenai--wildjailbreak/snapshots').glob('*/train/train.tsv'))[0]
csv.field_size_limit(sys.maxsize)
candidates=[]
with source.open(newline='') as f:
    for i,row in enumerate(csv.DictReader(f,delimiter='\t')):
        if row['data_type']=='adversarial_benign' and row.get('vanilla') and row.get('adversarial'):
            candidates.append({'id':f'wjb_benign_{i}','source_row':i,'vanilla':row['vanilla'],'adversarial':row['adversarial']})
rng=np.random.default_rng(20261106);order=rng.permutation(len(candidates))
selected=[];checks=[];excluded=[];seen=set();accepted_emb=None
for st in range(0,len(order),400):
    chunk=[candidates[i] for i in order[st:st+400]]
    em=model.encode([x[field] for x in chunk for field in ['vanilla','adversarial']],normalize_embeddings=True,batch_size=64,convert_to_numpy=True,show_progress_bar=False).reshape(len(chunk),2,-1)
    for x,e in zip(chunk,em):
        if norm(x['vanilla']) in seen:
            excluded.append({'id':x['id'],'reason':'duplicate_vanilla'});continue
        sims=e@ref_emb.T
        ri=np.unravel_index(np.argmax(sims),sims.shape);maxref=float(sims[ri])
        internal=float((e@accepted_emb.T).max()) if accepted_emb is not None else -1.
        if max(maxref,internal)>=.85:
            excluded.append({'id':x['id'],'reason':'near_reference' if maxref>=.85 else 'near_selected','cosine_reference':maxref,'reference':refs[ri[1]]['id'],'cosine_selected':internal});continue
        selected.append(x);seen.add(norm(x['vanilla']))
        checks.append({'id':x['id'],'max_reference_cosine':maxref,'reference':refs[ri[1]]['id'],'candidate_side':['vanilla','adversarial'][ri[0]],'max_previous_selected_cosine':internal})
        accepted_emb=e.copy() if accepted_emb is None else np.concatenate([accepted_emb,e])
        if len(selected)==300:break
    print('AUDIT accepted',len(selected),'examined',len(selected)+len(excluded),flush=True)
    if len(selected)==300:break
assert len(selected)==300
manifest=ROOT/'configs/stage0_data/wjb_benign246_pairs300.json'
assert not manifest.exists(),'refuse overwriting frozen manifest'
write(manifest,selected)
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'threshold':.85,'comparison':'both vanilla/adversarial against val296 both sides, keep60 and all train_strat texts; and previously selected pairs','seed':20261106,'n':300,'reference_counts':{'val_pairs':296,'val_texts':592,'keep60':60,'train_groups':97,'train_texts':len(refs)-652},
 'model':{'snapshot':str(snapshot),'max_seq_length':256,'pooling':'SentenceTransformer default; normalized embeddings','warning':'Text beyond 256 tokenizer tokens is truncated by the embedding model.'},'source_tsv':{'path':str(source),'sha256':sha(source)},'manifest':{'file':str(manifest.relative_to(ROOT)),'sha256':sha(manifest)},'checks':checks,'excluded':excluded,
 'max_reference_cosine':max(x['max_reference_cosine'] for x in checks),'max_selected_pair_cosine':max(x['max_previous_selected_cosine'] for x in checks)}
write(OUT/'doc246_nearest_neighbor_audit.json',report)
addendum=ROOT/'docs/246_ADDENDUM_RAND1_AND_AUDIT.md'
assert not addendum.exists()
addendum.write_text('# 246 追加：近邻审计与第二个随机方向（任何配对生成之前）\n\n'
 '原文件保持不变，原 sha256='+sha(doc)+'。\n'
 '固定条件：alpha0、old s0 alpha=1、rand0、rand1；同一份 300 对清单，同节点 innet，同顺序，单条生成（batch size=1），每侧 120 token，统一 generate_with_injection。\n'
 '随机方向：np.random.default_rng(0/1) 各自生成 4096 维高斯后归一到 5.21；方向间分别报告，不合并成一个随机点。\n'
 '数值判据不变：learned 双重差 >=3pp 且 95% 区间排除 0；随机方向双重差在 +/-3pp 内。对 rand0、rand1 分别应用原判据并并列报告；不因新增方向改阈值或筛选方向。\n'
 '分析集：alpha0 对两侧均回答的配对；固定规则 v2；按 vanilla 聚类 bootstrap 2000 次（seed=20261106）。v3/V_b 仅作并列敏感性，不替换主口径。\n'
 '抽样 seed=20261106，按固定随机顺序取最先通过排除与近邻检查的 300 个不同 vanilla；比较 val296 双侧、keep60、train_strat 全部文本，并排除清单内部 >=0.85 近邻。\n'
 '清单：'+str(manifest.relative_to(ROOT))+'；sha256='+sha(manifest)+'。\n'
 '审计：results/audit/handoff_20261106/doc246_nearest_neighbor_audit.json；sha256='+sha(OUT/'doc246_nearest_neighbor_audit.json')+'。\n'
 '模型为缓存 all-MiniLM-L6-v2；max_seq_length=256，长文本会被截断，不能把通过阈值解释为完整语义互斥。\n',encoding='utf-8')
stamp={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[],'generation_files_present':[]}
for p in [doc,addendum,manifest,OUT/'doc246_nearest_neighbor_audit.json']:
    st=p.stat();stamp['files'].append({'file':str(p.relative_to(ROOT)),'mtime_ns':st.st_mtime_ns,'mtime_utc':datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat(),'sha256':sha(p)})
write(OUT/'doc246_pre_generation_stat.json',stamp)
with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:
    now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    f.write(f'{now} docs/246 addendum rand1+embedding audit BEFORE ANY paired generation; original immutable sha256={sha(doc)}; addendum sha256={sha(addendum)}; manifest sha256={sha(manifest)}; audit sha256={sha(OUT/"doc246_nearest_neighbor_audit.json")}; stat=results/audit/handoff_20261106/doc246_pre_generation_stat.json; thresholds unchanged.\n')
print('AUDIT_DONE',json.dumps({k:report[k] for k in ['n','reference_counts','max_reference_cosine','max_selected_pair_cosine','manifest']}),flush=True)
