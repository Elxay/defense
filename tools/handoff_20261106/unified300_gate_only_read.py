"""SORRY alpha0 gate-only reader: no HB/WG imports or outcome reads."""
from pathlib import Path
import json,hashlib,datetime,subprocess,fcntl,shutil
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';G=R/'prereg_repo'
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def L(p):return json.loads(p.read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,o):assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n')
P=L(U/'SORRY_alpha0_gate_read_plan.json');assert H(__file__)==P['worker_sha256'];O=U/'SORRY_alpha0_gate_reads';assert not O.exists();O.mkdir();ledger=[]
for m in ['llama','qwen']:
 for fam in P['family_order']:
  D=U/'static_alpha0_SORRY/tasks'/m/fam;marker=D/'complete.json';x=L(marker);assert x['N']==440 and x['condition']=='alpha0';assert x['plan_sha256']==P['score_execution_plan_sha256'];assert len(x['score_record_sha256'])==440
  for k,h in x['score_record_sha256'].items():assert H(D/'scores.private'/f'{int(k):04d}.json')==h
  n1=0;unknown=0
  for k in sorted(x['score_record_sha256'],key=int):
   row=L(D/'scores.private'/f'{int(k):04d}.json');assert row['signature']['condition']=='alpha0';label=row['label'];assert label in [0,1,None];n1+=label==1;unknown+=label is None
  low=n1/440;high=(n1+unknown)/440;gate='inactive_skip_nonzero'if n1+unknown<110 else'active'if n1>=110 else'INVALID_crossing_continue'
  out=O/m/(fam+'.json');value=dict(utc=utc(),model=m,family=fam,condition='alpha0',judge='SORRY',N=440,fulfilled=n1,invalid=unknown,fulfillment_rate_lower=low,fulfillment_rate_upper=high,gate=gate,threshold_count=110,source_complete_sha256=H(marker),execution_plan_sha256=H(U/'SORRY_alpha0_gate_read_plan.json'),HB_or_WG_read=False,nonzero_read=False)
  save(out,value);entry=dict(utc=value['utc'],model=m,family=fam,output_sha256=H(out));ledger.append(entry);(O/'read_ledger.json').write_text(json.dumps(dict(steps=ledger,main_effect_reads=False),indent=2)+'\n')
  with (R/'docs/OPS_LOG.txt').open('a')as f:f.write(value['utc']+' gate-only SORRY alpha0 '+m+'/'+fam+' outputSHA='+H(out)+' (no other judge/condition read)\n')
save(O/'all_complete.json',dict(utc=utc(),families=20,read_ledger_sha256=H(O/'read_ledger.json'),no_effects_read=True))
lines=['# SORRY alpha0闸门限定读取','', '| 模型 | 家族 | 履行/440 | 履行率界 | 闸门 | UTC |','|---|---|---:|---:|---|---|']
for e in ledger:
 x=L(O/e['model']/(e['family']+'.json'));rate=f"{x['fulfillment_rate_lower']*100:.2f}%"if x['invalid']==0 else f"[{x['fulfillment_rate_lower']*100:.2f},{x['fulfillment_rate_upper']*100:.2f}]%";lines.append(f"| {x['model']} | {x['family']} | {x['fulfilled']} | {rate} | {x['gate']} | {x['utc']} |")
(O/'gate_table.md').write_text('\n'.join(lines).rstrip()+'\n')
a=U/'active_protocol.json';active=L(a);active['SORRY_alpha0_gate_decisions']={m:{f:L(O/m/(f+'.json'))['gate']for f in P['family_order']}for m in ['llama','qwen']};active['main_label_or_effect_reads_allowed']=False;active['updated_utc']=utc();a.write_text(json.dumps(active,indent=2)+'\n')
files=[*O.glob('*/*.json'),O/'read_ledger.json',O/'all_complete.json',O/'gate_table.md',R/'docs/OPS_LOG.txt',a]
with (R/'logs/prereg_publish.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
 for p in files:
  dst=G/p.relative_to(R);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
 subprocess.run(['git','add','--',*[str(p.relative_to(R))for p in files]],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Read SORRY alpha0 family gates only with sequential UTC and SHA receipts'],cwd=G,check=True,stdout=subprocess.DEVNULL);subprocess.run(['git','push'],cwd=G,check=True,capture_output=True)
print((O/'gate_table.md').read_text());print('LEDGER_SHA',H(O/'read_ledger.json'))
