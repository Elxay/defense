"""Publish a precise whitelist of coded PAIR read artifacts and manuscript source."""
from pathlib import Path
import datetime,fcntl,hashlib,json,re,shutil,subprocess
R=Path('/data/HZX/Def');G=R/'prereg_repo';B=R/'results/audit/pair500';O=B/'read_order10'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(obj):
 if isinstance(obj,dict):
  assert not({'prompt','response','text','raw_output','raw_response','best','messages','input_ids'}&set(obj)),str(set(obj))
  for v in obj.values():safe(v)
 elif isinstance(obj,list):
  for v in obj:safe(v)
def main():
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 files=['docs/289_PAIR500_COMPLETED_ORDERED_READ.md','docs/PREREG_LOG.txt','docs/OPS_LOG.txt','paper/main.tex','paper/sections/01_introduction.tex','paper/sections/04_results.tex','paper/sections/06_limitations.tex','paper/tables/pair500_primary.tex','paper/generated/pair500_completed_read.tex','paper/generated/pair500_numbers.tex']
 files +=[str((O/'ordered_results'/f'{i:02d}.json').relative_to(R))for i in range(1,9)]
 files +=[str(p.relative_to(R))for p in (O/'published_tables').glob('*')if p.is_file()]
 files +=[str(p.relative_to(R))for p in (O/'lifecycle').glob('*.json')if p.name!='observer_live.json']
 files +=['tools/handoff_20261106/'+n for n in ['pair254_export_completed_read.py','pair254_complete_manuscript.py','publish_pair254_completed_read.py']]
 for relative in ['results/audit/pair500/lease_priority/completed_reservations/cleanup_receipt.json','results/audit/pair500/lease_priority/completed_reservations/gpu0_20261109_133302.json','results/audit/pair500/tail_contextual_followup_20261109/contextual_all1300_length_audit.json','results/audit/pair500/argument_revision_20261109/contextual_full1300_receipt.json']:
  assert(R/relative).is_file(),relative;files.append(relative)
 files=sorted(set(files))
 for n in files:
  p=R/n;assert p.is_file(),n
  s=p.read_text();assert not re.search(r'hf_[A-Za-z0-9]{20,}',s),'Credential-like literal; do not print it'
  if p.suffix=='.json':safe(json.loads(s))
  assert '.private'not in n and not n.endswith(('.bin','.safetensors','.pt','.npy'))
 with(R/'logs/prereg_publish.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip(),'Unrelated or incomplete work; preserve it'
  for n in files:
   p=G/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
  m='manifests_pair254_completed_read.json';(G/m).write_text(json.dumps({'utc':now,'files':{n:sha(G/n)for n in files},'all500_all13_both_judges_admitted':True,'ordered_read_completed':True,'PDF_rebuilt':False,'raw_attack_or_model_output_published':False,'weights_or_vectors_published':False,'pending_model_ports_not_counted_as_replication':True},indent=2)+'\n')
  subprocess.run(['git','add',*files,m],cwd=G,check=True)
  staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=G,text=True).splitlines();assert set(staged)<=set(files)|{m}
  subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True)
  subprocess.run(['git','commit','-m','Report complete sequential PAIR read and regenerate evidence tables and abstract'],cwd=G,check=True)
  commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip()
  subprocess.run(['git','push','origin','main'],cwd=G,check=True)
 print(json.dumps({'utc':now,'commit':commit,'file_count':len(files),'report_sha256':sha(R/files[0])if files[0]=='docs/289_PAIR500_COMPLETED_ORDERED_READ.md'else sha(R/'docs/289_PAIR500_COMPLETED_ORDERED_READ.md'),'primary_csv_sha256':sha(O/'published_tables/primary.csv'),'final_read_sha256':sha(O/'ordered_results/08.json')}))
if __name__=='__main__':main()
