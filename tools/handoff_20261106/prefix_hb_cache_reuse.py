"""Rebind byte-verified incremental inference to the actual final snapshot."""
from pathlib import Path
import hashlib,json
from lease_priority_support import ROOT,BASE,load,save,sha,utc,verify

def import_verified():
    verify();from prefix_hb_incremental_worker import cache_signature
    from prefix_support import objsha
    rows={r['id']:r for r in load(BASE/'rows.private.json')};counts={};original_manifest={}
    for folder in (BASE/'prefix254/hb_pre_scores').glob('*'):
        name=folder.name;counts[name]=0
        for p in folder.glob('*.json'):
            key=p.stem;canonical=BASE/'canonical254/generation.private'/name/(key+'.json')
            if not canonical.exists():continue
            c=load(canonical);prefix=ROOT/c['prefix_source'];assert sha(prefix)==c['signature']['prefix_generation_sha256'];x=load(p);assert x['signature']==cache_signature(sha(prefix),objsha(rows[key]))
            original_manifest[str(p.relative_to(ROOT))]=sha(p)
            value={**x,'signature':{'generation_sha256':sha(canonical),'config_sha256':sha(BASE/'prefix254_runtime.json')},'incremental_inference_provenance':{'original_file':str(p.relative_to(ROOT)),'original_sha256':sha(p),'original_signature':x['signature'],'no_new_inference':True}}
            dest=BASE/'canonical254/scores'/name/(key+'.json')
            if dest.exists():assert load(dest)['signature']==value['signature']
            else:save(dest,value)
            counts[name]+=1
    save(BASE/'prefix254/hb_cache_reuse_receipt.json',{'utc':utc(),'verified_cached_rows':counts,'original_files_sha256':original_manifest,'effects_read':False,'final_fresh_reference_gate_still_required':True});return counts
