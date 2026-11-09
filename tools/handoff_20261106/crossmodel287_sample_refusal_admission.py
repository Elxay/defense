"""Freeze the seeded v2-negative review set after complete native alpha-zero outputs."""
from pathlib import Path
import datetime,hashlib,json,random,sys
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287';sys.path.insert(0,str(R/'src'))
from judge.refusal import new_rule
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 key=sys.argv[1];assert key in ['qwen','gemma','vicuna'];protocol=O/'protocol_effective_addenda3_4.json';cfg=json.loads(protocol.read_text());seed=cfg['refusal_admission']['seeds'][key]
 inputs=json.loads((O/'native_selection_inputs.private.json').read_text());folder=O/'native_selection_private'/key
 assert all((folder/'legal400'/(r['id']+'.json')).exists()for r in inputs['legal400'])and all((folder/'val70'/(r['id']+'.json')).exists()for r in inputs['val70'])
 sets={'legal388':[r for r in inputs['legal400']if r['in_fixed388']],'val70':inputs['val70']};selected=[];populations={};ids={}
 for name,rows in sets.items():
  kind='legal400'if name=='legal388'else'val70';pool=[];records={}
  for r in rows:
   p=folder/kind/(r['id']+'.json');x=json.loads(p.read_text());assert x['prompt_sha256']==r['prompt_sha256'];records[r['id']]=(r,x,p)
   if not new_rule(x['result']['text']):pool.append(r['id'])
  chosen=random.Random(seed[name]).sample(sorted(pool),min(30,len(pool)));ids[name]=chosen;populations[name]={'eligible_rows':len(rows),'v2_negative_pool':len(pool),'sample_n':len(chosen),'seed':seed[name],'census':len(pool)<30}
  for identifier in chosen:
   r,x,p=records[identifier];selected.append({'id':identifier,'set':name,'request':r['prompt'],'response':x['result']['text'],'source_file_sha256':sha(p),'n_chars':len(x['result']['text']),'new_tokens':x['result']['new_tokens'],'eos':x['result']['eos']})
 random.Random(seed['presentation']).shuffle(selected);blind=[];mapping=[]
 for i,row in enumerate(selected):
  b=f'review{i:03d}';blind.append({'blind_id':b,'request':row['request'],'response':row['response']});mapping.append({'blind_id':b,**row})
 prefix=O/(key+'_refusal_admission');prefix.mkdir(exist_ok=True);assert not(prefix/'sample_manifest.json').exists(),'Do not resample an existing review'
 write(prefix/'ids_only.json',ids);write(prefix/'blind.private.json',blind);write(prefix/'mapping.private.json',mapping)
 for name in ['blind.private.json','mapping.private.json']:(prefix/name).chmod(0o600)
 manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':key,'protocol_sha256':sha(protocol),'sampling_code_sha256':sha(Path(__file__)),'populations':populations,'presentation_seed':seed['presentation'],'ids_only_sha256':sha(prefix/'ids_only.json'),'blind_file_sha256':sha(prefix/'blind.private.json'),'private_mapping_sha256':sha(prefix/'mapping.private.json'),'per_item_exposed_fields':['blind_id','request','response'],'review_labels_collected':False,'training_allowed':False}
 write(prefix/'sample_manifest.json',manifest)
 with(R/'docs/PREREG_LOG.txt').open('a')as f:f.write(manifest['utc']+' CROSSMODEL287_REFUSAL_REVIEW_SAMPLE_FROZEN model='+key+' SHA='+sha(prefix/'sample_manifest.json')+' ids_only_SHA='+manifest['ids_only_sha256']+' before model review/gradients.\n')
 print(json.dumps(manifest))
if __name__=='__main__':main()
