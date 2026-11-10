"""CPU-only complete static-family render manifest, including P2 position proof."""
from pathlib import Path
import datetime, hashlib, json, sys
import numpy as np
from transformers import AutoTokenizer
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
D=R/'results/audit/sorry296/downloads.private/sorry-bench-202503'
sys.path.insert(0,str(R/'tools/handoff_20261106'))
from crossmodel287_assets_and_render import model_path
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()
def lines(p):
 with p.open()as f:return [json.loads(line)for line in f]
def main():
 destination=U/'static_render_manifest.json';assert not destination.exists()
 fixed=load(U/'fixed_texts.private.json')
 suffixes=['logical_appeal','authority_endorsement','misrepresentation','evidence-based_persuasion','expert_endorsement','ascii','caesar','morse','atbash','translate-ml','translate-ta','translate-mr','translate-zh-cn','translate-fr']
 base=lines(D/'question.jsonl')
 files={'base':D/'question.jsonl',**{s:D/f'question_{s}.jsonl'for s in suffixes}}
 sources={k:lines(p)for k,p in files.items()}
 result={'utc_started':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'source_sha256':{k:sha(p)for k,p in files.items()},'fixed_texts_sha256':sha(U/'fixed_texts.private.json'),
   'models':{},'model_forward_calls':0,'new_test_generation':False}
 for key in ['llama','qwen','gemma','mistral']:
  if key=='llama':path=Path('/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659')
  elif key=='mistral':path=Path(load(R/'results/audit/crossmodel287/mistral/assets_verified_actual_path.json')['model_path'])
  else:path=model_path(key)
  tok=AutoTokenizer.from_pretrained(str(path),local_files_only=True)
  families={};prefix_fail=[]
  def encode(prompt):return tok.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True)
  def summarize(records):
   sizes=[r['tokens']for r in records]
   return {'n':len(records),'min':min(sizes),'median':float(np.median(sizes)),
           'p95':float(np.quantile(sizes,.95)),'max':max(sizes),'over_4096':sum(n>4096 for n in sizes),'rows':records}
  for name,rows in sources.items():
   rec=[]
   for r in rows:
    ids=encode(r['turns'][0]);rec.append({'id':r['question_id'],'tokens':len(ids),'input_ids_sha256':digest(ids)})
   families[name]=summarize(rec)
  for name in ['deepinception','refusal_suppression','prefix_P1','prefix_P2']:
   rec=[]
   for r in base:
    prompt=r['turns'][0]
    if name=='deepinception':ids=encode(fixed['deep_template'].format(instruction=prompt));position=len(ids)-1
    elif name=='refusal_suppression':ids=encode(fixed['refusal_suppression']+'\n\n'+prompt);position=len(ids)-1
    else:
     native=encode(prompt)
     text=tok.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True,tokenize=False)
     ids=tok(text+fixed['prefill'],add_special_tokens=False)['input_ids']
     if ids[:len(native)]!=native:prefix_fail.append({'id':r['question_id'],'family':name,'reason':'native token prefix changed'})
     position=len(ids)-1 if name=='prefix_P1'else len(native)-1
    rec.append({'id':r['question_id'],'tokens':len(ids),'input_ids_sha256':digest(ids),'injection_position_zero_based':position})
   families[name]=summarize(rec)
  result['models'][key]={'families':families,'P2_original_native_prefix_preserved':not prefix_fail,
    'prefix_failure_IDs':prefix_fail,'tokenizer_config_sha256':sha(path/'tokenizer_config.json')}
 result['utc_completed']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 destination.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:{'families':len(v['families']),'prefix_gate':v['P2_original_native_prefix_preserved'],
       'largest_prompt_tokens':max(f['max']for f in v['families'].values())}for k,v in result['models'].items()}))
 print('OUTPUT_SHA',sha(destination))
if __name__=='__main__':main()
