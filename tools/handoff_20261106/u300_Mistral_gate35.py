from pathlib import Path
import os,sys,json,hashlib,datetime,time,gc
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T));from batched_injection300 import generate_batch_with_injection
L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
mode=sys.argv[1];assert mode in ['initial','B4_long'];P=L(U/'Mistral_gate35_plan.json');assert H(__file__)==P['worker_sha256'];assert H(T/'batched_injection300.py')==P['batch_core_sha256'];I=U/'Mistral_gate35_inputs.private.json';assert H(I)==P['inputs_sha256'];rows=L(I);assert len(rows)==104;D=U/'Mistral_gate35';lease=Path(os.environ['DEF_LEASE_DIR']);mp=Path(P['model_path'])
for n,h in P['model_files_sha256'].items():assert H(mp/n)==h
tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();ids=[tok.apply_chat_template([dict(role='user',content=r['prompt'])],add_generation_prompt=True) for r in rows];vectors={}
for c,s in P['vectors'].items():
 assert H(R/s['path_relative'])==s['sha256'];v=np.load(R/s['path_relative']).astype(np.float32);vectors[c]=v*np.float32(1.5)
vectors['alpha0']=np.zeros(model.config.hidden_size,dtype=np.float32)
def group(cap,B,c):
 folder=D/f'cap{cap}'/f'B{B}'/c;limit=104 if B==8 else 100
 if (folder/'complete.json').exists():return True
 if (folder/'memory_failed.json').exists():return False
 for k in range(0,limit,B):
  ix=list(range(k,min(k+B,limit)));paths=[folder/'generation.private'/f'{i:04d}.json' for i in ix]
  if all(p.exists() for p in paths):continue
  torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();tick=time.monotonic();zs=None;failed=None
  try:
   zs=generate_batch_with_injection(model,tok,[ids[i] for i in ix],vectors[c],layer=9,max_new_tokens=cap,alpha=0 if c=='alpha0' else 1.5)
   free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();head=total-outside-torch.cuda.max_memory_reserved();assert head>=3*1024**3,'peak headroom below3GiB'
  except (torch.OutOfMemoryError,AssertionError) as e:failed=dict(type=type(e).__name__,message=str(e)[:240],rows=ix);zs=None
  if failed:
   gc.collect();torch.cuda.empty_cache();save(folder/'memory_failed.json',dict(utc=utc(),cap=cap,B=B,condition=c,**failed));return False
  for i,z,p in zip(ix,zs,paths):
   expected=float(np.linalg.norm(vectors[c].astype(np.float64)));assert z['injection_count']==1;assert abs(z['rho_runtime']-expected)<=1e-7 if expected==0 else abs(z['rho_runtime']-expected)/expected<=.01
   save(p,dict(id=i,condition=c,alpha=0 if c=='alpha0' else 1.5,cap=cap,B=B,selected=i<100,result=z,headroom_GiB=head/1024**3,plan_sha256=H(U/'Mistral_gate35_plan.json'),device_uuid=str(torch.cuda.get_device_properties(0).uuid)))
  save(lease/'live.json',dict(utc=utc(),cap=cap,B=B,condition=c,N=min(k+B,limit),selected_N=min(k+B,100),total_selected=100,no_judge_statistics_read=True))
 save(folder/'complete.json',dict(utc=utc(),N_selected=100,N_covered=limit,record_sha256={p.name:H(p) for p in (folder/'generation.private').glob('*.json')}));return True
def packet(cap,batches,wave):
 pack=[]
 for B in batches:
  for c in ['alpha0','s3','61000']:
   folder=D/f'cap{cap}'/f'B{B}'/c;assert (folder/'complete.json').exists()
   for i,r in enumerate(rows[:100]):
    gp=folder/'generation.private'/f'{i:04d}.json';z=L(gp);response=z['result']['text'];ph=hashlib.sha256(r['prompt'].encode()).hexdigest();pack.append(dict(id=f'{cap}:B{B}:{c}:{i}',model='mistral',family='engineering_Mistral_gate35',condition=f'cap{cap}_B{B}_{c}',prompt=r['prompt'],behavior=r['prompt'],response=response,prompt_sha256=ph,behavior_sha256=ph,response_sha256=hashlib.sha256(response.encode()).hexdigest(),generation_sha256=H(gp),preprocessing_sha256=None))
 W=U/'score_waves'/wave;save(W/'inputs.private.json',pack);save(W/'manifest.json',dict(utc=utc(),N=len(pack),judges=['WG'],inputs_sha256=H(W/'inputs.private.json'),scope='engineering label gate only; not alpha selection',cap=cap,batches=batches));save(D/(wave+'_ready.json'),dict(utc=utc(),wave=wave,N=len(pack)))
if mode=='initial':
 short_batches=[1]
 for c in ['alpha0','s3','61000']:assert group(120,1,c),'B1 short memory gate failed'
 for B in [8,4]:
  ok=all(group(120,B,c) for c in ['alpha0','s3','61000'])
  if ok:short_batches.append(B)
 packet(120,short_batches,'Mistral_gate35_short')
 refs=L(U/'Mistral_gate35_reference20.private.json');checks=[]
 for c in ['alpha0','s3']:
  for i in range(20):
   p=D/'cap120/B8'/c/'generation.private'/f'{i:04d}.json'
   if p.exists():checks.append(dict(condition=c,id=i,byte_equal=L(p)['result']['text']==refs[c][i]['text']))
 save(D/'node_reference20.json',dict(utc=utc(),N=len(checks),passed=len(checks)==40 and all(r['byte_equal'] for r in checks),checks=checks,scope='same alpha0 and s3 alpha1.5 B8 first20 versus node calibration,120 tokens'))
 # Preserve the cap120 result independently. A failed cross-site reference blocks long admission.
 if not L(D/'node_reference20.json')['passed']:sys.exit(2)
 for c in ['alpha0','s3','61000']:assert group(2400,1,c),'B1 long memory gate failed'
 long_batches=[1];candidate=None
 for B in [8,4]:
  if all(group(2400,B,c) for c in ['alpha0','s3','61000']):long_batches.append(B);candidate=B;break
 packet(2400,long_batches,'Mistral_gate35_long')
 save(D/'initial_complete.json',dict(utc=utc(),candidate_by_memory=candidate,B1_baseline_complete=True))
else:
 if all(group(2400,4,c) for c in ['alpha0','s3','61000']):packet(2400,[1,4],'Mistral_gate35_long_B4');save(D/'B4_long_complete.json',dict(utc=utc(),complete=True))
