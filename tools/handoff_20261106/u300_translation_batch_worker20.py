"""Fixed100 translation batch engineering only; no protected outcomes."""
from pathlib import Path
import os,sys,json,hashlib,datetime,time
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';sys.path.insert(0,str(T));from language300_unicode_routing20 import preprocess_reply,route_reply,detect_reply_language,digest
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def L(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'translation_batch_execution20.json');assert H(__file__)==P['worker_sha256'];assert H(T/'language300_unicode_routing20.py')==P['helper_sha256'];assert H(U/'translation_batch_inputs20.private.json')==P['inputs_sha256'];rows=L(U/'translation_batch_inputs20.private.json');assert len(rows)==100
D=U/'translation_batch_engineering20';lease=Path(os.environ['DEF_LEASE_DIR']);plan=L(U/'language_preprocessing_route20_plan.json');assets=L(U/'translator_Qwen3_asset_manifest.json');mp=Path(assets['path'])
for n,h in assets['files_sha256'].items():assert H(mp/n)==h
model=AutoModelForCausalLM.from_pretrained(mp,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();tok=AutoTokenizer.from_pretrained(mp,local_files_only=True);tok.padding_side='left'
if tok.pad_token_id is None:tok.pad_token=tok.eos_token
requested=int(sys.argv[1]);variants=[1,8] if requested==8 else [4];cap=4096
for B in variants:
 outdir=D/('B'+str(B))
 if (outdir/'complete.json').exists():continue
 try:
  for begin in range(0,100,B):
   group=rows[begin:begin+B];paths=[outdir/'processed.private'/f"{r['id']:03d}.json" for r in group]
   if all(p.exists() for p in paths):continue
   torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();tick=time.monotonic()
   if B==1:vals=[preprocess_reply(group[0]['response'],model,tok,plan)]
   else:
    routes=[route_reply(r['response'],plan['language_seed']) for r in group];assert all(r['route']=='local_translate' for r in routes)
    ids=[tok.apply_chat_template([dict(role='system',content=plan['system_text']),dict(role='user',content=r['response'])],add_generation_prompt=True,enable_thinking=False) for r in group]
    assert all(len(x)+cap<=model.config.max_position_embeddings for x in ids),'Engineering panel translator context overflow'
    enc=tok.pad({'input_ids':ids},padding=True,return_tensors='pt').to('cuda:0');width=enc.input_ids.shape[1];torch.manual_seed(plan['translation_seed'])
    with torch.inference_mode():out=model.generate(**enc,max_new_tokens=cap,do_sample=False,pad_token_id=tok.eos_token_id)
    eos=model.generation_config.eos_token_id;eos={eos} if isinstance(eos,int) else set(eos or []);vals=[]
    for raw,routed,seq in zip(group,routes,out[:,width:].tolist()):
     cut=next((j+1 for j,t in enumerate(seq) if t in eos),len(seq));seq=seq[:cut];text=tok.decode(seq,skip_special_tokens=True);lang=detect_reply_language(text,plan['language_seed']);finished=bool(seq and seq[-1] in eos);truncated=len(seq)>=cap and not finished
     status='translation_truncated' if truncated else 'translation_empty' if not text.strip() else 'translation_not_identified_English' if lang['language']!='en' else 'translated'
     vals.append(dict(raw_response_sha256=digest(raw['response']),**routed,translation_attempted=True,translation_human_validated=False,status=status,translated_response=text,translated_response_sha256=digest(text),translator_new_tokens=len(seq),translator_eos=finished,translator_output_language=lang,primary_INVALID=status!='translated',processed_response=text if status=='translated' else None,processed_response_sha256=digest(text) if status=='translated' else None))
   torch.cuda.synchronize();free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();head=total-outside-torch.cuda.max_memory_reserved()
   for r,z,p in zip(group,vals,paths):
    value=dict(id=r['id'],source_generation_sha256=r['source_generation_sha256'],plan_sha256=H(U/'translation_batch_execution20.json'),B=B,result=z)
    if p.exists():assert L(p)==value,'Partial batch replay differs; retain and stop'
    else:save(p,value)
   save(outdir/'metrics'/f'{begin:03d}.json',dict(utc=utc(),rows=len(group),seconds=time.monotonic()-tick,headroom_GiB=head/1024**3,peak_reserved_GiB=torch.cuda.max_memory_reserved()/1024**3))
   if head<3*1024**3:raise MemoryError('peak headroom below3GiB')
   save(lease/'live.json',dict(utc=utc(),B=B,N=min(begin+B,100),total=100,engineering_only=True))
  pack=[]
  for r in rows:
   p=outdir/'processed.private'/f"{r['id']:03d}.json";z=L(p)['result'];text=z.get('processed_response') or ''
   pack.append(dict(id=r['id'],source_model=r['source_model'],source_family=r['source_family'],model='translator_engineering',family='translation_B'+str(B),condition='alpha0',prompt=r['prompt'],behavior=r['behavior'],response=text,prompt_sha256=r['prompt_sha256'],behavior_sha256=r['behavior_sha256'],response_sha256=digest(text),generation_sha256=H(p),preprocessing_sha256=H(p),primary_preprocessing_INVALID=z['primary_INVALID']))
  W=U/'score_waves'/('translation_engineering_B'+str(B));save(W/'inputs.private.json',pack);save(W/'manifest.json',dict(utc=utc(),N=100,judges=['SORRY'],inputs_sha256=H(W/'inputs.private.json'),scope='translation engineering alpha0 only'))
  save(outdir/'complete.json',dict(utc=utc(),N=100,wave=W.name,plan_sha256=H(U/'translation_batch_execution20.json')))
 except (torch.cuda.OutOfMemoryError,MemoryError) as e:
  save(outdir/'failed.json',dict(utc=utc(),reason=type(e).__name__,next_B=4 if B==8 else 1,formal_admitted=False));break
