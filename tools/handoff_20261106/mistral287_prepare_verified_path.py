from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';D=C/'mistral';D.mkdir(exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def pulse(phase,**kw):save(D/'live.json',{'utc':utc(),'pid':os.getpid(),'phase':phase,'training_started':False,**kw})
def main():
 spec=json.loads((C/'protocol_effective_addendum6_Mistral.json').read_text());m=spec['models']['mistral'];path=Path('/data/models/Mistral-7B-Instruct-v0.3');path.mkdir(parents=True,exist_ok=True)
 from transformers import AutoTokenizer
 if '--norm'in sys.argv:
  import numpy as np,torch,transformers
  assert os.environ.get('CUDA_VISIBLE_DEVICES')=='3';assert json.loads((D/'assets_verified_actual_path.json').read_text())['all3_weights_verified'];tok=AutoTokenizer.from_pretrained(str(path),local_files_only=True);teacher=json.loads((R/'results/style_intervention/old_recipe_targets.json').read_text())
  execution={'utc':utc(),'worker_sha256':sha(Path(__file__)),'protocol_sha256':sha(C/'protocol_effective_addendum6_Mistral.json'),'assets_sha256':sha(D/'assets_verified_actual_path.json'),'torch':torch.__version__,'transformers':transformers.__version__,'physical_gpu':3,'host':os.uname().nodename,'device_uuid':subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader','-i','3'],text=True).strip(),'hook':'native model.layers[9] OUTPUT; last prompt token; no padding','no_training':True};save(D/'norm_execution.json',execution);pulse('loading_norm_model')
  from transformers import AutoModelForCausalLM
  mdl=AutoModelForCausalLM.from_pretrained(str(path),local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval();assert len(mdl.model.layers)==32
  values=[]
  for row in teacher['keep']:
   ids=tok.apply_chat_template([{'role':'user','content':row['text']}],add_generation_prompt=True,return_tensors='pt').to('cuda:0');box=[]
   def hook(module,args,out):
    assert module is mdl.model.layers[9];h=out[0]if isinstance(out,tuple)else out;box.append(h[0,-1].detach().float().cpu())
   handle=mdl.model.layers[9].register_forward_hook(hook)
   try:
    with torch.inference_mode():mdl(input_ids=ids,use_cache=False)
   finally:handle.remove()
   assert len(box)==1 and torch.isfinite(box[0]).all();values.append({'id':row['id'],'norm':float(box[0].norm())});save(D/'norm_rows.json',values);pulse('norm',completed=len(values),total=60)
  med=float(np.median([x['norm']for x in values]));save(D/'norm_complete.json',{'utc':utc(),'n':60,'block':9,'keep60_median':med,'rho':0.9*med,'execution_sha256':sha(D/'norm_execution.json'),'no_training':True});pulse('norm_complete',median=med,rho=.9*med);return
 from huggingface_hub import hf_hub_download
 meta=json.loads((C/'mistral_discovery.json').read_text());wanted=[s for s in meta['siblings']if s['rfilename']in ['config.json','generation_config.json','model.safetensors.index.json','tokenizer.json','tokenizer.model','tokenizer_config.json','special_tokens_map.json','README.md','LICENSE']or s['rfilename'].startswith('model-')and s['rfilename'].endswith('.safetensors')];wanted.sort(key=lambda x:x['rfilename'].endswith('.safetensors'));assets={}
 for row in wanted:
  name=row['rfilename'];pulse('download',file=name)
  for attempt in range(5):
   try:p=Path(hf_hub_download(repo_id=m['repo'],filename=name,revision=m['revision'],endpoint='https://hf-mirror.com',token=False,local_dir=path));break
   except Exception:
    if attempt==4:raise
    time.sleep(5)
  actual=sha(p);expected=(row.get('lfs')or{}).get('sha256');assert expected is None or expected==actual;assets[name]={'sha256':actual,'expected_sha256':expected,'verified':True};save(D/'assets_verified_actual_path.json',{'utc':utc(),'files':assets,'all3_weights_verified':sum(n.endswith('.safetensors')for n in assets)==3,'credential_used':False})
  if name=='tokenizer_config.json':pass
 tok=AutoTokenizer.from_pretrained(str(path),local_files_only=True);fixture=tok.apply_chat_template([{'role':'system','content':'System fixture.'},{'role':'user','content':'Hello.'}],tokenize=False,add_generation_prompt=True);teacher=json.loads((R/'results/style_intervention/old_recipe_targets.json').read_text());lengths=[];checks=[]
 for row,t in zip(teacher['fit'],teacher['ref_targets']):
  prefix=tok.apply_chat_template([{'role':'user','content':row['text']}],add_generation_prompt=True);target=tok(t,add_special_tokens=False)['input_ids'];assert target and tok.unk_token_id not in target and not any(i in tok.all_special_ids for i in target);decoded=tok.decode(target,clean_up_tokenization_spaces=False);labels=[-100]*len(prefix)+target;assert labels[len(prefix):]==target;lengths.append(len(target));checks.append({'id':row['id'],'target_tokens':len(target),'roundtrip':decoded==t,'mask_ok':True})
 save(D/'template_and_U1.json',{'utc':utc(),'benign_fixture_render':fixture,'native_template':tok.chat_template,'native_system_role_supported':True,'target_checks':checks,'target_token_min':min(lengths),'target_token_max':max(lengths),'target_token_sorted':sorted(lengths),'no_GPU_outputs_before_template_check':True});pulse('assets_template_complete_waiting_idle_gpu0')
 script='''source /data/HZX/Def/night/launch.sh
cd /data/HZX/Def
exec 8>>logs/idle_gpu0.lock
flock 8
unset NOGPU
export DEVICE=cuda:0
while ! wait_gpu cuda:0; do sleep 20; done
launch_job env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN CUDA_VISIBLE_DEVICES=0 DEVICE=cuda:0 HF_HUB_OFFLINE=1 /home/kemove/anaconda3/envs/HZX_GLA/bin/python -u tools/handoff_20261106/mistral287_prepare.py --norm
'''
 subprocess.run(['bash','-s'],input=script.encode(),check=True)
if __name__=='__main__':main()
