"""Resolve official model revisions/configs without printing any credential."""
from pathlib import Path
import datetime,hashlib,json,os,shutil
import requests
from huggingface_hub import get_token
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287';O.mkdir(parents=True,exist_ok=True)
MODELS={'gemma':'google/gemma-2-9b-it','qwen':'Qwen/Qwen2.5-7B-Instruct','vicuna':'lmsys/vicuna-13b-v1.5'}
def main():
    token=get_token();out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'credential_available':bool(token),'disk_free_bytes':shutil.disk_usage(R).free,'models':{}}
    for key,repo in MODELS.items():
        item={'repo':repo,'attempts':[]}
        for endpoint in ['https://huggingface.co','https://hf-mirror.com']:
            headers={'Authorization':'Bearer '+token}if token and key=='gemma'else{}
            try:
                res=requests.get(endpoint+'/api/models/'+repo,params={'blobs':'true'},headers=headers,timeout=20);item['attempts'].append({'endpoint':endpoint,'metadata_status':res.status_code})
                if res.status_code!=200:continue
                meta=res.json();rev=meta['sha'];dest=O/'metadata'/key;dest.mkdir(parents=True,exist_ok=True);(dest/'api_metadata.json').write_text(json.dumps(meta,indent=2)+'\n');files={x['rfilename']:x for x in meta['siblings']};configs={}
                for name in ['config.json','tokenizer_config.json','README.md']:
                    z=requests.get(endpoint+'/'+repo+'/resolve/'+rev+'/'+name,headers=headers,timeout=30);configs[name]={'status':z.status_code}
                    if z.status_code==200:(dest/name).write_bytes(z.content);configs[name]['sha256']=hashlib.sha256(z.content).hexdigest()
                item.update(endpoint=endpoint,revision=rev,gated=meta.get('gated'),files=[{'name':n,'bytes':x.get('size'),'lfs_sha256':(x.get('lfs')or{}).get('sha256')}for n,x in files.items()if n.endswith(('.safetensors','.bin'))or n.endswith('.index.json')],metadata_sha256=hashlib.sha256((dest/'api_metadata.json').read_bytes()).hexdigest(),config_access=configs)
                if configs['config.json']['status']==200:
                    cfg=json.loads((dest/'config.json').read_text());item['config']={k:cfg.get(k)for k in ['model_type','architectures','hidden_size','num_hidden_layers','max_position_embeddings','torch_dtype','sliding_window','num_attention_heads','num_key_value_heads']}
                if configs['tokenizer_config.json']['status']==200:
                    tok=json.loads((dest/'tokenizer_config.json').read_text());item['tokenizer_template_present']=bool(tok.get('chat_template'));item['system_rejection_literal']='System role not supported'in str(tok.get('chat_template',''))
                break
            except Exception as e:item['attempts'].append({'endpoint':endpoint,'error_type':type(e).__name__})
        out['models'][key]=item
    p=O/'model_access_probe.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
