"""Frozen Mistral B8 calibration; alpha is applied to the vector before injection."""
from pathlib import Path
import os,sys,json,hashlib,datetime,time
import numpy as np,torch
from transformers import AutoTokenizer,AutoModelForCausalLM
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T))
from batched_injection300 import generate_batch_with_injection
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def L(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'Mistral_calibration32_plan.json');assert H(__file__)==P['worker_sha256'];assert H(T/'batched_injection300.py')==P['batch_core_sha256'];I=Path(P['input_path']);assert H(I)==P['input_sha256'];raw=L(I);rows=raw if isinstance(raw,list) else raw.get('rows') or raw.get('items');assert len(rows)==700
lease=Path(os.environ['DEF_LEASE_DIR']);D=Path(P['output_root']);spec=P['model'];mp=Path(spec['path'])
for n,h in spec['files_sha256'].items():assert H(mp/n)==h
tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left';tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();B=8;cap=120
V={}
for s,z in P['vectors'].items():
 assert H(z['path'])==z['sha256'];V[s]=np.load(z['path']).astype(np.float32);assert abs(float(np.linalg.norm(V[s].astype(np.float64)))-z['norm'])<1e-6
zero=np.zeros(model.config.hidden_size,dtype=np.float32)
def generate(indices,vec,alpha):
 prompts=[rows[i].get('prompt') or rows[i].get('text') for i in indices];ids=[tok.apply_chat_template([dict(role='user',content=p)],add_generation_prompt=True) for p in prompts]
 out=generate_batch_with_injection(model,tok,ids,vec,layer=9,max_new_tokens=cap,positions=[len(x)-1 for x in ids],alpha=alpha,source_vector_sha256=None)
 expected=float(np.linalg.norm(vec.astype(np.float64)))
 for z in out:
  assert z['injection_count']==1
  assert abs(z['rho_runtime']-expected)<1e-7 if expected==0 else abs(z['rho_runtime']-expected)/expected<=.01
  z['rho_expected']=expected;z['rho_relative_error']=abs(z['rho_runtime']-expected)/expected if expected else 0
 return out
# Same-vector alpha1 and alpha0 must reproduce known legacy rows before fresh sweep.
gate=D/'reference20.json'
if not gate.exists():
 checks=[]
 for c,vec in [('alpha0',zero),('s3_a1.00',V['3'])]:
  ref=Path(P['legacy_reference_root'])/(c+'.json');assert H(ref)==P['legacy_reference_sha256'][c];old=L(ref)['items']
  for begin in range(0,24,8):
   idx=list(range(begin,begin+8));zs=generate(idx,vec,0 if c=='alpha0' else 1)
   for i,z in zip(idx,zs):checks.append(dict(condition=c,id=i,selected=i<20,byte_equal=z['text'].encode()==old[str(i)]['text'].encode()))
 save(gate,dict(utc=utc(),passed=all(z['byte_equal'] for z in checks),checks=checks,selected_pairs=sum(z['selected'] for z in checks),scope='20 selected rows per alpha0 and true-alpha1; full fixed B8 batches'))
assert L(gate)['passed'],'Reference byte gate failed; no calibration sweep admitted'
conditions=[('alpha0',None,0.)]+[(f's{s}_a{a:.2f}',s,a) for s in [3,4,5] for a in P['alpha_grid']]
for c,s,a in conditions:
 folder=D/c
 if (folder/'complete.json').exists():continue
 vec=zero if s is None else (V[str(s)]*np.float32(a)).astype(np.float32)
 expected=0 if s is None else P['vectors'][str(s)]['norm']*a;assert abs(float(np.linalg.norm(vec.astype(np.float64)))-expected)<1e-5
 for begin in range(0,700,B):
  indices=list(range(begin,min(begin+B,700)));paths=[folder/'generation.private'/f'{i:04d}.json' for i in indices]
  if all(p.exists() for p in paths):continue
  if (lease/'yield.request').exists():save(lease/'yielded.json',dict(utc=utc(),condition=c,before_row=begin));sys.exit(75)
  out=generate(indices,vec,a)
  for i,z,p in zip(indices,out,paths):
   save(p,dict(id=i,source_row_id=rows[i].get('id'),condition=c,alpha=a,result=z,plan_sha256=H(U/'Mistral_calibration32_plan.json'),source_vector_sha256=None if s is None else P['vectors'][str(s)]['sha256']))
  save(lease/'live.json',dict(utc=utc(),condition=c,N=min(begin+B,700),total=700,alpha=a,rho_expected=float(np.linalg.norm(vec.astype(np.float64))),no_labels_or_selection_read=True))
 files={p.name:H(p) for p in (folder/'generation.private').glob('*.json')};assert len(files)==700;save(folder/'complete.json',dict(utc=utc(),N=700,record_sha256=files,plan_sha256=H(U/'Mistral_calibration32_plan.json')))
save(D/'complete22.json',dict(utc=utc(),N_conditions=22,N_rows=15400,plan_sha256=H(U/'Mistral_calibration32_plan.json'),main_test_admitted=False,selection_read_admitted=False))
