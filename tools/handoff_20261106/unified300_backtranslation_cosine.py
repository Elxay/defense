"""Fixed descriptive instruction-backtranslation cosine; never reads tested-model labels."""
from pathlib import Path
import json,hashlib,subprocess,time,datetime,statistics
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';O=U/'translation_backtranslation_cosine';O.mkdir(exist_ok=True)
def save(p,o):q=p.with_suffix('.tmp');q.write_text(json.dumps(o,indent=2)+'\n');q.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((U/'translation_diagnostic_inputs.private.json').read_text());langs=['zh-cn','fr','mr','ml','ta'];model=None
while len(list(O.glob('summary_*.json')))<5:
 for lang in langs:
  dest=O/f'summary_{lang}.json'
  if dest.exists():continue
  cmd=f'find /home/dell/Def/results/audit/unified300/translation_execution_20261111/backtranslation.private/{lang} -maxdepth 1 -name "*.json" -type f 2>/dev/null | wc -l'
  result=subprocess.run(['ssh','node01',cmd],capture_output=True,text=True);n=int(result.stdout.strip()or 0)
  save(O/'live.json',dict(utc=utc(),phase='waiting_per_language_complete',language=lang,saved_rows=n,total=440))
  if n!=440:continue
  d=O/'private'/lang;d.mkdir(parents=True,exist_ok=True);subprocess.run(['rsync','-a','node01:/home/dell/Def/results/audit/unified300/translation_execution_20261111/backtranslation.private/'+lang+'/',str(d)+'/'],check=True,capture_output=True)
  if model is None:
   from sentence_transformers import SentenceTransformer
   mp=Path('/data/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41');model=SentenceTransformer(str(mp),device='cpu',local_files_only=True)
  selected=[r for r in rows if r['language']==lang];pairs=[];fail=[]
  for r in selected:
   z=json.loads((d/f"{r['id']:04d}.json").read_text());tr=z['translation']
   if tr is None or not tr['text'].strip()or tr['truncated']:fail.append(r['id']);continue
   pairs.append((r,tr))
  originals=[r['base_text']for r,t in pairs];translated=[t['text']for r,t in pairs];a=model.encode(originals,batch_size=64,normalize_embeddings=True,show_progress_bar=False);b=model.encode(translated,batch_size=64,normalize_embeddings=True,show_progress_bar=False);cos=(a*b).sum(axis=1);cos=[float(x)for x in cos]
  original_long=sum(len(model.tokenizer.encode(t,add_special_tokens=True,truncation=False))>model.max_seq_length for t in originals);translated_long=sum(len(model.tokenizer.encode(t,add_special_tokens=True,truncation=False))>model.max_seq_length for t in translated)
  save(O/f'cosines_{lang}.json',dict(language=lang,rows=[dict(id=r['id'],cosine=c,source_sha256=r['source_sha256'],base_sha256=r['base_sha256'],translated_sha256=t['text_sha256'])for(r,t),c in zip(pairs,cos)]))
  save(dest,dict(utc=utc(),language=lang,N_total=440,N_valid=len(cos),failed_IDs=fail,mean=statistics.mean(cos)if cos else None,SD=statistics.stdev(cos)if len(cos)>1 else None,median=statistics.median(cos)if cos else None,min=min(cos)if cos else None,max=max(cos)if cos else None,encoder_max_seq_length=model.max_seq_length,original_over_encoder_limit=original_long,translation_over_encoder_limit=translated_long,metric='English MiniLM cosine, instruction only; no reply fidelity claim; no admission threshold',cosines_sha256=sha(O/f'cosines_{lang}.json')))
 time.sleep(30)
save(O/'all_complete.json',dict(utc=utc(),languages=langs,no_scope_or_threshold_changes=True,no_main_model_labels_read=True))
