"""Exercise the existing final-binding checks using synthetic rows only."""
from pathlib import Path
import datetime,json,sys,tempfile
from unittest.mock import patch
R=Path('/data/HZX/Def');sys.path.insert(0,str(R/'tools/handoff_20261106'));import prefix_controller as old
def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x))
def main():
    with tempfile.TemporaryDirectory(prefix='def_prompt_assertions_')as directory:
        root=Path(directory);base=root/'results/audit/pair500';prefix=base/'prefix254';runtime=base/'runtime.json';put(runtime,{});(root/'docs').mkdir();(root/'docs/PREREG_LOG.txt').touch();row={'id':'synthetic','prompt_sha256':'prompt_A','source_file_sha256':'source_A'}
        def snapshot(prompt='prompt_A',source='source_A'):put(base/'frozen_prompt_snapshot.json',{'rows':[{'id':'synthetic','prompt_sha256':prompt,'file_sha256':source}]})
        with patch.object(old,'ROOT',root),patch.object(old,'BASE',base),patch.object(old,'PREFIX',prefix),patch.object(old,'RUNTIME',runtime),patch.object(old,'NAMES',[]):
            snapshot();old.materialize([row]);assert(prefix/'final_snapshot_binding.json').exists()
            for case,arguments in [('changed_prompt',{'prompt':'prompt_B'}),('changed_source_bytes',{'source':'source_B'})]:
                snapshot(**arguments)
                try:old.materialize([row])
                except AssertionError:pass
                else:raise AssertionError(case+' was silently accepted')
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'same_prompt_and_source':'PASS','changed_final_prompt_rejected_before_reuse':'PASS','changed_source_bytes_rejected_before_reuse':'PASS','synthetic_data_only':True,'real_classifier_outputs_read':False,'real_generation_or_cache_files_changed':False};p=R/'results/audit/pair500/read_order10/final_prompt_assertion_test.json';p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
