"""Prepare and register a norm-only two-card Vicuna job after the CPU asset copy."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
from transformers import AutoTokenizer
from crossmodel287_assets_and_render import model_path,render,fastchat_template
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';D=C/'vicuna_norm_node01';D.mkdir(exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def pulse(phase,**kw):(D/'controller_live.json').write_text(json.dumps({'utc':utc(),'pid':os.getpid(),'phase':phase,'no_training':True,**kw},indent=2)+'\n')
def main():
 assert not(D/'plan.json').exists();worker=R/'tools/handoff_20261106/crossmodel287_vicuna_norm_node01.py';source=R/'results/style_intervention/old_recipe_targets.json';teacher=json.loads(source.read_text());tok=AutoTokenizer.from_pretrained(str(model_path('vicuna')),local_files_only=True)
 import crossmodel287_assets_and_render as helper
 rows=[{'id':r['id'],'text':r['text'],'input_ids_sha256':helper.digest(render(tok,'vicuna',r['text']))}for r in teacher['keep']];private=D/'keep60.private.json';private.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');private.chmod(0o600)
 metadata=json.loads((C/'metadata/vicuna/api_metadata.json').read_text());expected={r['rfilename']:r['lfs']['sha256']for r in metadata['siblings']if r['rfilename'].endswith('.bin')};path=model_path('vicuna')
 expected.update({p.name:sha(p)for p in path.iterdir()if p.name.startswith('tokenizer')or p.name in ['config.json','special_tokens_map.json','added_tokens.json','generation_config.json']});assert len([n for n in expected if n.endswith('.bin')])==3
 plan={'utc':utc(),'model_relative_path':'models/crossmodel287/vicuna/c8327bf999adbd2efe2e75f6509fa01436100dc2','model_files_sha256':expected,'private_inputs_sha256':sha(private),'source_teacher_sha256':sha(source),'effective_U1_protocol_sha256':sha(C/'protocol_effective_addendum5_U1.json'),'worker_sha256':sha(worker),'fastchat_template':fastchat_template(),'physical_gpus':[1,2],'norm_rule':'native model.layers[12] output at last prompt token; all60; float32 CPU L2 then median; rho=0.9M','allocation_deadline_utc':'2026-11-09T15:00:00+00:00','model_native_bf16_no_quantization_no_CPU_offload':True,'registered_launch_job_shared_locks_unchanged_gate':True,'node_backend_is_reported':True,'norm_only_no_targets_or_alpha0_generation_or_training':True};(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 with(R/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{utc()} VICUNA_NORM_NODE01_PLAN SHA={sha(D/"plan.json")} wait_asset_copy_then_original_node_launch_helper GPU1+2; float32_CPU_norm_same_native_block_hook; no_training_or_generation.\n')
 remote='/home/dell/Def/results/audit/crossmodel287/vicuna_norm_node01';subprocess.run(['ssh','node01','mkdir','-p',remote],check=True)
 for p in [D/'plan.json',private]:subprocess.run(['rsync','-a',str(p),'node01:'+remote+'/'],check=True)
 subprocess.run(['rsync','-a',str(worker),'node01:/home/dell/Def/tools/handoff_20261106/'],check=True)
 pulse('waiting_existing_asset_transfer',transfer_pid=2820081)
 while subprocess.run(['ps','-p','2820081'],stdout=subprocess.DEVNULL).returncode==0:
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,11,9,14,57,tzinfo=datetime.timezone.utc):pulse('deferred_asset_copy_near_allocation_end');return
  time.sleep(10);pulse('waiting_existing_asset_transfer',transfer_pid=2820081)
 script='''source /home/dell/Def/tools/handoff_20261106/node01_launch_round9.sh
cd /home/dell/Def
exec 7>>logs/idle_gpu1.lock
exec 8>>logs/idle_gpu2.lock
flock 7
flock 8
unset NOGPU
export DEVICE=cuda:1
while ! wait_gpu cuda:1 || ! wait_gpu cuda:2; do sleep 15; done
launch_job env CUDA_VISIBLE_DEVICES=1,2 DEVICE=cuda:0 HF_HUB_OFFLINE=1 USE_TF=0 USE_FLAX=0 /data/ray/env/bin/python -u tools/handoff_20261106/crossmodel287_vicuna_norm_node01.py
'''
 pulse('remote_norm_job_started_waiting_receipt')
 with(R/'logs/vicuna_norm_node01.log').open('ab')as log:result=subprocess.run(['ssh','node01','bash','-s'],input=script.encode(),stdout=log,stderr=subprocess.STDOUT)
 subprocess.run(['rsync','-a','--exclude=keep60.private.json','node01:'+remote+'/',str(D)+'/'],check=True);pulse('complete'if(D/'complete.json').exists()else'not_complete',remote_returncode=result.returncode)
if __name__=='__main__':main()
