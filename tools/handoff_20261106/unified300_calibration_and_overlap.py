"""CPU-only fixed WJB sampling and SORRY overlap flags; never generates responses."""
from pathlib import Path
import collections, csv, datetime, hashlib, json, random, unicodedata

R=Path('/data/HZX/Def');U=R/'results/audit/unified300';S=R/'results/audit/sorry296'
W=Path('/data/huggingface/hub/datasets--allenai--wildjailbreak/snapshots/5ddc12a7894f842b0619b8e1c7ee496b198af009/train/train.tsv')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(16*1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def norm(s):return ' '.join(unicodedata.normalize('NFKC',s).casefold().split())
def pulse(phase,**kw):save(U/'CPU_audit_live.json',dict(utc=utc(),phase=phase,model_outputs_generated=False,**kw))
def main():
 cfg={'adversarial_harmful':(300,20261230),'adversarial_benign':(200,20261231),'vanilla_benign':(200,20261232)}
 randoms={k:random.Random(seed)for k,(_,seed)in cfg.items()};sample={k:[]for k in cfg};seen=collections.Counter()
 pulse('sampling_fixed_source_reservoir')
 with W.open()as f:
  for ordinal,row in enumerate(csv.DictReader(f,delimiter='\t')):
   kind=row['data_type']
   if kind not in cfg:continue
   seen[kind]+=1;k=cfg[kind][0]
   pos=seen[kind]-1 if seen[kind]<=k else randoms[kind].randrange(seen[kind])
   if pos>=k:continue
   prompt=row['vanilla']if kind=='vanilla_benign'else row['adversarial']
   record={'id':f'wjb_train_{ordinal:09d}','source_ordinal':ordinal,'kind':kind,'prompt':prompt,'behavior':row['vanilla'],'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()}
   if seen[kind]<=k:sample[kind].append(record)
   else:sample[kind][pos]=record
 selected=[]
 for kind in cfg:
  assert len(sample[kind])==cfg[kind][0]
  selected.extend(sorted(sample[kind],key=lambda r:r['id']))
 assert len(selected)==700 and all(r['prompt']for r in selected)
 dest=U/'calibration700.private.json'
 if dest.exists():assert load(dest)==selected
 else:save(dest,selected)
 manifest={'utc':utc(),'source':str(W),'source_sha256':sha(W),'sampling':'uniform reservoir over fixed stable source ordinals; per-type independent fixed PRNG; final sort by ID','seeds':{k:v[1]for k,v in cfg.items()},'population':dict(seen),'selected_counts':{k:len(v)for k,v in sample.items()},'file_sha256':sha(dest),'selected':[{'id':r['id'],'kind':r['kind'],'prompt_sha256':r['prompt_sha256']}for r in selected],'resample_after_overlap':False,'model_outputs_generated':False}
 save(U/'calibration700_manifest.json',manifest)
 # Distinguish original behaviors from actual historical attack prompts.
 pair=load(R/'results/audit/pair500/rows.private.json');reference={}
 for flag in ['fit12','val70','legacy46','dev22']:
  reference[flag+'_behaviors']=[{'id':r['id'],'text':r['behavior'],'group':r['group']}for r in pair if flag in r['direct_flags']]
 fit=load(R/'configs/stage0_data/attacks_fit12.json')
 reference['fit12_attack_prompts']=[{'id':r['id'],'text':r['text'],'group':r['id']}for r in fit]
 native=load(R/'results/audit/crossmodel287/native_selection_inputs.private.json')['val70']
 reference['val70_attack_prompts']=[{'id':r['id'],'text':r['prompt'],'group':r['id']}for r in native]
 strat=load(R/'configs/stage0_data/b8_train_strat.json')['items']
 reference['train_strat97']=[{'id':f'group{i:03d}_alias{j}','group':f'group{i:03d}','text':text}for i,r in enumerate(strat)for j,text in enumerate(r['texts'])]
 reference['WJB_HarmBench_standard_sources']=[{'id':r['id'],'group':r['group'],'text':r['behavior']}for r in pair if r['dataset']=='HarmBench'and r['layer']=='standard']
 assert len(reference['WJB_HarmBench_standard_sources'])==200
 for kind in cfg:reference['calibration_'+kind]=[{'id':r['id'],'group':r['id'],'text':r['prompt']}for r in selected if r['kind']==kind]
 reference['calibration_underlying_behaviors']=[{'id':r['id'],'group':r['id'],'text':r['behavior']}for r in selected]
 with(S/'downloads.private/sorry-bench-202503/question.jsonl').open()as f:base=[json.loads(l)for l in f if l.strip()]
 pulse('loading_frozen_MiniLM_CPU')
 import torch
 torch.set_num_threads(8)
 from sentence_transformers import SentenceTransformer
 import numpy as np
 modelpath=Path('/data/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41')
 model=SentenceTransformer(str(modelpath),device='cpu',local_files_only=True)
 # Match the existing project's normalized MiniLM cosine audit, not a new threshold.
 B=model.encode([r['turns'][0]for r in base],batch_size=64,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False)
 flags={str(r['question_id']):{}for r in base};summary={};source_hashes={}
 for family,records in reference.items():
  assert records
  texts=[r['text']for r in records];E=model.encode(texts,batch_size=64,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False);cos=B@E.T
  raw={t for t in texts};normal={norm(t)for t in texts};a=b=c=0
  for i,r in enumerate(base):
   text=r['turns'][0];j=int(np.argmax(cos[i]));value=float(cos[i,j]);entry={'byte_exact':text in raw,'normalized_exact':norm(text)in normal,'cos_ge_085':value>=.85,'nearest_reference_id':records[j]['id'],'nearest_cosine':value}
   flags[str(r['question_id'])][family]=entry;a+=entry['byte_exact'];b+=entry['normalized_exact'];c+=entry['cos_ge_085']
  summary[family]={'reference_texts':len(records),'reference_groups':len({r['group']for r in records}),'SORRY_byte_exact':a,'SORRY_normalized_exact':b,'SORRY_cos_ge_085':c}
  pulse('overlap_reference_complete',reference=family)
 calibration_flags=[]
 all_refs=[(fam,z)for fam,rs in reference.items()if not fam.startswith('calibration_')for z in rs]
 E=model.encode([z['text']for _,z in all_refs],batch_size=64,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False)
 C=model.encode([r['prompt']for r in selected],batch_size=64,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False);sim=C@B.T
 for i,r in enumerate(selected):
  j=int(np.argmax(sim[i]));calibration_flags.append({'id':r['id'],'kind':r['kind'],'SORRY_nearest_id':base[j]['question_id'],'cosine':float(sim[i,j]),'cos_ge_085':bool(sim[i,j]>=.85)})
 encoder_files={str(p.relative_to(modelpath)):sha(p)for p in modelpath.rglob('*')if p.is_file()and not p.name.startswith('.')}
 source_paths=['results/audit/pair500/rows.private.json','configs/stage0_data/attacks_fit12.json','configs/stage0_data/b8_train_strat.json','results/audit/crossmodel287/native_selection_inputs.private.json']
 result={'utc':utc(),'N_base':440,'threshold':.85,'normalization':'NFKC casefold whitespace collapse','encoder_revision':modelpath.name,'encoder_files_sha256':encoder_files,'encoder_max_seq_length':model.max_seq_length,'reference_source_sha256':{p:sha(R/p)for p in source_paths},'calibration_manifest_sha256':sha(U/'calibration700_manifest.json'),'summary':summary,'base_row_flags':flags,'calibration_vs_SORRY_flags':calibration_flags,'rows_deleted':0,'no_resampling':True,'unverified_semantic_identity':True}
 save(U/'overlap_flags.json',result);pulse('complete_no_model_outputs',n_base=440,n_calibration=700)
 print(json.dumps({'summary':summary,'calibration_marked':sum(r['cos_ge_085']for r in calibration_flags),'rows_deleted':0},indent=2))
if __name__=='__main__':main()
