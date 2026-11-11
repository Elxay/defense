from pathlib import Path
import json,subprocess,hashlib,datetime,shutil,fcntl
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';G=R/'prereg_repo'
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def L(p):return json.loads(p.read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
subprocess.run(['scp','node01:/home/dell/Def/results/audit/unified300/translation_execution_20261111/benign20_gate.json',str(U/'translation_benign20_gate_passed.json')],check=True,capture_output=True)
assert L(U/'translation_benign20_gate_passed.json')['passed']
source=T/'unified300_static_alpha0.py';s=source.read_text().replace('static_alpha0_execution_plan','language_alpha0_execution_plan').replace('static_alpha0_inputs.private','language_alpha0_inputs.private').replace("dest=U/'static_alpha0'/key","dest=U/'language_alpha0'/key")
worker=T/'unified300_language_alpha0.py';assert not worker.exists();worker.write_text(s);compile(s,str(worker),'exec')
prep=(T/'unified300_prepare_static_alpha0.py').read_text();head=prep[:prep.index("p=U/'static_alpha0_inputs.private.json'")];start=head.index('families=[');end=head.index(';base=',start);head=head[:start]+"families=['translate-ml','translate-ta','translate-mr','translate-zh-cn','translate-fr']"+head[end:]
ns={};exec(compile(head,'language_preparation_shared_render','exec'),ns)
private=ns['private'];models=ns['models'];families=ns['families'];sources=ns['sources']
p=U/'language_alpha0_inputs.private.json';assert not p.exists();p.write_text(json.dumps(private,indent=2)+'\n')
plan=U/'language_alpha0_execution_plan.json';parent=L(U/'static_alpha0_execution_plan.json');d={k:v for k,v in parent.items()if k not in ['models','family_order','worker_sha256','private_input_sha256','source_sha256','main_outputs_before_plan']};d.update(utc_frozen=utc(),stage='S3a language alpha0 only after fixed translator interface gate',worker_sha256=H(worker),private_input_sha256=H(p),models=models,family_order=families,source_sha256={n:H(pth)for n,pth in sources.items()},language_benign20_gate_sha256=H(U/'translation_benign20_gate_passed.json'),language_plan_sha256=H(U/'language_preprocessing_plan.json'),addendum5_sha256=H(R/'docs/300_ADDENDUM5_UNREACHABLE_OPERATION_AND_DEVICE_TRANSLATION_GATES.md'),encoding_language_not_admitted=False,encoding_not_admitted=True,language_only_descriptive=True,main_outputs_before_plan=0);plan.write_text(json.dumps(d,indent=2)+'\n')
active=L(U/'active_protocol.json');active.update(updated_utc=utc(),language_alpha0_execution_plan_sha256=H(plan),language_encoding_execution_locked=False,encoding_execution_locked=True,language_execution_locked=False,language_reply_preprocessing_execution_gate_passed=True);active['allowed_main_families']+=families;(U/'active_protocol.json').write_text(json.dumps(active,indent=2)+'\n')
files=[plan,worker,U/'active_protocol.json',U/'translation_benign20_gate_passed.json'];launches=[]
for model,card in [('llama',2),('qwen',3)]:
 f=T/f'launch300_language_alpha0_{model}.sh';f.write_text(f'''#!/usr/bin/env bash
set -euo pipefail
source /data/HZX/Def/night/launch.sh
exec 201>/data/HZX/Def/logs/idle_gpu{card}.lock
flock -n 201 || exit 73
unset NOGPU
export DEVICE=cuda:{card}
wait_gpu "$DEVICE"
launch_job env CUDA_VISIBLE_DEVICES={card} DEVICE=cuda:0 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True /home/kemove/anaconda3/envs/HZX_GLA/bin/python /data/HZX/Def/tools/handoff_20261106/unified300_language_alpha0.py {model} {card}
''');files.append(f);launches.append(f)
line=utc()+' fixed translation assets and benign20 repeatability gate passed; freeze five-language alpha0 cache-only generation on innetGPU2/3, B8/B4, same frozen inputIDs and family-specific zero20. Backtranslation2200 diagnostic has no fidelity threshold and continues independently. English-subset/language results descriptive; no language WG/HB, no nonzero main outputs/read unlocked. planSHA='+H(plan)+'\n'
with (R/'docs/OPS_LOG.txt').open('a')as f:f.write(line)
files.append(R/'docs/OPS_LOG.txt')
with (R/'logs/prereg_publish.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
 for src in files:
  dst=G/src.relative_to(R);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 subprocess.run(['git','add','--',*[str(p.relative_to(R))for p in files]],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Admit cache-only language alpha0 after translation interface gate with per-family zero20 retained'],cwd=G,check=True,stdout=subprocess.DEVNULL);subprocess.run(['git','push'],cwd=G,check=True,capture_output=True)
for f in launches:
 log=open(R/'logs'/(f.stem+'.log'),'a');j=subprocess.Popen(['bash',str(f)],stdout=log,stderr=log,start_new_session=True);print('LAUNCHED',f.name,j.pid)
print('PLAN_SHA',H(plan))
