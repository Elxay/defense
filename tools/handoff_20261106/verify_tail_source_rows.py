"""CPU source/template preflight against the actual existing baselines."""
from pathlib import Path
import datetime,hashlib,json,sys
ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
from prefix_support import verify_role,system_texts
import wjb_eval255_run as w
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    verify_role('target',full=True);texts=system_texts();public=w.public_rows();baseline=json.loads((BASE/'wildguard_public/alpha0_inputs.private.json').read_text());lookup={(r['dataset'],r['original_id']):r['prompt'] for r in baseline};assert len(lookup)==1979
    checked=0;batches=0
    for dataset,rows in public.items():
        for key,prompt in rows:assert lookup[(dataset,key)].encode()==prompt.encode();checked+=1
        for offset in range(0,len(rows),8):
            keys=[k for k,_ in rows[offset:offset+8]];p=w.EVAL/'public.private/alpha0'/dataset/(keys[0]+'.json');record=json.loads(p.read_text());assert [x['id'] for x in record['items']]==keys;batches+=1
    assert checked==1979;harmful=w.harmful_rows(json.loads(w.PLAN.read_text()));prior={r['id']:r['prompt']for r in json.loads((BASE/'wildguard/alpha0_inputs.private.json').read_text())};assert len(prior)==2000 and set(harmful)==set(prior) and all(harmful[k].encode()==prior[k].encode() for k in prior)
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'public_prompts_byte_matched':checked,'public_original_batch_compositions_matched':batches,'WJB_harmful_prompts_byte_matched':len(prior),'target_files_full_hash_verified':True,'system_text_hashes':{k:hashlib.sha256(v.encode()).hexdigest()for k,v in texts.items()},'source_payload_sha256':{'public':sha(BASE/'wildguard_public/alpha0_inputs.private.json'),'harmful':sha(BASE/'wildguard/alpha0_inputs.private.json')},'PAIR_effects_read':False}
    p=BASE/'lease_priority/source_rows_preflight.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
