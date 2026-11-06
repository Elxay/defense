"""Finish the current rand0, score it, then run the pre-specified s3/s4/rand1 queue."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time
ROOT=Path('/data/HZX/Def');OUT=ROOT/'results/audit/handoff_20261106'
def node_python(code):
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','node01','python3 -'],input=code,text=True,capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr)
    return r.stdout
def state(phase,**kw):
    obj={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':phase,**kw}
    p=OUT/'wjb_workflow_status.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(p)
    print(json.dumps(obj),flush=True)
def run_node(name,script,args=()):
    cmd='DSH_OWNER=/data/HZX/Def python3 /home/dell/Def/tools/handoff_20261106/run_job.py '+name+' /data/ray/env/bin/python -u /home/dell/Def/tools/handoff_20261106/'+script
    if args:cmd+=' '+' '.join(args)
    subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','node01',cmd],check=True)
def copyback(name,rel):
    subprocess.run(['scp','-q','node01:/home/dell/Def/'+name,str(ROOT/rel)],check=True)
# Preflight: never queue a different vector or generator implementation unnoticed.
pre=node_python("from pathlib import Path\nimport hashlib,json\nb=Path('/home/dell/Def')\nfiles=['src/gen/common.py','configs/stage0_data/wjb300.json']+[f'results/audit/runs/block10_keep60_s{s}/v.npy' for s in [3,4]]\nprint(json.dumps({p:hashlib.sha256((b/p).read_bytes()).hexdigest() for p in files}))\nfor p in [b/'tools/AGENTS.md',b/'tools/handoff_20261106/AGENTS.md']:\n if p.exists():raise RuntimeError('unread scoped instructions: '+str(p))\n")
for rel,h in json.loads(pre).items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,(rel,'node/source mismatch')
plan={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'node':'node01','tracked_rand0_pid':1744249,
 'order':['finish existing rand0','judge rand0 (20-item same-backend gate, three-card free window)','old s3 alpha1','old s4 alpha1','rand1'],
 'generation_protocol':{'items':300,'batch_size':1,'max_new_tokens':2400,'layer':9,'norm':5.21,'device':'cuda:2','resume':'skip completed IDs; atomic every item'},
 'budget':'At 25 new items, if projected >6 hours per condition, stop remaining queue and record; no unregistered process termination.',
 'source_hashes':json.loads(pre)}
(OUT/'wjb_queue_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+' WJB QUEUE armed: finish existing rand0 PID1744249 -> same-backend gate20 + judge all300 -> old s3 -> old s4 -> rand1; node01 cuda:2; frozen single-item 2400 protocol, atomic resume, each child registered. queue_plan=results/audit/handoff_20261106/wjb_queue_plan.json; no outputs of future conditions read.\n')
deadline=time.time()+7200
probe="from pathlib import Path\nimport json,hashlib,subprocess,datetime\np=Path('/home/dell/Def/results/audit/WJB_rand0.json');raw=p.read_bytes();d=json.loads(raw)\nproc=subprocess.run(['ps','-p','1744249','-o','pid=,etimes=,args='],capture_output=True,text=True).stdout.strip()\nprint(json.dumps({'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'n':len(d),'complete':len(d)==300,'sha256':hashlib.sha256(raw).hexdigest(),'file':str(p),'mtime_ns':p.stat().st_mtime_ns,'process':proc}))\n"
last=None
while True:
    info=json.loads(node_python(probe))
    (OUT/'wjb_rand0_status.json').write_text(json.dumps(info,indent=2)+'\n')
    if info['n']!=last:state('waiting_existing_rand0',**info);last=info['n']
    if info['complete'] and not info['process']:break
    if not info['process'] and not info['complete']:raise RuntimeError('existing rand0 exited incomplete; no automatic restart')
    if info['process']:assert 'night/wjb_rand.py cuda:2 0 rand0' in info['process'],'tracked PID no longer matches'
    if time.time()>deadline:raise RuntimeError('wait deadline reached')
    time.sleep(30)
state('judging_rand0')
run_node('wjb_judge_rand0','judge_rand0.py')
copyback('results/audit/WJB_rand0.json','results/audit/WJB_rand0.json')
copyback('results/hfjudge/JUDGE_HF_wjb_rand0','results/hfjudge/JUDGE_HF_wjb_rand0')
d=json.loads((ROOT/'results/hfjudge/JUDGE_HF_wjb_rand0').read_text())
assert hashlib.sha256((ROOT/'results/audit/WJB_rand0.json').read_bytes()).hexdigest()==d['source_sha256']
for script in ['audit.py','review.py','report.py']:
    subprocess.run([sys.executable,str(ROOT/'tools/handoff_20261106'/script)],check=True)
state('rand0_scored',verified=d['verified'],harmful=sum(v['p_yes'] is not None and v['p_yes']>.5 for v in d['items'].values()),
      report_sha256=hashlib.sha256((ROOT/'docs/247_RESULTS_51_SKELETON.md').read_bytes()).hexdigest())
with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+' WJB rand0 all300 judged; verified='+str(d['verified'])+'; docs247 updated sha256='+hashlib.sha256((ROOT/'docs/247_RESULTS_51_SKELETON.md').read_bytes()).hexdigest()+'; post-score source=tools/handoff_20261106/wjb_workflow.py.\n')
if not d['verified']:raise RuntimeError('judge gate failed; stop future queue')
for name,kind,seed,tag in [('wjb_old_s3','learned','3','old_s3_a1.0'),('wjb_old_s4','learned','4','old_s4_a1.0'),('wjb_rand1','random','1','rand1')]:
    state('generating_'+tag)
    run_node(name,'wjb_future.py',['--kind',kind,'--seed',seed])
    copyback(f'results/audit/WJB_{tag}.json',f'results/audit/WJB_{tag}.json')
    copyback(f'results/audit/WJB_{tag}.meta.json',f'results/audit/WJB_{tag}.meta.json')
state('generation_queue_complete',note='s3/s4/rand1 complete and copied; future-condition scoring not yet performed')
