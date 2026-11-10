"""Progress-only controller for the frozen WG selection grid; no label aggregation."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';D=C/'qwen_selection'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def pulse(phase,**kw):save(D/'WG_queue_live.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'phase':phase,'condition_effects_read':False,**kw})
def main():
 plan=load(D/'plan.json');assert sha(Path(__file__))==plan['score_queue_sha256'];base=load(C/'qwen_WG_cross/Qwen_alpha0_inputs.private.json');assert len(base)==470
 for seed in [3,4,5]:
  for alpha in plan['alpha_grid']:
   name=f's{seed}_a{alpha:g}';markers=[D/'condition_done'/f'{name}_shard{i}.json'for i in [0,1]]
   while not all(p.exists()for p in markers):
    if any((D/f'zero20_gpu{k}.json').exists()and not load(D/f'zero20_gpu{k}.json')['passed']for k in [2,3]):pulse('stopped_zero20_failed');return
    pulse('waiting_generation',condition=name);time.sleep(15)
   payload=[]
   for row in base:
    p=D/'generation.private'/name/row['set']/(row['source_id']+'.json');x=load(p);assert x['signature']['plan_sha256']==sha(D/'plan.json');payload.append({**{k:v for k,v in row.items()if k!='v2'},'response':x['result']['text'],'source_sha256':sha(p)})
   private=D/(name+'_inputs.private.json')
   if private.exists():assert load(private)==payload
   else:save(private,payload);private.chmod(0o600)
   subprocess.run(['ssh','node01','mkdir','-p','/home/dell/Def/results/audit/crossmodel287/qwen_selection_WG'],check=True)
   subprocess.run(['rsync','-a',str(private),'node01:/home/dell/Def/results/audit/crossmodel287/qwen_selection_WG/'],check=True)
   subprocess.run(['rsync','-a',str(D/'plan.json'),'node01:/home/dell/Def/results/audit/crossmodel287/qwen_selection_WG/selection_plan.json'],check=True)
   script=f'''source /home/dell/Def/tools/handoff_20261106/node01_launch_round9.sh
cd /home/dell/Def
exec 8>>logs/idle_gpu0.lock
flock 8
unset NOGPU
export DEVICE=cuda:0
while ! wait_gpu cuda:0; do sleep 15; done
launch_job env CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 /data/ray/env/bin/python -u tools/handoff_20261106/qwen287_selection_wg_worker.py {name}
'''
   pulse('scoring',condition=name)
   with(R/f'logs/qwen_selection_WG_{name}.log').open('ab')as log:result=subprocess.run(['ssh','node01','bash','-s'],input=script.encode(),stdout=log,stderr=subprocess.STDOUT)
   if result.returncode:pulse('failed_worker',condition=name,returncode=result.returncode);return
   dest=D/'WG_scores';dest.mkdir(exist_ok=True);subprocess.run(['rsync','-a','--exclude=*_inputs.private.json','node01:/home/dell/Def/results/audit/crossmodel287/qwen_selection_WG/',str(dest)+'/'],check=True)
 pulse('all21_conditions_scored_ready_for_frozen_selection_read')
if __name__=='__main__':main()
