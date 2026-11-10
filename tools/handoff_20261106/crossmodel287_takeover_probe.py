"""Bounded engineering probes; never replace the three frozen Qwen vectors."""
from pathlib import Path
import argparse,csv,datetime,gc,hashlib,json,os,signal,sys,time
import numpy as np
import torch
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';O=C/'takeover_20261110';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,x):q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['qwen','gemma']);a=ap.parse_args();plan=json.loads((O/'plan.json').read_text());assert sha(Path(__file__))==plan['probe_sha256']
 if a.mode=='qwen':
  assert os.environ.get('CUDA_VISIBLE_DEVICES')=='2';source=R/'tools/handoff_20261106/crossmodel287_train_generic.py';assert sha(source)==plan['generic_trainer_sha256'];text=source.read_text();prefix=text[:text.index('opt=torch.optim.Adam')];block=text[text.index('opt=torch.optim.Adam'):text.index("v=(cfg['norm']*theta.detach()")];results={}
  for seed in [3,4,5]:
   config=R/f'configs/qwen_vec_s{seed}.json';sys.argv=[str(source),'--config',str(config),'--device','cuda:0'];ns={};exec(compile(prefix,str(source)+'#replay_prefix','exec'),ns)
   init=ns['theta'].detach().cpu().numpy();final=np.load(C/f'qwen_vec_s{seed}/v.npy');iv=init.astype('float64');fv=final.astype('float64');row={'seed':seed,'utc':utc(),'init_provenance':'replayed current frozen trainer prefix; historical init bytes were not saved','init_raw_sha256':hashlib.sha256(init.tobytes()).hexdigest(),'final_file_sha256':sha(C/f'qwen_vec_s{seed}/v.npy'),'cos_final_reconstructed_init':float(fv@iv/np.linalg.norm(fv)/np.linalg.norm(iv)),'difference_L2':float(np.linalg.norm(fv-iv)),'norm':float(np.linalg.norm(fv)),'encoding_checks':0}
   expected={r['fit_id']:r for r in csv.DictReader((C/'U1_tokenization_rows.csv').open())if r['model']=='qwen'};teacher=json.loads((R/'results/style_intervention/old_recipe_targets.json').read_text());assert ns['ref_targets']==teacher['ref_targets']
   for r,tgt in zip(ns['fit'],ns['ref_targets']):
    ids,labels,plen=ns['render'](r['text'],tgt);assert digest(ids[0].tolist())==expected[r['id']]['training_ids_sha256'];assert labels[0,:plen].eq(-100).all();row['encoding_checks']+=1
   gradients=[]
   def capture():
    g=ns['theta'].grad;assert g is not None and torch.isfinite(g).all();gradients.append({'grad_L2':float(g.norm()),'grad_max_abs':float(g.abs().max()),'nonzero':int(g.count_nonzero()),'dim':g.numel()})
   if seed==3:
    ids,labels,plen=ns['render'](ns['fit'][0]['text'],ns['ref_targets'][0]);vector=ns['cfg']['norm']*ns['theta']/ns['theta'].norm()
    def hook(module,args,out):
     h=out[0].clone();h[0,plen-1]+=vector;return(h,)+out[1:]
    handle=ns['mdl'].model.layers[8].register_forward_hook(hook)
    try:logits=ns['mdl'](ids,use_cache=False).logits;loss=-torch.log_softmax(logits[0,plen-1:-1].float(),-1).gather(-1,labels[0,plen:].unsqueeze(-1)).mean();g=torch.autograd.grad(loss,ns['theta'])[0];assert torch.isfinite(g).all();row['single_target']={'loss':float(loss),'gradient_L2':float(g.norm()),'nonzero':int(g.count_nonzero())}
    finally:handle.remove()
    del logits,loss,g,vector,handle
    loop=block.replace("range(cfg['steps'])",'range(5)').replace('    opt.step()','    CAPTURE_GRAD()\n    opt.step()');ns['CAPTURE_GRAD']=capture;exec(compile(loop,str(source)+'#five_step_diagnostic','exec'),ns);row.update(five_step_losses=ns['losses'],gradients=gradients)
   results[str(seed)]=row;save(O/'qwen_diagnostic.json',{'utc':utc(),'source_sha256':sha(source),'plan_sha256':sha(O/'plan.json'),'results':results,'original_vectors_unchanged':True});del ns;gc.collect();torch.cuda.empty_cache()
  return
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='0'
 from transformers import AutoTokenizer,AutoModelForCausalLM
 sys.path.insert(0,str(R/'src'));from gen.common import generate_with_injection
 sys.path.insert(0,str(R/'tools/handoff_20261106'));from crossmodel287_assets_and_render import model_path,render
 private=O/'gemma_compile.private';private.mkdir(exist_ok=True);state={'utc':utc(),'pid':os.getpid(),'attention':'eager','formal_compile':False,'comparisons':[],'plan_sha256':sha(O/'plan.json')}
 def stop(sig,frame):state.update(utc=utc(),phase='timeout_incomplete');save(O/'gemma_compile_check.json',state);raise SystemExit(0)
 signal.signal(signal.SIGALRM,stop);signal.alarm(900)
 try:
  tok=AutoTokenizer.from_pretrained(str(model_path('gemma')),local_files_only=True);mdl=AutoModelForCausalLM.from_pretrained(str(model_path('gemma')),local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='eager').eval();assert mdl.config._attn_implementation=='eager';teacher=json.loads((R/'results/style_intervention/old_recipe_targets.json').read_text());rows=teacher['keep'][:5];assert [r['id']for r in rows]==plan['gemma_compile_ids'];v=np.zeros(3584,dtype=np.float32);original=mdl.forward;baseline={}
  for compiled in [False,True]:
   mdl.forward=torch.compile(original,fullgraph=False)if compiled else original
   for row in rows:
    ids=torch.tensor([render(tok,'gemma',row['text'])],device='cuda:0');start=time.monotonic();z=generate_with_injection(mdl,tok,ids,v,layer=12,max_new_tokens=120,device='cuda:0',alpha=0);save(private/(row['id']+('_compiled'if compiled else'_plain')+'.json'),z)
    if not compiled:baseline[row['id']]=z
    else:state['comparisons'].append({'id':row['id'],'byte_equal':z['text']==baseline[row['id']]['text'],'plain_text_sha256':hashlib.sha256(baseline[row['id']]['text'].encode()).hexdigest(),'compiled_text_sha256':hashlib.sha256(z['text'].encode()).hexdigest(),'elapsed_seconds':time.monotonic()-start})
    state.update(utc=utc(),phase='compiled'if compiled else'uncompiled',completed=len(state['comparisons']));save(O/'gemma_compile_check.json',state)
  state.update(utc=utc(),phase='complete');save(O/'gemma_compile_check.json',state)
 except Exception as e:state.update(utc=utc(),phase='failed_preserve_plain_results',exception_class=type(e).__name__);save(O/'gemma_compile_check.json',state);raise
 finally:signal.alarm(0)
if __name__=='__main__':main()
