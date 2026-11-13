from pathlib import Path
import os,sys,json,hashlib,datetime,time,subprocess
R=Path('/home/dell/Def');U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'Mistral_calibration32_plan.json');D=Path(P['output_root']);B=L(U/'followup34/Mistral_WG_binding.json')
while not ((D/'complete22.json').exists() and (U/'followup34/Mistral_norm_and_adjacent_guard.json').exists() and L(U/'followup34/Mistral_norm_and_adjacent_guard.json')['selection_execution_contract_passed']):time.sleep(10)
raw=L(P['input_path']);raw=raw if isinstance(raw,list) else raw.get('rows') or raw['items'];pack=[];conditions=['alpha0']+[f's{s}_a{a:.2f}' for s in [3,4,5] for a in P['alpha_grid']]
for c in conditions:
 comp=L(D/c/'complete.json');assert comp['N']==700
 for i in range(700):
  gp=D/c/'generation.private'/f'{i:04d}.json';assert H(gp)==comp['record_sha256'][gp.name];z=L(gp);assert z['plan_sha256']==H(U/'Mistral_calibration32_plan.json');prompt=raw[i].get('prompt') or raw[i].get('text');response=z['result']['text'];ph=hashlib.sha256(prompt.encode()).hexdigest()
  pack.append(dict(id=f'{c}:{i}',model='mistral',family='calibration700_v32',condition=c,prompt=prompt,behavior=prompt,response=response,prompt_sha256=ph,behavior_sha256=ph,response_sha256=hashlib.sha256(response.encode()).hexdigest(),generation_sha256=H(gp),preprocessing_sha256=None))
assert len(pack)==15400;W=U/'score_waves/Mistral_calibration32';save(W/'inputs.private.json',pack);save(W/'manifest.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),N=15400,judges=['WG'],inputs_sha256=H(W/'inputs.private.json'),scope='corrected calibration only; cache write, no selection statistics',generation_plan_sha256=H(U/'Mistral_calibration32_plan.json')))
lease=U/'followup34/Mistral_WG32_lease';lease.mkdir(parents=True,exist_ok=True);script=T/'launch_Mistral_WG32_after34.sh';script.write_text('''#!/usr/bin/env bash
source /home/dell/Def/night/launch_node01.sh
declare -F wait_gpu >/dev/null && declare -F launch_job >/dev/null || exit 1
set -e
export DEVICE=cuda:1
while ! wait_gpu "$DEVICE"; do sleep 10; done
launch_job env DEF_ROOT=/home/dell/Def DEF_SITE=node01 DEF_LEASE_DIR='''+str(lease)+''' CUDA_VISIBLE_DEVICES=1 DEF_FROZEN_GIT_REV='''+B['published_commit']+''' bash /home/dell/Def/tools/handoff_20261106/u300_logged_job31.sh /home/dell/Def results/audit/unified300/scoring_schedule_v1.json 1 /data/ray/env/bin/python /home/dell/Def/tools/handoff_20261106/u300_score_cache_worker.py WG Mistral_calibration32
''')
log=(lease/'runner.log').open('a');proc=subprocess.Popen(['bash',str(script)],stdout=log,stderr=log,start_new_session=True);save(U/'followup34/Mistral_WG32_started.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),launcher_PID=proc.pid,calibration_completed_UTC=L(D/'complete22.json')['utc'],N=15400,only_cache_write=True,no_selection_read=True));proc.wait();save(U/'followup34/Mistral_WG32_exit.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),returncode=proc.returncode,selection_read_admitted=False))
