"""Synthetic cache-rebinding checks without model or research outcomes."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
from unittest.mock import patch

import prefix_wg_reuse as reuse

def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x)+'\n')


def main():
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory);base=root/'results/audit/pair500';condition='alpha0';key='benign_fixture'
        pub={'wildguard_model_manifest_sha256':'model','pair_wildguard_source_sha256':'worker','wildguard_format_gate_sha256':'format'};put(base/'prefix254_dual_publication.json',pub)
        original={'id':key,'signature':{'model_manifest_sha256':'model','runtime_source_sha256':'worker','format_gate_sha256':'format','input_sha256':'OLD_BATCH'},'labels':{'Response refusal':'no'}}
        source=root/'private_fixture/score.json';put(source,original);before=source.read_bytes()
        entry={'generation_sha256':'generation','prompt_sha256':hashlib.sha256(b'Garden?').hexdigest(),'response_sha256':hashlib.sha256(b'A garden.').hexdigest(),'score_file':str(source.relative_to(root)),'score_file_sha256':hashlib.sha256(before).hexdigest(),'batch_manifest_sha256':'batch'}
        put(base/'prefix254/wg_pre_index/alpha0.json',{key:entry});put(base/'canonical254/generation.private/alpha0'/(key+'.json'),{'signature':{'prefix_generation_sha256':'generation'}})
        with patch.object(reuse,'ROOT',root),patch.object(reuse,'BASE',base):
            assert reuse.import_verified(condition,[{'id':key,'prompt':'Garden?','response':'A garden.'}],'FINAL_BATCH')==1
            result=json.loads((base/'wildguard_pair254/alpha0_scores'/(key+'.json')).read_text());assert result['labels']==original['labels'];assert result['signature']['input_sha256']=='FINAL_BATCH';assert source.read_bytes()==before
            try:reuse.import_verified(condition,[{'id':key,'prompt':'Changed?','response':'A garden.'}],'FINAL_BATCH')
            except AssertionError:pass
            else:raise AssertionError('A changed prompt was accepted')
    print('PASS: identical input rebind; original inference bytes retained; changed prompt rejected')


if __name__=='__main__':main()
