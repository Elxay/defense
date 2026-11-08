"""Pinned, single-node alpha0 scoring only; no condition effects are read."""
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

import torch
from transformers import AutoModelForCausalLM,AutoTokenizer

ROOT=Path('/home/dell/Def');MODEL=ROOT/'models/WildGuard';OUT=ROOT/'results/audit/pair500/wildguard'


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
    gate=json.loads((OUT/'format5.json').read_text());assert gate['passed_format']
    config=json.loads((MODEL/'config.json').read_text());manifest=json.loads((MODEL/'DOWNLOAD_SHA256.json').read_text())
    assert manifest['revision']=='cbba4823f3e8020e5a74a5e29bf85072def6f2ff'
    signature={'model_manifest_sha256':sha(MODEL/'DOWNLOAD_SHA256.json'),'runtime_source_sha256':sha(Path(__file__)),
               'input_sha256':sha(OUT/'alpha0_inputs.private.json'),'format_gate_sha256':sha(OUT/'format5.json')}
    for name,value in manifest['files'].items():assert sha(MODEL/name)==value
    block=re.search(r'```python\s*\n(.*?)\n```',(MODEL/'README.md').read_text(),re.S).group(1)
    template=next(ast.literal_eval(n.value) for n in ast.parse(block).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='instruction_format' for t in n.targets))
    assert hashlib.sha256(template.encode()).hexdigest()==gate['template_sha256']
    inputs=json.loads((OUT/'alpha0_inputs.private.json').read_text());assert len(inputs)==2000
    tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval()
    start=time.monotonic();timed=0
    keys=['Harmful request','Response refusal','Harmful response']
    for i,row in enumerate(inputs,1):
        dest=OUT/'alpha0_scores'/(row['id']+'.json')
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
        if i%10==0:save(OUT/'alpha0_live.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'n':i,'total':2000,'seconds_per_scored_row':(time.monotonic()-start)/max(1,timed),'host':socket.gethostname(),'gpu':0})
    summaries={}
    subsets={'all':inputs,'high':[r for r in inputs if not r['low_confidence']],
             'low':[r for r in inputs if r['low_confidence']],
             'v2_negative':[r for r in inputs if not r['v2']],
             'historically_marked':[r for r in inputs if r['historical_used']],
             'historically_unmarked':[r for r in inputs if not r['historical_used']]}
    for name,rows in subsets.items():
        counts={k:collections.Counter() for k in keys};matrix=collections.Counter()
        for row in rows:
            record=json.loads((OUT/'alpha0_scores'/(row['id']+'.json')).read_text())
            for k in keys:counts[k][str(record['labels'][k])]+=1
            v=record['labels']['Response refusal']
            if v in ('yes','no'):matrix[int(row['v2']),int(v=='yes')]+=1
        n=sum(matrix.values());po=(matrix[0,0]+matrix[1,1])/n if n else None
        pe=((matrix[0,0]+matrix[0,1])*(matrix[0,0]+matrix[1,0])+(matrix[1,0]+matrix[1,1])*(matrix[0,1]+matrix[1,1]))/n**2 if n else None
        summaries[name]={'n':len(rows),'labels':{k:dict(v) for k,v in counts.items()},'v2_vs_model_refusal_2x2':{f'v2{a}_model{b}':matrix[a,b] for a in (0,1) for b in (0,1)},'kappa':(po-pe)/(1-pe) if pe is not None and pe!=1 else None}
    save(OUT/'alpha0_summary.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'signature':signature,
        'host':'node01','cross_node20_status':'pending; single-node score set','strata':summaries})
    save(OUT/'alpha0_done.json',{'n':2000,'summary_sha256':sha(OUT/'alpha0_summary.json')})
    print('ALPHA0_COMPLETE_2000_SUMMARY_SAVED_NO_CONDITION_BATCH',flush=True)


if __name__=='__main__':main()
