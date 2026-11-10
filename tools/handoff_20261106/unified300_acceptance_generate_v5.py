"""Generate only the fixed S0 100x3 engineering panel; no selection/test rates."""
from pathlib import Path
import datetime,hashlib,json,os,socket,sys,time,shutil
import numpy as np
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
sys.path.insert(0,str(R/'tools/handoff_20261106'));sys.path.insert(0,str(R/'src'))
from batched_injection300 import generate_batch_with_injection,ids_sha
from gen.common import generate_with_injection
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def main():
 key,card=sys.argv[1],int(sys.argv[2]);assert os.environ['CUDA_VISIBLE_DEVICES']==str(card)
 plan=load(U/'acceptance_generation_plan_v5.json');assert sha(__file__)==plan['worker_sha256']
 assert sha(U/'calibration700.private.json')==plan['calibration_sha256']
 assert sha(R/'src/gen/common.py')==plan['legacy_core_sha256']
 assert sha(R/'tools/handoff_20261106/batched_injection300.py')==plan['batch_core_sha256']
 spec=plan['models'][key];d=U/'acceptance_v5'/key
 def pulse(phase,**kw):save(d/'live.json',dict(utc=utc(),pid=os.getpid(),host=socket.gethostname(),physical_gpu=card,phase=phase,test_effect_read=False,**kw))
 pulse('loading')
 tok=AutoTokenizer.from_pretrained(spec['path'],local_files_only=True);tok.padding_side='left'
 if tok.pad_token_id is None:tok.pad_token=tok.eos_token
 model=AutoModelForCausalLM.from_pretrained(spec['path'],local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa').eval()
 source={r['id']:r for r in load(U/'calibration700.private.json')}
 encoded={k:tok.apply_chat_template([{'role':'user','content':source[k]['prompt']}],add_generation_prompt=True)for k in plan['IDs100']}
 ordered=sorted(encoded,key=lambda k:(len(encoded[k]),hashlib.sha256(('20261240:'+k).encode()).hexdigest()))
 vecs={}
 for condition,v in spec['vectors'].items():
  assert sha(v['path'])==v['sha256'];vecs[condition]=np.load(v['path'])
 assert len({v.shape for v in vecs.values()})==1
 zero=np.zeros_like(vecs['s3']);vecs={'alpha0':zero,**vecs}
 for k,reference in plan['reused_legacy_records'].items():
  source_path=Path(reference['source_path']);assert sha(source_path)==reference['sha256']
  condition,row_id=k.split('/',1);target=d/'generation.private/cap2400'/condition/'legacy_single'/(row_id+'.json');target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert sha(target)==reference['sha256']
  else:shutil.copy2(source_path,target)
 eos=model.generation_config.eos_token_id;eos={eos}if isinstance(eos,int)else set(eos)
 for cap in plan['caps']:
  batch_size=spec['batch_by_cap'][str(cap)]
  for condition in ['alpha0','s3','random']:
   vec=vecs[condition];alpha=0 if condition=='alpha0'else 1
   srcsha=None if condition=='alpha0'else spec['vectors'][condition]['sha256']
   for path_name,b in [('legacy_single',1),('candidate_batch',batch_size)]:
    folder=d/'generation.private'/f'cap{cap}'/condition/path_name
    for n in range(0,len(ordered),b):
     members=ordered[n:n+b];paths=[folder/(k+'.json')for k in members]
     if all(p.exists()for p in paths):
      assert all(load(p)['signature']['plan_sha256']==sha(U/'acceptance_generation_plan_v5.json')or(condition+'/'+p.stem in plan['reused_legacy_records']and sha(p)==plan['reused_legacy_records'][condition+'/'+p.stem]['sha256'])for p in paths);continue
     pulse('generating',cap=cap,condition=condition,path=path_name,batch_size=b,completed_rows=n,total=100)
     batch_started_utc=utc();tick=time.monotonic();torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats()
     if path_name=='legacy_single':
      captured={};original=model.generate
      def tracked(*args,**kwargs):
       out=original(*args,**kwargs);captured['last_token']=int(out[0,-1]);return out
      model.generate=tracked
      try:record=generate_with_injection(model,tok,torch.tensor([encoded[members[0]]],device='cuda:0'),vec,layer=spec['layer'],max_new_tokens=cap,src_vec_sha256=srcsha,alpha=alpha)
      finally:model.generate=original
      record['eos']=captured['last_token']in eos;record['rho_runtime']=record['delta_norm_runtime'];record['input_ids_sha256']=ids_sha(encoded[members[0]]);records=[record]
     else:records=generate_batch_with_injection(model,tok,[encoded[k]for k in members],vec,layer=spec['layer'],max_new_tokens=cap,source_vector_sha256=srcsha,alpha=alpha)
     assert all(r['injection_count']==1 for r in records)
     if condition=='alpha0':assert all(r['rho_runtime']==0 for r in records)
     for k,record,p in zip(members,records,paths):
      value={'id':k,'prompt_sha256':source[k]['prompt_sha256'],'signature':{'plan_sha256':sha(U/'acceptance_generation_plan_v5.json'),'host':socket.gethostname(),'device_uuid':record['device_uuid'],'condition':condition,'engineering_alpha':alpha,'cap':cap,'path':path_name,'batch_ids':members,'source_vector_sha256':srcsha},'result':record}
      if p.exists():assert load(p)==value,'Partial batch replay differs; preserve and stop'
      else:save(p,value)
     torch.cuda.synchronize();free,total=torch.cuda.mem_get_info();outside=total-free-torch.cuda.memory_reserved();headroom=total-outside-torch.cuda.max_memory_reserved()
     save(d/'metrics'/f'cap{cap}_{condition}_{path_name}_start{n:03d}.json',{'utc_start':batch_started_utc,'utc_end':utc(),'rows':len(records),'elapsed_seconds':time.monotonic()-tick,'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'headroom_bytes':headroom,'device_free_bytes_after':free,'batch_ids':members,'batch_size':b,'plan_sha256':sha(U/'acceptance_generation_plan_v5.json')})
     if path_name=='candidate_batch'and headroom<3*1024**3:
      save(d/'memory_admission_failed.json',{'utc':utc(),'cap':cap,'condition':condition,'batch_size':b,'headroom_bytes':headroom,'formal_admitted':False,'next_action':'Deterministic smaller-B generation, preserve this candidate; never mix formal outputs'})
      pulse('candidate_memory_failed');return
 save(d/'generation_complete.json',{'utc':utc(),'N_prompts':100,'conditions':3,'caps':plan['caps'],'paths':2,'expected_files':600,'reused_legacy_rows':300,'newly_generated_expected':300,'label_gate_complete':False,'formal_admitted':False,'plan_sha256':sha(U/'acceptance_generation_plan_v5.json')})
 pulse('generated_waiting_paired_WG_and_v2_flip_gate')
if __name__=='__main__':
 try:main()
 except torch.cuda.OutOfMemoryError:
  key=sys.argv[1]
  save(U/'acceptance_v5'/key/'memory_admission_failed.json',{'utc':utc(),'reason':'OOM','formal_admitted':False,'next_action':'Preserve artifacts; test the next smaller predeclared B under a versioned plan'})
  raise
