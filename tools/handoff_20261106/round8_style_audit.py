"""CPU-only, full-window group audit before any intervention training."""
import os
os.environ.update(OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1')
from pathlib import Path
import csv,json,sys,re,unicodedata,hashlib,datetime,time,collections
import numpy as np,torch
from sentence_transformers import SentenceTransformer
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round8';torch.set_num_threads(4)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(p,d):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def norm(t):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',t).casefold()).strip()
def pulse(phase,**kw):atomic(O/'style_audit_live.json',dict(utc=now(),pid=os.getpid(),phase=phase,device='CPU',**kw))
assert not list((B/'results').glob('style_intervention*/**/v.npy'))
refs=[];sourcefiles=[]
def ref(group,key,text):
 if text:refs.append(dict(group=group,id=group+':'+str(key),text=text))
base=json.loads((B/'results/audit/LEGALVALB_none.json').read_text());val=json.loads((B/'data/wjb_val_pairs.json').read_text());val=[r for r in val if not base[r['key']]['refused']];assert len(val)==296
for r in val:
 for side in ['vanilla','adversarial']:ref('val296',r['key']+':'+side,r[side])
for r in json.loads((B/'configs/stage0_data/wjb_benign246_pairs300.json').read_text()):
 for side in ['vanilla','adversarial']:ref('docs250',r['id']+':'+side,r[side])
keep=json.loads((B/'configs/keep60_ids.json').read_text())['keep60'];assert len(keep)==60
for r in keep:ref('keep60',r['id'],r['text'])
train=json.loads((B/'configs/stage0_data/b8_train_strat.json').read_text())['items'];assert len(train)==97
for i,r in enumerate(train):
 for j,t in enumerate(r['texts']):ref('train_strat',str(i)+':'+str(j),t)
for r in json.loads((B/'data/legal_val_items.json').read_text()):ref('legal400',r['key'],r['prompt'])
for r in json.loads((B/'configs/stage0_data/wjb300.json').read_text()):
 for side in ['vanilla','adversarial']:ref('WJB_harm300',r['id']+':'+side,r[side])
refnorm={norm(r['text'])for r in refs};snap='/data/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
pulse('loading_cpu_embedding_model',reference_counts=dict(collections.Counter(r['group']for r in refs)))
model=SentenceTransformer(snap,device='cpu',local_files_only=True);model.max_seq_length=256;tok=model.tokenizer;assert tok.num_special_tokens_to_add(False)==2
cache={}
def windows(text):
 key=hashlib.sha256(text.encode()).hexdigest()
 if key in cache:return cache[key]
 ids=tok.encode(text,add_special_tokens=False);pieces=[tok.decode(ids[i:i+254],skip_special_tokens=True)for i in range(0,len(ids),200)]or[''];ranges=[[i,min(i+254,len(ids))]for i in range(0,len(ids),200)]or[[0,0]]
 cache[key]=(pieces,ranges);return pieces,ranges
texts=[];refindex=[]
for i,r in enumerate(refs):
 w,_=windows(r['text']);texts+=w;refindex.extend([i]*len(w))
refemb=model.encode(texts,normalize_embeddings=True,batch_size=64,convert_to_numpy=True,show_progress_bar=False);refindex=np.array(refindex)
source=sorted(Path('/data/huggingface/hub/datasets--allenai--wildjailbreak/snapshots').glob('*/train/train.tsv'))[0];csv.field_size_limit(sys.maxsize);groups=collections.defaultdict(list)
with source.open(newline='')as f:
 for i,r in enumerate(csv.DictReader(f,delimiter='\t')):
  if r['data_type']=='adversarial_benign'and r.get('vanilla')and r.get('adversarial'):groups[norm(r['vanilla'])].append(dict(id=f'wjb_benign_{i}',source_row=i,vanilla=r['vanilla'],adversarial=r['adversarial']))
