from pathlib import Path
import json,hashlib,datetime,statistics,csv,io,subprocess,shlex
import numpy as np
from transformers import AutoTokenizer
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';O=U/'takeover30';O.mkdir(exist_ok=True)
def L(p):return json.loads(p.read_text())
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,z):p.write_text(json.dumps(z,indent=2,ensure_ascii=False)+'\n')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
P=L(U/'ready_generation_CF20.json');tok={m:AutoTokenizer.from_pretrained(s['model_paths']['innet'],local_files_only=True) for m,s in P['models'].items()}
def stat(a):return dict(N=len(a),median=float(np.median(a)) if a else None,p90=float(np.percentile(a,90)) if a else None,mean=float(np.mean(a)) if a else None,SD=float(np.std(a,ddof=1)) if len(a)>1 else None,min=min(a) if a else None,max=max(a) if a else None)
def ids_sha(a):return hashlib.sha256(json.dumps(a,separators=(',',':')).encode()).hexdigest()
def retoken(m,z):
 a=tok[m].encode(z['text'],add_special_tokens=False);exact=ids_sha(a)==z.get('generated_ids_sha256')
 if not exact and z.get('eos'):
  for end in set(tok[m].all_special_ids):
   if ids_sha(a+[end])==z.get('generated_ids_sha256'):return a+[end],True
 return a,exact
def compare(m,aa,bb):
 allpos=[];changed=[];equal=0;exactpairs=0;rows=[]
 for key in sorted(set(aa)&set(bb),key=str):
  a,ea=retoken(m,aa[key]['result']);b,eb=retoken(m,bb[key]['result']);exactpairs+=int(ea and eb)
  pos=next((i+1 for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
  if pos is None and len(a)!=len(b):pos=min(len(a),len(b))+1
  if pos is None:equal+=1
  else:changed.append(pos)
  rows.append(dict(id=key,first_divergence_1based=pos,hash_verified_original_tokenization=ea and eb))
 return dict(N=len(rows),unchanged=equal,changed=len(changed),first_divergence_among_changed=stat(changed),exact_hash_verified_pairs=exactpairs,measurement='Recovered token IDs where SHA verifies, otherwise decoded-text re-tokenization; EOS attempted against all special IDs. Equal rows have no finite divergence, not zero.',rows=rows)
out=[]
for m in ['llama','qwen']:
 for f in ['translate-fr','translate-zh-cn']:
  d=U/'ready_generated_CF20'/m/f;aa={L(p)['id']:L(p) for p in (d/'alpha0/generation.private').glob('*.json')}
  for c in P['condition_order'][m]:
   if c=='alpha0':continue
   bb={L(p)['id']:L(p) for p in (d/c/'generation.private').glob('*.json')};assert len(aa)==len(bb)==440
   z=compare(m,aa,bb);out.append(dict(model=m,family=f,condition=c,group='learned' if c.startswith('s') else 'random',**z))
a=U/'acceptance/llama/generation.private/cap2400/alpha0/candidate_batch';b=U/'acceptance_v2/llama/generation.private/cap2400/alpha0/candidate_batch';aa={L(p)['id']:L(p) for p in a.glob('*.json')};bb={L(p)['id']:L(p) for p in b.glob('*.json')};noise=compare('llama',aa,bb);noise.update(batch_pair=[16,8],source_dirs=[str(a),str(b)],different_prompt_panel_from_language=True)
report=dict(utc=utc(),scope='CPU output-byte/token diagnostic, no judge labels',language=out,batch_noise=noise)
save(O/'first_divergence.json',report)
print('DIVERGENCE',json.dumps([dict(model=z['model'],family=z['family'],condition=z['condition'],N=z['N'],changed=z['changed'],median=z['first_divergence_among_changed']['median'],exact=z['exact_hash_verified_pairs']) for z in out]))
print('NOISE',json.dumps({k:v for k,v in noise.items() if k!='rows'}))
# Metadata-only timing and record validity for all existing Indian alpha0 sources.
existing=[]
for m,f,d,planfile in [('llama','translate-ml',U/'ready_generated_B4_ml/llama/translate-ml/alpha0',U/'ready_generation_plan_B4_ml.json'),('llama','translate-ta',U/'ready_generated_B4_ta/llama/translate-ta/alpha0',U/'ready_generation_plan_B4_ta.json'),('llama','translate-mr',U/'ready_generated/llama/translate-mr/alpha0',U/'ready_generation_plan.json')]+[('qwen',f,U/'language_alpha0/qwen'/f,U/'language_alpha0_execution_plan.json') for f in ['translate-ml','translate-mr','translate-ta']]:
 files=sorted((d/'generation.private').glob('*.json'));records=[L(p) for p in files];assert len(records)==440 and len({r['id'] for r in records})==440
 hashes={r['signature'].get('plan_sha256',r['signature'].get('execution_plan_sha256')) for r in records};assert hashes=={H(planfile)}
 marker=next((d/n for n in ['complete.json','generation_complete.json'] if (d/n).exists()),None);meta=L(marker);metrics=[L(p) for p in (d/'metrics').glob('*.json')];starts=[datetime.datetime.fromisoformat(z['utc'])-datetime.timedelta(seconds=z['elapsed_seconds']) for z in metrics];finish=datetime.datetime.fromisoformat(meta['utc']);first=min(starts)
 existing.append(dict(model=m,family=f,records=440,parseable=440,unique_IDs=440,complete_marker=str(marker),complete_marker_sha256=H(marker),plan_file=str(planfile),plan_sha256=H(planfile),output_root=str(d),physical_resolved=str(d.resolve()),first_timed_batch_start_UTC=first.isoformat(),complete_UTC=finish.isoformat(),elapsed_first_batch_to_complete_seconds=(finish-first).total_seconds(),generation_seconds=sum(z['elapsed_seconds'] for z in metrics),peak_reserved_bytes=max(z['peak_reserved_bytes'] for z in metrics),min_headroom_bytes=min(z['headroom_bytes'] for z in metrics)))
save(O/'existing_Indian_alpha0_receipts.json',dict(utc=utc(),cells=existing));print('EXISTING_INDIAN',json.dumps(existing))
print('DONE_CPU_DIAGNOSTICS')
