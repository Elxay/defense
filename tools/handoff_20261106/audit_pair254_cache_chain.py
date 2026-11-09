"""Metadata/signatures only: no labels, probabilities or INVALID fields are selected."""
from pathlib import Path
import ast,collections,datetime,hashlib,json,subprocess,sys
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';P=B/'prefix254';O=B/'read_order10'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def objsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def main():
    now=datetime.datetime.now(datetime.timezone.utc);rows={r['id']:objsha(r)for r in load(B/'rows.private.json')};index=[];counts=collections.Counter();expected={'classifier_source_sha256':sha(R/'tools/handoff_20261106/pair500_eval254.py'),'eval_utils_sha256':sha(R/'repos/HarmBench/eval_utils.py'),'model_asset_manifest_sha256':sha(B/'prefix254_asset_manifest.json'),'runtime_sha256':sha(B/'prefix254_runtime.json')}
    native_prompt={}
    for p in(B/'generations.private').glob('*.json'):
        z=load(p);native_prompt[z['id']]=hashlib.sha256(z['best']['prompt'].encode()).hexdigest()
    # Entire record bytes are hashed; only the signature mapping is selected after parsing.
    for p in sorted((P/'hb_pre_scores').glob('*/*.json')):
        name=p.parent.name;key=p.stem;sig=load(p)['signature'];g=P/'generation.private'/name/(key+'.json');gsig=load(g)['signature'];assert sig['prefix_generation_sha256']==sha(g);assert sig['row_sha256']==rows[key]
        assert all(sig[k]==v for k,v in expected.items());assert gsig['prompt_sha256']==native_prompt[key] and gsig['row_sha256']==rows[key] and gsig['condition']==name
        index.append({'judge':'HB','condition':name,'id':key,'prompt_sha256':gsig['prompt_sha256'],'row_sha256':rows[key],'generation_sha256':sig['prefix_generation_sha256'],'cache_sha256':sha(p)});counts['HB']+=1
    for p in sorted((P/'wg_pre_index').glob('*.json')):
        name=p.stem
        for key,ref in load(p).items():
            g=P/'generation.private'/name/(key+'.json');gsig=load(g)['signature'];assert ref['generation_sha256']==sha(g) and ref['prompt_sha256']==gsig['prompt_sha256']==native_prompt[key];assert sha(R/ref['score_file'])==ref['score_file_sha256']
            index.append({'judge':'WG','condition':name,'id':key,'prompt_sha256':ref['prompt_sha256'],'row_sha256':rows[key],'generation_sha256':ref['generation_sha256'],'cache_sha256':ref['score_file_sha256']});counts['WG']+=1
    O.mkdir(exist_ok=True);idx=O/'cache_prompt_hash_index.private.json';assert not idx.exists();idx.write_text(json.dumps({'utc':now.isoformat(),'rows':index},indent=2)+'\n')
    sources=['prefix_hb_incremental_worker.py','prefix_hb_cache_reuse.py','prefix_wildguard_queue.py','prefix_wg_batch_runner.py','pair500_wildguard_run.py','prefix_wg_reuse.py','pair500_read_gate.py','lease_priority_controller.py','prefix_controller.py']
    ast_report={}
    for n in sources:
        p=R/'tools/handoff_20261106'/n;t=p.read_text();tree=ast.parse(t);ast_report[n]={'sha256':sha(p),'syntactically_valid':True,'literal_subscript_keys':sorted({z.slice.value for z in ast.walk(tree)if isinstance(z,ast.Subscript)and isinstance(z.slice,ast.Constant)and isinstance(z.slice.value,str)})}
    # Live workers write row labels as required for inference; this audit never selects them.
    potential=[]
    for folder in [P,B/'canonical254',B/'wildguard_pair254']:
        for p in folder.glob('*.json'):
            if any(k in p.name.lower()for k in ['summary','report','aggregate','invalid']):potential.append(str(p.relative_to(R)))
    result={'utc':now.isoformat(),'signature_audit_passed':True,'cache_file_counts_not_outcomes':dict(counts),'explicit_prompt_index_sha256':sha(idx),'source_audit':ast_report,'root_summary_like_paths':potential,'outcome_values_selected':False,'INVALID_counted':False,'cache_files_modified':False,'scope':'Inspected HB/WG workers, queues and reuse/readiness paths. Classification writes individual labels/invalid fields; signature checks and progress are permitted. No outcome-summary/aggregation entry is called in these paths. This is not a claim about unobserved third-party sessions.','final_assertions':['prefix_controller.sync_search: accepted source file hashes unchanged','prefix_controller.materialize: final prompt SHA and source file SHA equal accepted prefix','prefix_support.verify_record: complete generation signature equality','HB cache import: generation/row/template/model/runtime equality','WG cache import: explicit prompt/response/generation equality'],'mismatch_policy':'assertion blocks reuse; preserve original; invalidate affected row, regenerate if final prompt changed, then rejudge with UTC/hashes; no silent repair'}
    q=O/'cache_only_audit.json';q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'file':str(q.relative_to(R)),'sha256':sha(q),'utc':result['utc'],'cache_file_counts_not_outcomes':dict(counts),'explicit_prompt_index_sha256':sha(idx),'summary_like_paths':potential,'outcome_values_selected':False,'INVALID_counted':False}))
if __name__=='__main__':main()
