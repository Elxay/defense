"""Read registered generation files only; never reads judge labels or discovers cells by glob."""
from pathlib import Path
import json,hashlib,sys,datetime
R=Path(sys.argv[1]);registry=Path(sys.argv[2]);out=Path(sys.argv[3])
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
P=json.loads(registry.read_text());states=[];fatal=[]
for c in P['cells']+P.get('legacy_cells',[]):
 d=R/c['output_root'];root=R/c['declared_root'];p=R/c['plan_relative'];exists=root.exists();files=sorted((R/c['record_dir']).glob('*.json'));valid=[];bad=[];mismatch=[]
 if not exists:fatal.append(c['cell_id'])
 for f in files:
  try:
   z=json.loads(f.read_text());assert isinstance(z.get('id'),(int,str));assert isinstance(z.get('result',{}).get('text'),str);valid.append(z['id']);s=z.get('signature',{});h=s.get('plan_sha256',s.get('execution_plan_sha256'))
   if h!=c['plan_sha256']:mismatch.append(f.name)
  except Exception as e:bad.append(dict(file=f.name,error=type(e).__name__))
 marks=[str((d/n).relative_to(R)) for n in ['complete.json','generation_complete.json'] if (d/n).exists()]
 status='MISSING' if not files else 'INVALID' if bad or mismatch else 'COMPLETE' if len(valid)==c['expected_rows'] and len(set(valid))==c['expected_rows'] and marks else 'PARTIAL'
 states.append(dict(cell_id=c['cell_id'],role=c.get('role','main'),model=c['model'],language=c['language'],condition=c['condition'],home_site=c['home_site'],output_root=c['output_root'],root_exists=exists,disk_rows=len(files),parseable_rows=len(valid),unique_IDs=len(set(valid)),complete_markers=marks,plan_exists=p.exists(),plan_sha256=c['plan_sha256'],plan_file_matches=p.exists() and H(p)==c['plan_sha256'],record_plan_mismatch=mismatch,parse_errors=bad,status=status,physical_resolved=str((R/c['record_dir']).resolve())))
rep=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),registry_sha256=H(registry),cells=states,missing_roots=fatal,no_judge_cache_opened=True)
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=2)+'\n')
summary={}
for z in states:
 key=z['role']+':'+z['model']+':'+z['language'];summary.setdefault(key,[]).append(z['condition']+'='+z['status']+'('+str(z['parseable_rows'])+')')
print(json.dumps(dict(utc=rep['utc'],summary=summary,missing_roots=fatal),indent=2));sys.exit(2 if fatal else 0)
