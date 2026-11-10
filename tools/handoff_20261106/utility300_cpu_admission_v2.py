"""CPU utility parser and native-prefix token checks; no model forward/effect."""
from pathlib import Path
import datetime, hashlib, json, sys
from transformers import AutoTokenizer
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
sys.path.insert(0,str(R/'tools/handoff_20261106'))
from crossmodel287_assets_and_render import model_path
from utility300_scoring import gsm8k_correct
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def main():
 dest=U/'utility_cpu_admission_v2.json';assert not dest.exists()
 gsm=load(U/'utility.private/gsm8k200.json');arc=load(U/'utility.private/arc200.json')
 assert all(gsm8k_correct('#### '+str(x['gold_numeric']),x['gold_numeric'])for x in gsm)
 manifest=load(U/'utility200_manifest.json');checks={}
 for key in ['llama','qwen','gemma','mistral']:
  if key=='llama':
   path=Path('/data/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659')
  elif key=='mistral':
   # Use the verified actual asset receipt, not the earlier model-pool helper.
   path=Path(load(R/'results/audit/crossmodel287/mistral/assets_verified_actual_path.json')['model_path'])
  else:path=model_path(key)
  tok=AutoTokenizer.from_pretrained(str(path),local_files_only=True)
  failed=[];records=[];actual={}
  expected=manifest['ARC_CPU_token_checks'][key]['letters']
  for row in arc:
   messages=[{'role':'user','content':row['prompt']}]
   native=tok.apply_chat_template(messages,add_generation_prompt=True)
   text=tok.apply_chat_template(messages,add_generation_prompt=True,tokenize=False)
   options={}
   for letter in row['candidate_letters']:
    whole=tok(text+letter,add_special_tokens=False)['input_ids']
    suffix=whole[len(native):] if whole[:len(native)]==native else None
    options[letter]=suffix
    if suffix is None or len(suffix)!=1:failed.append({'id':row['id'],'option':letter,'appended_suffix_ids':suffix})
    elif letter not in actual:actual[letter]=suffix
    elif suffix!=actual[letter]:failed.append({'id':row['id'],'option':letter,'appended_suffix_ids':suffix})
   records.append({'id':row['id'],'option_suffixes':options})
  assert len(actual)==4 and len({v[0] for v in actual.values()})==4
  checks[key]={'n':len(arc),'passed':not failed,'actual_letters':actual,'previous_standalone_letters':expected,'previous_mapping_equal':actual==expected,'failure_ids_and_tokens':failed,
      'joint_tokenization_checked':True,'option_records_sha256':hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()}
 x={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'GSM_gold_roundtrip':len(gsm),
    'scoring_code_sha256':sha(R/'tools/handoff_20261106/utility300_scoring.py'),
    'ARC_native_prefix_checks':checks,'actual_model_forward':False,
    'utility_effect_read':False,'formal_generation_admitted':False,
    'remaining':'ARC injected forward/logit gate; generation/backend admission'}
 dest.write_text(json.dumps(x,indent=2)+'\n')
 print(json.dumps({k:{'n':v['n'],'passed':v['passed'],'failures':len(v['failure_ids_and_tokens'])}for k,v in checks.items()}))
 print('OUTPUT_SHA',sha(dest))
if __name__=='__main__':main()
