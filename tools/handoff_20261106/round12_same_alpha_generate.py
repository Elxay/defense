"""Separate, resumable same-alpha benign sensitivity, fixed s3/s5."""
import argparse,datetime,hashlib,json,os,socket,sys,time
from pathlib import Path
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
p=argparse.ArgumentParser();p.add_argument('--seed',type=int,choices=[3,5],required=True);a=p.parse_args()
B=Path('/home/dell/Def');O=B/'results/audit/handoff_round12';O.mkdir(parents=True,exist_ok=True)
card={3:0,5:2}[a.seed];assert os.environ['CUDA_VISIBLE_DEVICES']==str(card)
sys.path.insert(0,str(B/'src'));from gen.common import generate_with_injection
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc)
def save(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');q.replace(p)
add=B/'docs/252_ADDENDUM5_SAME_ALPHA_PAIRS.md';assert sha(add)=='1d9422f8f86ca463b8e222bf064126aa986eb5d36650d1128da90ba5e9552749'
pairs=B/'configs/stage0_data/wjb_benign246_pairs300.json'
rows=[(r['id']+'|'+s,r[s]) for r in json.loads(pairs.read_text()) for s in ('vanilla','adversarial')];assert len(rows)==600 and len(dict(rows))==600
vp=B/f'results/style_retrained/treatment_s{a.seed}/v.npy';v=np.load(vp).astype('float32');v=v/np.linalg.norm(v)*5.21
snapshot='/data/ray/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659'
sig=dict(seed=a.seed,alpha=1.,norm=5.21,max_new_tokens=120,worker_sha256=sha(Path(__file__)),addendum5_sha256=sha(add),vector_sha256=sha(vp),manifest_sha256=sha(pairs),generation_sha256=sha(B/'src/gen/common.py'),model_snapshot=Path(snapshot).name,host=socket.gethostname(),physical_gpu=card,baseline_file='results/audit/WJB_BENIGN246_alpha0.json')
out=O/f'same_alpha_s{a.seed}_pairs600.private.json';d=json.loads(out.read_text()) if out.exists() else dict(metadata=sig,items={})
assert d['metadata']==sig and set(d['items'])<=set(dict(rows))
initial=len(d['items']);start=time.monotonic()
def pulse(phase):
 n=len(d['items']);save(O/f'same_alpha_s{a.seed}_live.json',dict(utc=now().isoformat(),pid=os.getpid(),physical_gpu=card,phase=phase,n=n,total=600,seconds_per_item=(time.monotonic()-start)/(n-initial) if n>initial else None))
pulse('loading');tok=AutoTokenizer.from_pretrained(snapshot,local_files_only=True)
mdl=AutoModelForCausalLM.from_pretrained(snapshot,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval();mdl.config.use_cache=True
start=time.monotonic()
for key,prompt in rows:
 assert now()<datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc)
 if key in d['items']:continue
 ids=tok.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True,return_tensors='pt').to('cuda:0')
 d['items'][key]=generate_with_injection(mdl,tok,ids,v,layer=9,max_new_tokens=120,device='cuda:0');pulse('pairs600')
 if len(d['items'])%10==0:save(out,d)
save(out,d);pulse('complete')
