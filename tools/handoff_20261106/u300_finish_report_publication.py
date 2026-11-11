from pathlib import Path
import fcntl,json,shutil,subprocess
from u300_schedule_prepare import R,U,T,G,H,L,utc,save
md=[U/'RULE16_MATRIX_MODEL_PREPARATION_20261111.md',U/'family_condition_status_20261111_v3.md']
for p in md:p.write_text(p.read_text().rstrip()+'\n')
line=utc()+' Format-only final-newline repair after diff --check; numeric data unchanged. final reportSHA='+H(md[0])+'\n'
logs=[]
for name in ['OPS_LOG','OPS_LOG.txt','PREREG_LOG.txt']:
 p=R/'docs'/name
 if p.exists():
  with p.open('a') as f:f.write(line)
  logs.append(p)
files=md+logs+[T/'u300_rule16_final_report.py',T/'u300_generation_matrix_v3.py',Path(__file__)]
expected={str(p.relative_to(R)) for p in files}|{
 'results/audit/unified300/HiddenDetect_ModelScope_download_complete.json',
 'models/HiddenDetect_llava_v16_vicuna7b_modelscope/DOWNLOAD_SHA256.json',
 'results/audit/unified300/family_condition_status_20261111_v3.json',
 'results/audit/unified300/Gemma_Mistral_preparation_status_20261111.json',
 'results/audit/unified300/GPU_project_status_rule16.json',
 'results/audit/unified300/paper_rule16_diagnostic_claim_audit.json'}
with (R/'logs/prereg_publish.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 staged=set(subprocess.check_output(['git','diff','--cached','--name-only'],cwd=G,text=True).splitlines());assert staged<=expected
 dirty=set(subprocess.check_output(['git','diff','--name-only'],cwd=G,text=True).splitlines());assert dirty<=expected
 for p in files:
  dst=G/p.relative_to(R);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
 subprocess.run(['git','add','--',*[str(p.relative_to(R)) for p in files]],cwd=G,check=True)
 subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True)
 subprocess.run(['git','commit','-m','Publish refreshed family matrix, model readiness and active-cell budget after format verification'],cwd=G,check=True,capture_output=True)
 subprocess.run(['git','push'],cwd=G,check=True,capture_output=True)
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip()
save(U/'rule16_final_publication.json',dict(utc=utc(),commit=commit,report_sha256=H(md[0])))
print(json.dumps(dict(commit=commit,report_sha256=H(md[0]),matrix_utc=L(U/'family_condition_status_20261111_v3.json')['utc'],
 cards_utc=L(U/'GPU_project_status_rule16.json')['utc'],paper_pattern_hits=L(U/'paper_rule16_diagnostic_claim_audit.json')['narrow_pattern_hits'])))
