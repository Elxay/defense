"""Regenerate the eight fixed ambiguous legal items using original batch composition."""
import argparse,ast,datetime,hashlib,json,os,time
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round12';P=B/'results/audit/handoff_round11';T=B/'results/style_retrained'
a=argparse.ArgumentParser();a.add_argument('--card',type=int,required=True);a=a.parse_args()
assert os.environ['CUDA_VISIBLE_DEVICES']==str(a.card) and a.card in (2,3)
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,d):
 p=O/name;q=p.with_suffix('.tmp');q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def pulse(phase,n):
 save('legal400_live.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),physical_gpu=a.card,host='innet',phase=phase,n=n,total=8))
mapping=load(P/'legal_recall_blind60_mapping.json')['items'];review=load(P/'legal_recall_blind60_review.json')['items'];ids=[r['blind_id'] for r in review if r['category']=='U'];assert len(ids)==8
legal=load(B/'data/legal_val_items.json');positions={x['key']:i for i,x in enumerate(legal)};assert len(positions)==400
source=B/'src/eval/legal_val_batch.py'
snapshot='/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659'
pulse('loading',0);tok=AutoTokenizer.from_pretrained(snapshot,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
mdl=AutoModelForCausalLM.from_pretrained(snapshot,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval();mdl.config.use_cache=True
def build(cap):
 fn=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='run_batch')
 change=[n for n in ast.walk(fn) if isinstance(n,ast.keyword) and n.arg=='max_new_tokens'];assert len(change)==1 and change[0].value.value==120;change[0].value.value=cap
 scope=dict(torch=torch,tok=tok,mdl=mdl,DEV='cuda:0',LAYER=9);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),scope);return scope
f120,f400=map(build,(120,400));cache={};rows=[]
for k in ids:
 m=mapping[k];pos=positions[m['key']];off=pos//8*8;batch=[(off+i,r['group'],r['prompt']) for i,r in enumerate(legal[off:off+8])]
 assert batch[pos-off][2]==m['prompt']
 name=('repeatA_s3' if m['seed']==3 else f'control_s{m["seed"]}') if m['arm']=='control' else f'treatment_s{m["seed"]}'
 p=T/name/'v.npy';v=np.load(p).astype('float32');v=v/np.linalg.norm(v)*(5.21*m['alpha'])
 sig=(name,m['alpha'],off); original=load(B/m['source_file'])['metadata'];assert original['vector_sha256']==sha(p)
 if sig not in cache:
  f120['vec']=f400['vec']=v;cache[sig]=(f120['run_batch'](batch),f400['run_batch'](batch))
 x,y=[v[pos-off] for v in cache[sig]]
 rows.append(dict(blind_id=k,prompt=m['prompt'],original120=m['text'],reproduced120=x,generated400=y,
                  original120_exact=x==m['text'],prefix400_matches_original=y.startswith(m['text']),
                  original_sha256=m['text_sha256'],batch_offset=off,n_chars_400=len(y),original_host=original['host'],
                  original_card=original['physical_card'],runid=name,alpha=m['alpha'],vector_sha256=sha(p)))
 save('legal400_private.json',dict(worker_sha256=sha(Path(__file__)),batch_source_sha256=sha(source),items=rows))
 pulse('regenerating',len(rows))
pulse('complete',8)
