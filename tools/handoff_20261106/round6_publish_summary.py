"""Publish a completed summary document only; never stage raw data."""
from pathlib import Path
import datetime,fcntl,hashlib,json,subprocess,shutil
B=Path('/data/HZX/Def');R=B/'prereg_repo'
def publish(name,source_hashes):
 assert name in ['264_WJB_RANDOM_REFERENCES.md','265_BENIGN_SEEDS_RESULTS.md']
 with(B/'logs/prereg_publish.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  assert not subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True).strip(),'repository has pending changes; no automatic commit'
  doc=B/'docs'/name;shutil.copy2(doc,R/'docs'/name)
  with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+' OVERNIGHT_SUMMARY_READY doc='+name+' sha256='+hashlib.sha256(doc.read_bytes()).hexdigest()+'\n')
  shutil.copy2(B/'docs/PREREG_LOG.txt',R/'docs/PREREG_LOG.txt')
  manifest='manifests_'+name.split('_')[0]+'_complete.json'
  (R/manifest).write_text(json.dumps(dict(document=name,document_sha256=hashlib.sha256(doc.read_bytes()).hexdigest(),source_hashes=source_hashes),indent=2)+'\n')
  subprocess.run(['git','add','docs/'+name,'docs/PREREG_LOG.txt',manifest],cwd=R,check=True)
  subprocess.run(['git','commit','-m','Record overnight summary '+name],cwd=R,check=True)
  commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
  with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+' OVERNIGHT_SUMMARY_CONTENT_COMMIT doc='+name+' commit='+commit+'\n')
  shutil.copy2(B/'docs/PREREG_LOG.txt',R/'docs/PREREG_LOG.txt')
  subprocess.run(['git','add','docs/PREREG_LOG.txt'],cwd=R,check=True);subprocess.run(['git','commit','-m','Log overnight publication '+name],cwd=R,check=True);subprocess.run(['git','push','origin','main'],cwd=R,check=True)
  return commit
