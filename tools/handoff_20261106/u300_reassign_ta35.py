from u300_schedule_prepare import *
import os,time,shlex
O=U/'followup35';NROOT=Path('/home/dell/Def');rel='results/audit/unified300';key='qwen_translate-ml_alpha0';lease=f'/home/dell/Def/{rel}/followup34/leases/{key}'
def node(code):return json.loads(subprocess.check_output(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(code)],text=True))
info=node("""from pathlib import Path
import json,os,hashlib,datetime
R=Path('/home/dell/Def');U=R/'results/audit/unified300';parent=R/'tools/handoff_20261106/launch_node34_gpu0.sh';assert 'set -e' in parent.read_text();pids=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   if str(parent).encode() in p.joinpath('cmdline').read_bytes().split(bytes([0])) and p.stat().st_uid==os.getuid():pids.append(int(p.name))
  except OSError:pass
assert len(pids)==1,pids;D=U/'language_processed33/qwen_translate-ml_alpha0/processed.private';A={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.glob('*.json')};assert len(A)<440;assert not list((U/'language_processed33/qwen_translate-ta_alpha0/processed.private').glob('*.json'));print(json.dumps(dict(parent_PID=pids[0],before_hashes=A,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())))""")
save(O/'Qwen_ta_cancel_before.json',info)
subprocess.run(['ssh','node01',"printf 'row-boundary cancellation of reserved Tamil continuation; resume Malayalam alone\n' > "+lease+'/yield.request'],check=True,capture_output=True)
while True:
 check=node("""from pathlib import Path
import json,os
pid="""+str(info['parent_PID'])+""";p=Path('/proc')/str(pid);cmd=p.joinpath('cmdline').read_bytes() if p.exists() else b'';y=Path('"""+lease+"""/yielded.json');print(json.dumps(dict(parent_live=bool(cmd),yielded=json.loads(y.read_text()) if y.exists() else None)))""")
 if not check['parent_live'] and check['yielded']:break
 save(O/'Qwen_ta_cancel_live.json',dict(utc=utc(),**check));time.sleep(5)
verified=node("""from pathlib import Path
import json,hashlib
U=Path('/home/dell/Def/results/audit/unified300');before="""+repr(info['before_hashes'])+""";D=U/'language_processed33/qwen_translate-ml_alpha0/processed.private';assert all(hashlib.sha256((D/n).read_bytes()).hexdigest()==h for n,h in before.items());assert not list((U/'language_processed33/qwen_translate-ta_alpha0/processed.private').glob('*.json'));print(json.dumps(dict(preserved_files=len(before),N_now=len(list(D.glob('*.json'))),ta_rows=0)))""")
resume=T/'launch_Qwen_ml_single35.sh';newlease='/home/dell/Def/results/audit/unified300/followup35/Qwen_ml_resume_lease';rev=L(O/'publication.json')['commit'];resume.write_text('''#!/usr/bin/env bash
source /home/dell/Def/night/launch_node01.sh
declare -F wait_gpu >/dev/null && declare -F launch_job >/dev/null || exit 1
set -e
export DEVICE=cuda:0
while ! wait_gpu "$DEVICE"; do sleep 10; done
mkdir -p '''+newlease+'''
launch_job env DEF_ROOT=/home/dell/Def DEF_SITE=node01 DEF_LEASE_DIR='''+newlease+''' CUDA_VISIBLE_DEVICES=0 DEF_FROZEN_GIT_REV='''+rev+''' bash /home/dell/Def/tools/handoff_20261106/u300_logged_job31.sh /home/dell/Def results/audit/unified300/language_execution33.json 0 /data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/u300_language_translate33.py qwen_translate-ml_alpha0
''');subprocess.run(['scp',str(resume),'node01:/home/dell/Def/tools/handoff_20261106/'+resume.name],check=True,capture_output=True);pid=subprocess.check_output(['ssh','node01','mkdir -p /home/dell/Def/results/audit/unified300/followup35; nohup bash /home/dell/Def/tools/handoff_20261106/'+resume.name+' > /home/dell/Def/results/audit/unified300/followup35/Qwen_ml_resume.log 2>&1 < /dev/null & echo $!'],text=True).strip()
save(O/'Qwen_ta_node_continuation_cancelled.json',dict(utc=utc(),ready=True,old_parent_PID=info['parent_PID'],old_parent_ended=True,node_ta_rows=0,ml_preserved_files=verified['preserved_files'],ml_resume_launcher_PID=int(pid),ml_same_node_same_gpu=True,reason='Original two-cell shell exited75 at ML row boundary; restarted ML-only shell, no pending node Tamil command'))
print(json.dumps(L(O/'Qwen_ta_node_continuation_cancelled.json')))
