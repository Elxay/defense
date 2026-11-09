"""Rebind verified prefix classifier outputs; preserve original inference files."""
import hashlib
import json
from pathlib import Path

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def import_verified(name,payload,input_sha):
    indexpath=BASE/'prefix254/wg_pre_index'/(name+'.json')
    if not indexpath.exists():return 0
    index=json.loads(indexpath.read_text());pub=json.loads((BASE/'prefix254_dual_publication.json').read_text());n=0
    expected={'model_manifest_sha256':pub['wildguard_model_manifest_sha256'],'runtime_source_sha256':pub['pair_wildguard_source_sha256'],'input_sha256':input_sha,'format_gate_sha256':pub['wildguard_format_gate_sha256']}
    folder=BASE/'wildguard_pair254'/(name+'_scores');folder.mkdir(parents=True,exist_ok=True)
    for row in payload:
        key=row['id']
        if key not in index:continue
        ref=index[key];canonical=json.loads((BASE/'canonical254/generation.private'/name/(key+'.json')).read_text())
        assert canonical['signature']['prefix_generation_sha256']==ref['generation_sha256']
        assert hashlib.sha256(row['prompt'].encode()).hexdigest()==ref['prompt_sha256']
        assert hashlib.sha256(row['response'].encode()).hexdigest()==ref['response_sha256']
        source=ROOT/ref['score_file'];assert sha(source)==ref['score_file_sha256'];x=json.loads(source.read_text())
        assert all(x['signature'][k]==expected[k] for k in expected if k!='input_sha256')
        x['prefix_inference_provenance']={'original_file':ref['score_file'],'original_file_sha256':sha(source),'original_signature':x['signature'],'batch_manifest_sha256':ref['batch_manifest_sha256'],'no_new_inference':True}
        x['signature']=expected;dest=folder/(key+'.json')
        if dest.exists():assert json.loads(dest.read_text())['signature']==expected
        else:
            tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(dest)
        n+=1
    return n
