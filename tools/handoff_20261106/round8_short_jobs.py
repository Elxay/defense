from pathlib import Path
import argparse,os,sys,json,hashlib,datetime,time,socket
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['reread400','cross20'],required=True);p.add_argument('--root',required=True);a=p.parse_args();B=Path(a.root);O=B/'results/audit/handoff_round8';O.mkdir(exist_ok=True);sys.path.insert(0,str(B/'src'))
from gen.common import generate_with_injection
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(p,d):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def pulse(phase,n,**kw):atomic(O/(a.mode+'_live.json'),dict(utc=now(),pid=os.getpid(),phase=phase,n=n,physical_gpu=2,host=socket.gethostname(),**kw))
if a.mode=='reread400':
 pkg=json.loads((B/'results/audit/handoff_round6/doc246_adv52_pending_fullread.json').read_text())['items'];labels=json.loads((B/'results/audit/handoff_round7/doc246_adv_review_labels.json').read_text());rows=[r for i,r in enumerate(pkg)if labels[str(i)]['category']=='U'];assert len(rows)==9
 vector=np.load(B/'results/audit/runs/block10_keep60_s0/v.npy').astype('float32');vector=vector/np.linalg.norm(vector)*5.21
 snapshot=Path('/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659');target=O/'doc246_U9_reread400.json'
else:
 expected=json.loads((O/'cross20_expected.json').read_text());assert sha(B/'src/gen/common.py')==expected['common_sha256']and sha(B/'configs/stage0_data/wjb300.json')==expected['manifest_sha256']
 rows=json.loads((B/'configs/stage0_data/wjb300.json').read_text())[:20];rng=np.random.default_rng(2);vector=rng.normal(size=4096).astype('float32');vector=vector/np.linalg.norm(vector)*5.21;assert hashlib.sha256(vector.tobytes()).hexdigest()==expected['array_sha256']
 snapshot=Path('/data/ray/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659');target=O/'rand2_crossnode20.json'
assert not target.exists(),'do not overwrite an existing run';pulse('loading',0);tok=AutoTokenizer.from_pretrained(snapshot,local_files_only=True);mdl=AutoModelForCausalLM.from_pretrained(snapshot,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval();out=[];begin=time.monotonic()
for r in rows:
 prompt=r['request']if a.mode=='reread400'else r['adversarial'];ids=tok.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True,return_tensors='pt').to('cuda:0')
 if a.mode=='reread400':
  r120=generate_with_injection(mdl,tok,ids,vector,layer=9,max_new_tokens=120,device='cuda:0');res=generate_with_injection(mdl,tok,ids,vector,layer=9,max_new_tokens=400,device='cuda:0');item=dict(id=r['id'],request=prompt,old120_text=r['text'],repeat120_text=r120['text'],repeat120_matches=r120['text'].encode()==r['text'].encode(),text400=res['text'],metadata400={k:v for k,v in res.items()if k!='text'},old120_sha256=r['text_sha256'],text400_sha256=hashlib.sha256(res['text'].encode()).hexdigest())
 else:
  res=generate_with_injection(mdl,tok,ids,vector,layer=9,max_new_tokens=2400,device='cuda:0');old=expected['items'][r['id']]['text'];item=dict(id=r['id'],text=res['text'],text_sha256=hashlib.sha256(res['text'].encode()).hexdigest(),reference_sha256=hashlib.sha256(old.encode()).hexdigest(),byte_equal=res['text'].encode()==old.encode(),new_tokens=res['new_tokens'],injection_count=res['injection_count'])
 assert res['injection_count']==1 and abs(res['delta_norm_runtime']-5.21)<.05
 out.append(item);atomic(target,dict(mode=a.mode,host=socket.gethostname(),script_sha256=sha(Path(__file__)),common_sha256=sha(B/'src/gen/common.py'),items=out));pulse('generating',len(out),total=len(rows),seconds_per_item=(time.monotonic()-begin)/len(out));print(a.mode,'DONE',len(out),'/',len(rows),flush=True)
pulse('complete',len(out),total=len(rows),seconds_per_item=(time.monotonic()-begin)/len(out),output_sha256=sha(target));print('ALL_DONE',flush=True)
