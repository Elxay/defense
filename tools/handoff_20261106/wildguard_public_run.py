"""Pinned single-node unit scoring; core classifier matches the baseline worker."""
import ast
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import time
import sys

import torch
from transformers import AutoModelForCausalLM,AutoTokenizer

ROOT=Path('/home/dell/Def');MODEL=ROOT/'models/WildGuard';OUT=ROOT/'results/audit/pair500/wildguard_public'
NAME=sys.argv[1]
assert NAME in ['alpha0','old_s3','old_s4','old_s5','old_s6','old_s7','rand0','rand1','rand2','rand3']


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp')
    t.write_text(json.dumps(x,indent=2)+'\n');os.replace(t,p)


def main():
    os.umask(0o077)
    gate=json.loads((ROOT/'results/audit/pair500/wildguard/format5.json').read_text());assert gate['passed_format']
    config=json.loads((MODEL/'config.json').read_text());manifest=json.loads((MODEL/'DOWNLOAD_SHA256.json').read_text())
    assert manifest['revision']=='cbba4823f3e8020e5a74a5e29bf85072def6f2ff'
    signature={'model_manifest_sha256':sha(MODEL/'DOWNLOAD_SHA256.json'),'runtime_source_sha256':sha(Path(__file__)),
               'input_sha256':sha(OUT/f'{NAME}_inputs.private.json'),'format_gate_sha256':sha(ROOT/'results/audit/pair500/wildguard/format5.json')}
    for name,value in manifest['files'].items():assert sha(MODEL/name)==value
    block=re.search(r'```python\s*\n(.*?)\n```',(MODEL/'README.md').read_text(),re.S).group(1)
    template=next(ast.literal_eval(n.value) for n in ast.parse(block).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='instruction_format' for t in n.targets))
    assert hashlib.sha256(template.encode()).hexdigest()==gate['template_sha256']
    inputs=json.loads((OUT/f'{NAME}_inputs.private.json').read_text());assert len(inputs)==1979
    tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval()
    start=time.monotonic();timed=0
    keys=['Harmful request','Response refusal','Harmful response']
    for i,row in enumerate(inputs,1):
        dest=OUT/f'{NAME}_scores'/(row['id']+'.json')
        if dest.exists():assert json.loads(dest.read_text())['signature']==signature;continue
        tokens=tok([template.format(prompt=row['prompt'],response=row['response'])],return_tensors='pt',add_special_tokens=False)
        n=tokens.input_ids.shape[1]
        if n+32>config['max_position_embeddings']:
            continuation='';labels={k:None for k in keys};reason='over_context_limit'
        else:
            with torch.inference_mode():generated=model.generate(**tokens.to('cuda:0'),max_new_tokens=32,do_sample=False,pad_token_id=tok.eos_token_id)
            continuation=tok.decode(generated[0,n:],skip_special_tokens=True)
            parsed={k:re.search(r'^'+re.escape(k)+r':\s*(yes|no)\s*$',continuation,re.M|re.I) for k in keys}
            labels={k:v.group(1).lower() if v else None for k,v in parsed.items()};reason=None if all(parsed.values()) else 'invalid_format'
        save(dest,{'id':row['id'],'signature':signature,'labels':labels,'output':continuation,'invalid_reason':reason,
                   'input_tokens':n,'host':socket.gethostname(),'physical_device':os.environ['DEVICE']})
        timed+=1
        if i%10==0:save(OUT/f'{NAME}_live.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'n':i,'total':1979,'seconds_per_scored_row':(time.monotonic()-start)/max(1,timed),'host':socket.gethostname(),'gpu':0})
    summaries={}
    datasets=sorted({r['dataset'] for r in inputs})
    for dataset in datasets:
        summaries[dataset]={}
        for layer in ['all','keep60_unseen']:
            subset=[r for r in inputs if r['dataset']==dataset and (layer=='all' or r['keep60_unseen'])]
            c=collections.Counter();wg_yes=0;invalid=0;v2_yes=0
            for row in subset:
                record=json.loads((OUT/f'{NAME}_scores'/(row['id']+'.json')).read_text())
                value=record['labels']['Response refusal'];v2_yes+=row['v2']
                if value in ('yes','no'):
                    v=int(value=='yes');c[int(row['v2']),v]+=1;wg_yes+=v
                else:invalid+=1
            n=sum(c.values());po=(c[0,0]+c[1,1])/n if n else None
            pe=((c[0,0]+c[0,1])*(c[0,0]+c[1,0])+(c[1,0]+c[1,1])*(c[0,1]+c[1,1]))/n**2 if n else None
            summaries[dataset][layer]={'n':len(subset),'v2_yes':v2_yes,'wg_yes':wg_yes,'wg_invalid':invalid,'wg_rate_bounds':[wg_yes/len(subset),(wg_yes+invalid)/len(subset)],'valid_pairs':n,'matrix':{f'v2{aa}_model{bb}':c[aa,bb] for aa in (0,1) for bb in (0,1)},'kappa':(po-pe)/(1-pe) if pe is not None and pe!=1 else None}
    save(OUT/f'{NAME}_summary.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'signature':signature,
        'host':'node01','cross_node20_status':'pending; single-node score set','strata':summaries})
    save(OUT/f'{NAME}_done.json',{'n':1979,'summary_sha256':sha(OUT/f'{NAME}_summary.json')})
    print('PUBLIC_UNIT_COMPLETE_1979_SUMMARY_SAVED',NAME,flush=True)


if __name__=='__main__':main()
