from pathlib import Path
import json,datetime,hashlib,os,sys,unicodedata,collections
from langdetect import DetectorFactory,detect_langs
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
plan=load(U/'S0_followup_diagnostics_execution.json');assert sha(__file__)==plan['language_worker_sha256'];assert sha(U/'human_inputs.private.json')==plan['human_inputs_sha256'];assert sha(U/'human_gold.private.json')==plan['human_gold_sha256']
import langdetect
root=Path(langdetect.__file__).parent
for n,v in plan['language_package_files'].items():assert sha(root/n)==v
DetectorFactory.seed=plan['language_seed'];rows={r['id']:r for r in load(U/'human_inputs.private.json')};gold=load(U/'human_gold.private.json');styles={'translate-ml':'ml','translate-ta':'ta','translate-mr':'mr','translate-zh-cn':'zh-cn','translate-fr':'fr'};out=[]
for r in gold:
 if r['prompt_style']not in styles:continue
 text=rows[r['id']]['response'];counts=collections.Counter()
 for c in text:
  if not c.isalpha():continue
  o=ord(c);counts['letters']+=1
  for name,lo,hi in [('Malayalam',0x0D00,0x0D7F),('Tamil',0x0B80,0x0BFF),('Devanagari',0x0900,0x097F),('Han',0x4E00,0x9FFF)]:
   if lo<=o<=hi:counts[name]+=1
  if 'LATIN'in unicodedata.name(c,''):counts['Latin']+=1
 try:
  ds=detect_langs(text);top=ds[0];language=top.lang;prob=float(top.prob);err=None
 except Exception as e:language=None;prob=None;err=type(e).__name__
 latin=counts['Latin']/max(1,counts['letters']);english_dominant=language=='en'and prob>=plan['language_confidence']and latin>=.9
 out.append(dict(id=r['id'],style=r['prompt_style'],response_sha256=hashlib.sha256(text.encode()).hexdigest(),top1=language,probability=prob,english_dominant=english_dominant,script_counts=dict(counts),error=err))
 if len(out)%25==0:save(U/'human_language_audit_live.json',dict(utc=utc(),pid=os.getpid(),completed=len(out),total=626))
summary={}
for style in styles:
 group=[x for x in out if x['style']==style];summary[style]=dict(N=len(group),top1_counts=dict(collections.Counter(x['top1']for x in group)),english_dominant=sum(x['english_dominant']for x in group),native_top1_highconf=sum(x['top1']==styles[style]and x['probability']>=plan['language_confidence']for x in group),script_presence_rows={n:sum(x['script_counts'].get(n,0)>0 for x in group)for n in ['Malayalam','Tamil','Devanagari','Han']},script_total_letters={n:sum(x['script_counts'].get(n,0)for x in group)for n in ['Malayalam','Tamil','Devanagari','Han','Latin']},low_confidence_or_error=sum(x['probability']is None or x['probability']<plan['language_confidence']for x in group))
result=dict(utc=utc(),N=len(out),execution_sha256=sha(U/'S0_followup_diagnostics_execution.json'),summary=summary,records=out,no_response_text_published=True,original_pretranslation_pairs_available=False,interpretation='Language detection describes supplied reply field only; English records cannot validate translation of new original-language replies; short/mixed detection uncertain.')
save(U/'human_language_audit.json',result);save(U/'human_language_audit_live.json',dict(utc=utc(),pid=os.getpid(),phase='complete',N=len(out)));print(json.dumps(summary,indent=2));print('SHA',sha(U/'human_language_audit.json'))
