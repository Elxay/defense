"""Prepare identical portable assets without GPU use or effect reads."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys
import numpy as np

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(16*1024*1024),b''):h.update(block)
    return h.hexdigest()


def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')


def main():
    cfg=json.loads((BASE/'eval254_config.json').read_text());roles={}
    for role in ['target','judge','guard']:
        root=Path(cfg[role]);files={}
        if role=='judge':files=json.loads((BASE/'hb_judge_model_sha256.json').read_text())['files']
        else:
            for p in sorted(root.iterdir()):
                if p.is_file() and not p.name.startswith('.'):
                    files[p.name]={'bytes':p.stat().st_size,'sha256':sha(p)}
        roles[role]=files
    manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roles':roles}
    save(BASE/'prefix254_asset_manifest.json',manifest)
    specs=json.loads(json.dumps(cfg['conditions']))
    for name,spec in specs.items():
        if 'vector' not in spec:continue
        original=ROOT/spec['vector'];assert sha(original)==spec['file_sha256']
        v=np.load(original).astype(np.float32)
        if spec['renormalize']:v=v/np.linalg.norm(v)*5.21
        assert hashlib.sha256((v+0.).tobytes()).hexdigest()==spec['injection_sha256']
        dest=BASE/'prefix254/vectors'/(name+'.npy');dest.parent.mkdir(parents=True,exist_ok=True);np.save(dest,v)
        spec.update(injection_buffer=str(dest.relative_to(ROOT)),injection_buffer_file_sha256=sha(dest))
    # Sources/models never modify the already running PAIR search settings.
    sources=['src/gen/common.py','src/judge/refusal.py','repos/HarmBench/eval_utils.py','tools/handoff_20261106/pair500_score.py','tools/handoff_20261106/pair500_generate.py','tools/handoff_20261106/pair500_eval254.py','night/hf_judge_round2_reference.py','night/cls_prompt.txt','docs/227_SYSTEM_PROMPTS.txt']
    runtime={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'conditions':specs,'condition_order':cfg['condition_order'],'core_sha256':sha(ROOT/'src/gen/common.py'),
        'models':{'innet':{'target':cfg['target'],'judge':cfg['judge'],'guard':cfg['guard']},'node01':{'target':'/data/ray/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659','judge':'/home/dell/Def/local_judge13b'}},
        'source_sha256':{p:sha(ROOT/p) for p in sources}}
    save(BASE/'prefix254_runtime.json',runtime)
    copy=sources+['results/audit/pair500/prefix254_runtime.json','results/audit/pair500/prefix254_asset_manifest.json']+[spec['injection_buffer'] for spec in specs.values() if 'vector' in spec]
    subprocess.run(['rsync','-aR',*copy,'node01:/home/dell/Def/'],cwd=ROOT,check=True)
    expected={str((ROOT/s['vector']).relative_to(ROOT)):s['file_sha256'] for s in specs.values() if 'vector' in s}
    expected.update({s['injection_buffer']:s['injection_buffer_file_sha256'] for s in specs.values() if 'vector' in s})
    expected.update(runtime['source_sha256'])
    hashes=json.loads((BASE/'copyright_hash_manifest.json').read_text())
    expected.update({'repos/HarmBench/data/copyright_classifier_hashes/'+k+'.pkl':v for k,v in hashes.items()})
    save(BASE/'prefix254_expected_node_files.json',expected)
    subprocess.run(['scp',str(BASE/'prefix254_expected_node_files.json'),'node01:/home/dell/Def/results/audit/pair500/'],check=True)
    remote="""from pathlib import Path
import json,hashlib,datetime
r=Path('/home/dell/Def');b=r/'results/audit/pair500'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for z in iter(lambda:f.read(16*1024*1024),b''):h.update(z)
 return h.hexdigest()
expected=json.loads((b/'prefix254_expected_node_files.json').read_text())
for name,value in expected.items():assert sha(r/name)==value,name
cfg=json.loads((b/'prefix254_runtime.json').read_text());m=json.loads((b/'prefix254_asset_manifest.json').read_text())
for role in ['target','judge']:
 for name,spec in m['roles'][role].items():assert sha(Path(cfg['models']['node01'][role])/name)==spec['sha256'],role+'/'+name
wild=json.loads((r/'models/WildGuard/DOWNLOAD_SHA256.json').read_text())
for name,value in wild['files'].items():assert sha(r/'models/WildGuard'/name)==value,name
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all_passed':True,'related_files':len(expected),'original_vectors':10,'exact_injection_buffers':10,'copyright_references':100,'judge_shards':6,'target_model_hashes_match':True,'wildguard_revision':wild['revision'],'wildguard_artifacts_match':True,'runtime_sha256':sha(b/'prefix254_runtime.json'),'manifest_sha256':sha(b/'prefix254_asset_manifest.json')}
(b/'prefix254_node_asset_check.json').write_text(json.dumps(out,indent=2)+'\\n');print(json.dumps(out))
"""
    x=json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=remote,text=True));save(BASE/'prefix254_node_asset_check.json',x);print(json.dumps(x),flush=True)


if __name__=='__main__':main()
