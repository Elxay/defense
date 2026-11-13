from pathlib import Path
import os,sys,json,hashlib,datetime
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T));from batched_injection300 import generate_batch_with_injection
L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'encoding_alpha0_plan_v2.json');spec=P['models']['qwen'];assert spec['batch_size']==4;O=U/'followup35/encoding_probe';mp=spec['model_paths']['innet'];tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();zero=np.zeros(model.config.hidden_size,dtype=np.float32);checks=[];overlap=[];complete=[]
for f in ['ascii','caesar','morse','atbash']:
 cfg=spec['families'][f];raw=L(U/cfg['input_file'])['qwen'][f];by={str(r['id']):r for r in raw};old=U/'encoding_alpha0_generated/qwen'/f/'alpha0/generation.private';new=U/'encoding_alpha0_generated_v2/qwen'/f/'alpha0/generation.private';A={p.name:p for p in old.glob('*.json')};B={p.name:p for p in new.glob('*.json')};assert len(A)==440 and len({L(p)['id'] for p in A.values()})==440
 for p in A.values():
  z=L(p);assert z['prompt_sha256']==by[str(z['id'])]['prompt_sha256'];assert z['result']['injection_count']==1 and z['result']['rho_runtime']==0
 common=sorted(set(A)&set(B));assert f!='ascii' or len(common)>=40
 overlap.extend(dict(family=f,id=L(A[n])['id'],byte_equal=L(A[n])['result']['text']==L(B[n])['result']['text']) for n in common)
 selected=set(cfg['ordered_IDs'][:5])
 for members in cfg['batches']:
  if not selected.intersection(members):continue
  rows=[by[i] for i in members];torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();zs=generate_batch_with_injection(model,tok,[r['input_ids'] for r in rows],zero,layer=spec['layer'],max_new_tokens=2400,positions=[r['position'] for r in rows],alpha=0)
  free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();head=total-outside-torch.cuda.max_memory_reserved();assert head>=3*1024**3
  for r,z in zip(rows,zs):
   assert z['injection_count']==1 and z['rho_runtime']==0;p=old/f"{r['id']:04d}.json";eq=z['text']==L(p)['result']['text'];checks.append(dict(family=f,id=r['id'],selected=str(r['id']) in selected,byte_equal=eq,source_v1_sha256=H(p),headroom_GiB=head/1024**3));save(O/'observed.private'/f/f"{r['id']:04d}.json",z)
 complete.append(dict(family=f,N=440,record_sha256={p.name:H(p) for p in A.values()}))
 save(O/'progress.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),families_done=len(complete),total=4))
save(O/'result.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=all(r['byte_equal'] for r in checks+overlap),N_selected=sum(r['selected'] for r in checks),N_covered=len(checks),checks=checks,overlap=overlap,legacy_complete=complete,model='qwen',B=4,cap=2400,no_judge_labels_read=True))
