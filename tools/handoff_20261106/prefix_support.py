"""Shared portable generation protocol; no analysis or report imports."""
import hashlib
import json
import os
from pathlib import Path
import socket
import datetime

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'results/audit/pair500'
PREFIX=BASE/'prefix254'
RUNTIME=BASE/'prefix254_runtime.json'


def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16*1024*1024),b''):h.update(b)
    return h.hexdigest()


def objsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def load(p):return json.loads(Path(p).read_text())


def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.'+str(os.getpid())+'.tmp')
    tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,p)


def node():return 'innet' if str(ROOT)=='/data/HZX/Def' else 'node01'


def verify_code():
    publication=load(BASE/'prefix254_publication.json')
    assert publication['runtime_sha256']==sha(RUNTIME)
    assert publication['asset_manifest_sha256']==sha(BASE/'prefix254_asset_manifest.json')
    for name,value in publication['code_sha256'].items():assert sha(ROOT/name)==value,name
    for name,value in load(RUNTIME)['source_sha256'].items():assert sha(ROOT/name)==value,name


def verify_role(role,full=False):
    cfg=load(RUNTIME);m=load(BASE/'prefix254_asset_manifest.json');root=Path(cfg['models'][node()][role])
    assert root.is_absolute()
    receipt=PREFIX/'asset_checks'/(node()+'_'+role+'.json')
    cached=load(receipt) if receipt.exists() else None
    stats={name:[(root/name).stat().st_size,(root/name).stat().st_mtime_ns] for name in m['roles'][role]}
    expected=objsha(m['roles'][role])
    if not full and cached and cached['manifest_fingerprint']==expected and cached['stats']==stats:return
    for name,spec in m['roles'][role].items():
        assert (root/name).stat().st_size==spec['bytes'] and sha(root/name)==spec['sha256'],role+'/'+name
    save(receipt,{'utc':utc(),'manifest_fingerprint':expected,'stats':stats,'full_hash_verified':True})


def signature(condition,item,cfg):
    return {'protocol':'prefix254-v1','runtime_sha256':sha(RUNTIME),'condition':condition,'id':item['id'],
            'prompt_sha256':item['prompt_sha256'],'row_sha256':item['row_sha256'],
            'injection_source_sha256':cfg['core_sha256']}


def verify_record(path,condition,item,cfg):
    x=load(path);assert x['id']==item['id'] and x['signature']==signature(condition,item,cfg)
    assert x['result']['injection_count']==1
    return x


def system_texts():
    s=(ROOT/'docs/227_SYSTEM_PROMPTS.txt').read_text()
    a=s.split('A_short\n',1)[1].split('\n\nB_detailed\n',1)[0]
    b=s.split('B_detailed\n',1)[1].strip()
    assert hashlib.sha256(a.encode()).hexdigest()=='d33c70fdd0c40dc6d2b38a6be972bb8806bd5ac174db361930bb85341be974c3'
    assert hashlib.sha256(b.encode()).hexdigest()=='3606acab20daf5f70bde6b186c9b498ada1b0de51e4b67dd4a81a1e1745c4957'
    return {'SYS_A':a,'SYS_B':b}


def render_audit(tok,prompt,condition=None,system=None):
    import numpy as np
    texts=system_texts();user={'role':'user','content':prompt}
    rendered={k:tok.apply_chat_template([{'role':'system','content':v},user],tokenize=False,add_generation_prompt=True) for k,v in texts.items()}
    assert rendered['SYS_A'].replace(texts['SYS_A'],'__SYSTEM__',1)==rendered['SYS_B'].replace(texts['SYS_B'],'__SYSTEM__',1)
    marker='<|start_header_id|>user<|end_header_id|>\n\n'
    base=tok.apply_chat_template([user],tokenize=False,add_generation_prompt=True)
    assert marker in base and all(s.split(marker,1)[1]==base.split(marker,1)[1] for s in rendered.values())
    if condition in texts:assert system==texts[condition]
    messages=([{'role':'system','content':system}] if system else [])+[user]
    ids=tok.apply_chat_template(messages,add_generation_prompt=True,return_tensors='pt')
    return ids,{'only_system_differs_asserted':True,'input_ids_sha256':hashlib.sha256(ids.cpu().numpy().astype('<i8').tobytes()).hexdigest(),
                'user_content_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                'system_text_sha256':hashlib.sha256(system.encode()).hexdigest() if system else None}