keys=sorted(groups);rng=np.random.default_rng(202611070252);order=rng.permutation(len(keys));accepted=[];checks=[];rejected=[];selected_emb=None;t0=time.monotonic()
pulse('auditing',total_groups=len(keys),reference_windows=len(texts),accepted=0)
for number,gindex in enumerate(order):
 key=keys[gindex];variants=groups[key]
 if any(norm(r[side])in refnorm for r in variants for side in ['vanilla','adversarial']):rejected.append(dict(group_sha256=hashlib.sha256(key.encode()).hexdigest(),reason='group_exact_reference'));continue
 r=variants[int(rng.integers(0,len(variants)))];candidate=[];ranges={}
 for side in ['vanilla','adversarial']:
  w,rg=windows(r[side]);candidate+=w;ranges[side]=rg
 emb=model.encode(candidate,normalize_embeddings=True,batch_size=32,convert_to_numpy=True,show_progress_bar=False);sim=emb@refemb.T;maxref=float(sim.max());scores=np.full(len(refs),-np.inf);np.maximum.at(scores,refindex,sim.max(axis=0));top=np.argsort(scores)[-5:][::-1]
 internal=float((emb@selected_emb.T).max())if selected_emb is not None else -1.
 record=dict(id=r['id'],group_sha256=hashlib.sha256(key.encode()).hexdigest(),max_reference_cosine=maxref,max_other_selected_group_cosine=internal,top5=[dict(reference=refs[i]['id'],cosine=float(scores[i]))for i in top],candidate_window_token_ranges=ranges)
 if max(maxref,internal)>=.85:rejected.append(dict(**record,reason='embedding_reference'if maxref>=.85 else'embedding_other_group'))
 else:
  accepted.append(dict(**r,vanilla_group_sha256=record['group_sha256']));checks.append(record);selected_emb=emb.copy()if selected_emb is None else np.concatenate([selected_emb,emb])
 if number%25==0 or len(accepted)==120:pulse('auditing',examined_groups=number+1,accepted=len(accepted),rejected=len(rejected),elapsed_seconds=time.monotonic()-t0)
 if len(accepted)==120:break
assert len(accepted)>=60,'<60 audited groups: stop; never lower threshold'
assert len({r['vanilla_group_sha256']for r in accepted})==len(accepted)
manifest=O/'style_audited_candidate_pool.json';assert not manifest.exists();atomic(manifest,accepted)
sourcefiles=['data/wjb_val_pairs.json','results/audit/LEGALVALB_none.json','configs/stage0_data/wjb_benign246_pairs300.json','configs/keep60_ids.json','configs/stage0_data/b8_train_strat.json','data/legal_val_items.json','configs/stage0_data/wjb300.json','docs/252_ADDENDUM1_MEAN_CRITERION.md']
result=dict(completed_utc=now(),device='CPU',threads=4,threshold=.85,seed=202611070252,n_audited_pool=len(accepted),n_final_training_groups=60,baseline_target_filter_pending=True,total_candidate_groups=len(keys),reference_counts=dict(collections.Counter(r['group']for r in refs)),reference_windows=len(texts),window_policy='254 content tokens+2special=256; stride200; full text coverage; both sides vs all references, other accepted groups only',max_reference_cosine=max(c['max_reference_cosine']for c in checks),max_other_selected_cosine=max(c['max_other_selected_group_cosine']for c in checks),rejected_reason_counts=dict(collections.Counter(r['reason']for r in rejected)),checks=checks,rejected=rejected,source_tsv=str(source),source_tsv_sha256=sha(source),manifest_sha256=sha(manifest),embedding_model=snap,source_hashes={p:sha(B/p)for p in sourcefiles},audit_script_sha256=sha(Path(__file__)),no_intervention_training_started=True)
atomic(O/'style_data_audit.json',result);pulse('complete',accepted=len(accepted),audit_sha256=sha(O/'style_data_audit.json'))
with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(now()+' STYLE_DATA_AUDIT_CPU_COMPLETE pool='+str(len(accepted))+' exact+full-windowembedding0.85 passed, refs include val296/docs250/keep60/train_strat+legal400/WJBharm300; maxref='+str(result['max_reference_cosine'])+'; baseline target filter and final60 selection pending, no intervention training. auditSHA='+sha(O/'style_data_audit.json')+'\n')
print('AUDIT_COMPLETE',len(accepted),result['max_reference_cosine'],result['max_other_selected_cosine'],flush=True)
