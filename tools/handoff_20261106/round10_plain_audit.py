"""CPU-only, full-window group audit before any intervention training."""
import os
os.environ.update(OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1')
from pathlib import Path
import csv,json,sys,re,unicodedata,hashlib,datetime,time,collections
import numpy as np,torch
from sentence_transformers import SentenceTransformer
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round10';torch.set_num_threads(4)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(p,d):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def norm(t):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',t).casefold()).strip()
def pulse(phase,**kw):atomic(O/'style_audit_live.json',dict(utc=now(),pid=os.getpid(),phase=phase,device='CPU',**kw))
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
style=json.loads((B/'results/style_retrained/style_training_targets.json').read_text())
for r in style['items']:
 for side in ['vanilla','adversarial']:ref('wrapped_training60',r['id']+':'+side,r[side])
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

source=sorted(Path('/data/huggingface/hub/datasets--allenai--wildjailbreak/snapshots').glob('*/train/train.tsv'))[0];csv.field_size_limit(sys.maxsize);groups={}
with source.open(newline='')as f:
 for i,r in enumerate(csv.DictReader(f,delimiter='\t')):
  if r['data_type']=='vanilla_benign'and r.get('vanilla'):
   key=norm(r['vanilla'])
   if key not in groups:groups[key]=dict(id=f'wjb_plain_{i}',source_row=i,text=r['vanilla'],group_sha256=hashlib.sha256(key.encode()).hexdigest())
keys=sorted(groups);rng=np.random.default_rng(202611070253);accepted=[];checks=[];rejected=[];selected_emb=None;t0=time.monotonic()
for index in rng.permutation(len(keys)):
 key=keys[index];r=groups[key]
 if key in refnorm:rejected.append(dict(id=r['id'],reason='exact_reference'));continue
 pieces,ranges=windows(r['text']);lengths=[len(tok.encode(p,add_special_tokens=True))for p in pieces];assert max(lengths)<=256,'unexpected embedding re-truncation'
 emb=model.encode(pieces,normalize_embeddings=True,batch_size=32,convert_to_numpy=True,show_progress_bar=False);sim=emb@refemb.T;maxref=float(sim.max());scores=np.full(len(refs),-np.inf);np.maximum.at(scores,refindex,sim.max(axis=0));top=np.argsort(scores)[-5:][::-1];internal=float((emb@selected_emb.T).max())if selected_emb is not None else -1.
 record=dict(id=r['id'],max_reference_cosine=maxref,max_other_group_cosine=internal,top5=[dict(reference=refs[i]['id'],cosine=float(scores[i]))for i in top],token_ranges=ranges,max_submitted_tokens=max(lengths))
 if max(maxref,internal)>=.85:rejected.append(dict(**record,reason='embedding_reference'if maxref>=.85 else'embedding_other_group'))
 else:accepted.append(r);checks.append(record);selected_emb=emb if selected_emb is None else np.concatenate([selected_emb,emb])
 if len(accepted)%20==0:pulse('auditing_plain',accepted=len(accepted),rejected=len(rejected),elapsed_seconds=time.monotonic()-t0)
 if len(accepted)==240:break
assert len(accepted)==240,'insufficient audited plain buffer; stop'
manifest=O/'plain_audited_pool.json';assert not manifest.exists();atomic(manifest,accepted)
result=dict(completed_utc=now(),device='CPU',seed=202611070253,n_pool=240,n_final_required=120,reference_counts=dict(collections.Counter(r['group']for r in refs)),reference_windows=len(texts),threshold=.85,max_reference_cosine=max(r['max_reference_cosine']for r in checks),max_other_group_cosine=max(r['max_other_group_cosine']for r in checks),checks=checks,rejected=rejected,rejected_reason_counts=dict(collections.Counter(r['reason']for r in rejected)),pool_sha256=sha(manifest),addendum3_sha256=sha(B/'docs/252_ADDENDUM3_PLAIN_ARM_INTERPOLATION.md'),model_snapshot=snap,script_sha256=sha(Path(__file__)),source_sha256=sha(source))
atomic(O/'plain_data_audit.json',result)
with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(now()+' PLAIN_ARM_CPU_AUDIT_COMPLETE pool240 refs='+str(result['reference_counts'])+' maxref='+str(result['max_reference_cosine'])+' maxinternal='+str(result['max_other_group_cosine'])+' auditSHA='+sha(O/'plain_data_audit.json')+'; no plainarm optimization yet.\n')
pulse('complete',n_pool=240,audit_sha256=sha(O/'plain_data_audit.json'));print('PLAIN_AUDIT_COMPLETE',flush=True)
