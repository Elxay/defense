"""Two-layer, exact last-prompt-position native Mistral norm audit; no generation."""
from pathlib import Path
import datetime,hashlib,json,os,socket,subprocess,statistics
import torch,transformers
from transformers import AutoModelForCausalLM,AutoTokenizer
R=Path('/home/dell/Def');D=R/'results/audit/crossmodel287/mistral_recheck20'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,x):q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='1';plan=json.loads((D/'plan.json').read_text());assert sha(Path(__file__))==plan['worker_sha256'];path=R/plan['model_relative_path'];inputs=D/'inputs.private.json';assert sha(inputs)==plan['inputs_sha256'];rows=json.loads(inputs.read_text());assert len(rows)==20
 for n,v in plan['files_sha256'].items():assert sha(path/n)==v,n
 tok=AutoTokenizer.from_pretrained(str(path),local_files_only=True);model=AutoModelForCausalLM.from_pretrained(str(path),local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'}).eval();assert len(model.model.layers)==32
 result={'utc_started':utc(),'pid':os.getpid(),'host':socket.gethostname(),'physical_gpu':1,'torch':torch.__version__,'transformers':transformers.__version__,'plan_sha256':sha(D/'plan.json'),'rows':[],'no_generation_or_training':True}
 names={id(m):n for n,m in model.named_modules()}
 for row in rows:
  ids=tok.apply_chat_template([{'role':'user','content':row['text']}],add_generation_prompt=True);assert digest(ids)==row['input_ids_sha256'];position=len(ids)-1;captured={};handles=[]
  for layer in [9,10]:
   def hook(module,args,out,layer=layer):
    assert module is model.model.layers[layer]and names[id(module)]==f'model.layers.{layer}';h=out[0]if isinstance(out,tuple)else out;assert list(h.shape)==[1,len(ids),4096];assert layer not in captured;v=h[0,position,:].detach().float().cpu();captured[layer]={'norm':float(v.norm()),'module':names[id(module)],'shape':list(h.shape),'position':position}
   handles.append(model.model.layers[layer].register_forward_hook(hook))
  try:
   with torch.inference_mode():model(input_ids=torch.tensor([ids],device='cuda:0'),use_cache=False)
  finally:
   for h in handles:h.remove()
  assert set(captured)=={9,10};result['rows'].append({'id':row['id'],'input_ids_sha256':row['input_ids_sha256'],'last_token_id':ids[-1],'last_token_display':tok.convert_ids_to_tokens(ids[-1]),'layers':captured,'original_layer9_norm':row['original_norm']});save(D/'progress.json',result)
 result['summary']={}
 for layer in [9,10]:
  x=[r['layers'][layer]['norm']for r in result['rows']];result['summary'][str(layer)]={'n':len(x),'mean':statistics.mean(x),'median':statistics.median(x),'sample_SD':statistics.stdev(x),'min':min(x),'max':max(x)}
 result['layer9_max_abs_difference_from_original']=max(abs(r['layers'][9]['norm']-r['original_layer9_norm'])for r in result['rows']);result['utc_completed']=utc();save(D/'complete.json',result);print(json.dumps(result['summary']))
if __name__=='__main__':main()
