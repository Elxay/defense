"""Addendum8: extra fixed random directions; no effect analysis in this worker."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,socket,sys,time
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
B=Path('/data/HZX/Def');sys.path.insert(0,str(B/'src'))
from gen.common import generate_with_injection
p=argparse.ArgumentParser();p.add_argument('--seed',type=int,choices=[2,3],required=True);p.add_argument('--physical-card',type=int,choices=[2,3],required=True);a=p.parse_args()
assert os.environ.get('CUDA_VISIBLE_DEVICES')==str(a.physical_card)
O=B/'results/audit/handoff_round6';OP=B/f'results/audit/WJB_rand{a.seed}.json';MP=OP.with_suffix('.metadata.json');HP=O/f'rand{a.seed}_heartbeat.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(p,d):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,ensure_ascii=False)+'\n');os.replace(t,p)
def heartbeat(phase,n,**extra):
 atomic(HP,dict(utc=now(),phase=phase,pid=os.getpid(),host=socket.gethostname(),physical_card=a.physical_card,random_seed=a.seed,n=n,total=300,**extra));print(json.dumps(dict(utc=now(),phase=phase,n=n,**extra)),flush=True)
manifest=B/'configs/stage0_data/wjb300.json';rows=json.loads(manifest.read_text());assert len(rows)==300 and len({r['id']for r in rows})==300
snapshot=B.parent.parent/'huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659'
snapshot=Path('/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659')
rng=np.random.default_rng(a.seed);v=rng.normal(size=4096).astype('float32');v=v/np.linalg.norm(v)*5.21
meta=dict(random_seed=a.seed,vector_sha256=hashlib.sha256(v.tobytes()).hexdigest(),vector_norm=float(np.linalg.norm(v)),manifest_sha256=sha(manifest),common_generator_sha256=sha(B/'src/gen/common.py'),generator_sha256=sha(Path(__file__)),addendum8_sha256=sha(B/'docs/239_ADDENDUM8_RANDOM_REFERENCES.md'),host=socket.gethostname(),physical_card=a.physical_card,model_snapshot=str(snapshot),max_new_tokens=2400,layer=9,batch_size=1,device='cuda:0')
if MP.exists():assert json.loads(MP.read_text())==meta,'resume metadata changed'
else:assert not OP.exists(),'unproven existing outputs';atomic(MP,meta)
out=json.loads(OP.read_text())if OP.exists()else{}
assert set(out)<={r['id']for r in rows}
heartbeat('loading_model',len(out))
torch.cuda.set_device(0);tok=AutoTokenizer.from_pretrained(snapshot,local_files_only=True);mdl=AutoModelForCausalLM.from_pretrained(snapshot,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval()
t0=time.monotonic();started=now();first25=None;initial=len(out);fresh=0
heartbeat('generating',len(out),generation_started_utc=started)
for r in rows:
 if r['id']in out:continue
 ids=tok.apply_chat_template([{'role':'user','content':r['adversarial']}],add_generation_prompt=True,return_tensors='pt').to('cuda:0')
 z=generate_with_injection(mdl,tok,ids,v,layer=9,max_new_tokens=2400,device='cuda:0')
 assert z['injection_count']==1 and abs(z['delta_norm_runtime']-5.21)<.05
 out[r['id']]=dict(behavior=r['vanilla'],text=z['text'],new_tokens=z.get('new_tokens'),injection_count=z.get('injection_count'),rho_runtime=z.get('delta_norm_runtime'),host=socket.gethostname())
 fresh+=1;elapsed=time.monotonic()-t0
 atomic(OP,out)
 if fresh==25:
  first25=elapsed/25
  atomic(O/f'rand{a.seed}_first25.json',dict(utc=now(),seconds=elapsed,seconds_per_item=first25,remaining_seconds_estimate=(300-len(out))*first25,estimated_finish_utc=datetime.datetime.fromtimestamp(time.time()+(300-len(out))*first25,datetime.timezone.utc).isoformat(),includes_model_loading=False,resume_initial_n=initial))
 heartbeat('generating',len(out),generation_started_utc=started,elapsed_generation_seconds=elapsed,first25_seconds_per_item=first25)
assert len(out)==300
heartbeat('complete',300,generation_seconds=time.monotonic()-t0,source_sha256=sha(OP),first25_seconds_per_item=first25)
print('WJB_RAND_DONE',a.seed,300,flush=True)
