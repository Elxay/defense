"""CPU checks for duplicate reservation, ordered tails and immutable cache rebinding."""
from pathlib import Path
import hashlib,json,sys,tempfile,types
from unittest.mock import patch
ROOT=Path('/data/HZX/Def');sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
import lease_priority_controller as ctl
import prefix_hb_cache_reuse as reuse
import prefix_hb_incremental_worker as hb
from prefix_support import objsha

def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    with tempfile.TemporaryDirectory(prefix='def_lease_cpu_')as directory:
        root=Path(directory);base=root/'results/audit/pair500';prefix=base/'prefix254';item={'id':'r1','row_sha256':'rowhash'}
        with patch.object(ctl,'PREFIX',prefix):
            pending=ctl.prefix_pending([item],{});assert len(pending['alpha0'])==1 and all(not v for k,v in pending.items() if k!='alpha0')
            put(prefix/'generation.private/alpha0/r1.json',{});jobs={'2':{'kind':'prefix','condition':'old_s3','ids':['r1']}}
            pending=ctl.prefix_pending([item],jobs);assert not pending['old_s3'] and len(pending['rand0'])==1
        plan=base/'tail_plan.json';put(plan,{'ids':['a','b','c','d']});fake=types.SimpleNamespace(PLAN=plan,EVAL=base/'public255',public_rows=lambda:{'set':[(str(i),'')for i in range(20)]})
        with patch.dict(sys.modules,{'wjb_eval255_run':fake}):
            assert ctl.tail_candidate('harmful',{})==('old_s0',0)
            reserved={'2':{'kind':'tail','tail_kind':'harmful','condition':'old_s0','shard':0},'3':{'kind':'tail','tail_kind':'harmful','condition':'old_s0','shard':1}}
            assert ctl.tail_candidate('harmful',reserved) is None
            for key in ['a','b','c','d']:put(fake.EVAL/'harmful.private/old_s0/wildjailbreak_harmful'/(key+'.json'),{})
            assert ctl.tail_candidate('harmful',{})==('SYS_A',0)
        row={'id':'r1','layer':'standard'};put(base/'rows.private.json',[row]);source=prefix/'generation.private/old_s3/r1.json';put(source,{'id':'r1','dummy_inference':'unchanged'})
        canonical=base/'canonical254/generation.private/old_s3/r1.json';put(canonical,{'signature':{'prefix_generation_sha256':sha(source)},'prefix_source':str(source.relative_to(root))});runtime=base/'prefix254_runtime.json';put(runtime,{})
        sig={'prefix_generation_sha256':sha(source),'row_sha256':objsha(row)};inference=prefix/'hb_pre_scores/old_s3/r1.json';put(inference,{'id':'r1','signature':sig,'label':1,'method':'hf_innet_prompt'});original_bytes=inference.read_bytes()
        with patch.object(reuse,'ROOT',root),patch.object(reuse,'BASE',base),patch.object(reuse,'verify',lambda:None),patch.object(hb,'cache_signature',lambda g,r:{'prefix_generation_sha256':g,'row_sha256':r}):
            result=reuse.import_verified();assert result=={'old_s3':1};dst=base/'canonical254/scores/old_s3/r1.json';x=json.loads(dst.read_text());assert x['label']==1 and x['signature']['generation_sha256']==sha(canonical) and inference.read_bytes()==original_bytes
            source.write_text('changed')
            try:reuse.import_verified()
            except AssertionError:pass
            else:raise AssertionError('changed original generation accepted')
    print('PASS: alpha0 precedence; disjoint reservations; fixed tail condition order; cache rebinding keeps inference bytes and rejects changed generation')

if __name__=='__main__':main()
