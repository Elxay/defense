"""Prepare signed transfer targets and fixed native-selection inputs, without gradients."""
from pathlib import Path
import datetime,hashlib,json,os,sys
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287';sys.path.insert(0,str(R/'src'))
from judge.refusal import new_rule
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def objsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def main():
 protocol=O/'protocol_effective_addenda3_4.json';spec=json.loads(protocol.read_text());assert spec['target_source_branch']['decision']=='B'
 old=R/spec['target_source_branch']['teacher_file'];assert sha(old)==spec['target_source_branch']['teacher_sha256'];teacher=json.loads(old.read_text())
 native=O/'qwen_private';pack={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':'qwen','branch':'Llama_donor_target_text_transfer','effective_protocol_sha256':sha(protocol),'teacher_cache_sha256':sha(old),'fit':[],'keep':[]}
 for row,target in zip(teacher['fit'],teacher['ref_targets']):pack['fit'].append({'id':row['id'],'prompt':row['text'],'target':target,'target_source_model':'Llama-3.1-8B-Instruct','target_text_sha256':hashlib.sha256(target.encode()).hexdigest()})
 for row in teacher['keep']:
  file=native/'keep_alpha0'/(row['id']+'.json');x=json.loads(file.read_text());pack['keep'].append({'id':row['id'],'prompt':row['text'],'target':x['output'],'target_source_model':'Qwen2.5-7B-Instruct','native_file_sha256':sha(file)})
 assert len(pack['fit'])==12 and len(pack['keep'])==60
 private=O/'qwen_transfer_targets.private.json';assert not private.exists();save(private,pack);private.chmod(0o600)
 sources={};val={}
 for name in ['STAGE0_VAL_PAIR.json','STAGE0_VAL_HB_PAIR.json','STAGE0_VAL_HB_PAIR2.json','STAGE0_VAL_HB_PAIR3.json']:
  p=R/'results/audit'/name;sources[str(p.relative_to(R))]=sha(p)
  for row in json.loads(p.read_text()):
   if row['result'].get('success'):val[row['behavior_id']]=row['result']['best_prompt']
 ids_path=R/'configs/stage0_data/val70_ids.json';keys=json.loads(ids_path.read_text())['ids'];assert len(keys)==len(set(keys))==70 and all(k in val for k in keys);sources[str(ids_path.relative_to(R))]=sha(ids_path)
 legalpath=R/'data/legal_val_items.json';legal=json.loads(legalpath.read_text());basepath=R/'results/audit/LEGALVALB_none.json';base=json.loads(basepath.read_text());eligible=[k for k,v in base.items()if not new_rule(v['text'])];assert len(legal)==400 and len(eligible)==388
 sources[str(legalpath.relative_to(R))]=sha(legalpath);sources[str(basepath.relative_to(R))]=sha(basepath)
 inputs={'created_utc':pack['created_utc'],'val70':[{'id':k,'prompt':val[k],'prompt_sha256':hashlib.sha256(val[k].encode()).hexdigest()}for k in keys],
   'legal400':[{'id':row['key'],'prompt':row['prompt'],'prompt_sha256':hashlib.sha256(row['prompt'].encode()).hexdigest(),'in_fixed388':row['key']in eligible}for row in legal],
   'legal388_ids':eligible,'sources':sources,'effective_protocol_sha256':sha(protocol)}
 file=O/'native_selection_inputs.private.json';assert not file.exists();save(file,inputs);file.chmod(0o600)
 public={'utc':pack['created_utc'],'effective_protocol_sha256':sha(protocol),'transfer_targets_private_sha256':sha(private),'n_transfer_targets':12,'n_native_keep_targets':60,'native_selection_inputs_private_sha256':sha(file),'source_sha256':sources,
   'val70_ids':keys,'legal388_ids':eligible,'legal400_batch8_ids':[[r['id']for r in inputs['legal400'][i:i+8]]for i in range(0,400,8)],
   'row_signatures':{'val70':{r['id']:r['prompt_sha256']for r in inputs['val70']},'legal400':{r['id']:r['prompt_sha256']for r in inputs['legal400']}},
   'worker_scheduling':'native baseline generation waits PAIR_GPU_complete; unchanged0.9norm/layer; no gradients before fresh audits','raw_prompt_or_target_text_published':False}
 save(O/'transfer_and_native_selection_inputs_manifest.json',public)
 print(json.dumps({'manifest_sha256':sha(O/'transfer_and_native_selection_inputs_manifest.json'),'transfer_target_source':'12Llama/0Qwen','native_keep_source':'60Qwen','val70':70,'legal_generate':400,'legal_selection_mask':388,'training_allowed':False}))
if __name__=='__main__':main()
