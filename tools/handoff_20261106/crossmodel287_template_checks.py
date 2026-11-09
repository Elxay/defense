"""Native plus actual A/B template checks, independent of weight download status."""
from pathlib import Path
import datetime,hashlib,json,sys
from transformers import AutoTokenizer
from crossmodel287_assets_and_render import model_path,render,digest,fastchat_template
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=json.loads((R/'results/style_intervention/old_recipe_targets.json').read_text());rows=source['fit']+source['keep']
 text=(R/'docs/227_SYSTEM_PROMPTS.txt').read_text();bodies={'SYS_A':text.split('A_short\n',1)[1].split('\n\nB_detailed\n',1)[0],'SYS_B':text.split('B_detailed\n',1)[1].strip()}
 assert hashlib.sha256(bodies['SYS_A'].encode()).hexdigest().startswith('d33c70fd')and hashlib.sha256(bodies['SYS_B'].encode()).hexdigest().startswith('3606acab')
 for key in ['qwen','gemma','vicuna']:
  receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':key,'records':[],
           'actual_AB_body_sha256':{n:hashlib.sha256(t.encode()).hexdigest()for n,t in bodies.items()},'GPU_used':False,'weight_integrity_claimed':False}
  try:
   path=model_path(key);tok=AutoTokenizer.from_pretrained(str(path),local_files_only=True)
   for row in rows:
    base=render(tok,key,row['text']);assert base==render(tok,key,row['text'])
    receipt['records'].append({'id':row['id'],'condition':'native','input_ids_sha256':digest(base),'tokens':len(base)})
    for label,body in bodies.items():
     custom=render(tok,key,row['text'],body);assert custom!=base
     if key=='gemma':assert custom==tok.apply_chat_template([{'role':'user','content':body+'\n\n'+row['text']}],add_generation_prompt=True)
     elif key=='qwen':assert custom==tok.apply_chat_template([{'role':'system','content':'You are a helpful assistant.\n\n'+body},{'role':'user','content':row['text']}],add_generation_prompt=True)
     else:
      c=fastchat_template();expected=tok(c['system_message']+'\n\n'+body+' USER: '+row['text']+' ASSISTANT:',add_special_tokens=True)['input_ids'];assert expected==custom
     receipt['records'].append({'id':row['id'],'condition':label,'input_ids_sha256':digest(custom),'tokens':len(custom)})
   if key=='gemma':
    try:tok.apply_chat_template([{'role':'system','content':'fixture'},{'role':'user','content':'Hello'}],add_generation_prompt=True)
    except Exception:receipt['system_role_rejected']=True
    else:raise AssertionError('Unexpected Gemma system-role support')
   receipt.update(phase='passed',checked_inputs=len(receipt['records']),config_sha256=sha(path/'config.json'),tokenizer_config_sha256=sha(path/'tokenizer_config.json'))
   if key=='vicuna':receipt['fastchat_source']=json.loads((O/'metadata/fastchat_source.json').read_text())
  except Exception as e:receipt.update(phase='blocked',error_type=type(e).__name__)
  path=O/(key+'_actual_AB_render.json');path.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'model':key,'phase':receipt['phase'],'checks':len(receipt['records']),'sha256':sha(path)}),flush=True)
if __name__=='__main__':main()
