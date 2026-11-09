"""Pin and push all new scheduling code before it is dispatched."""
from pathlib import Path
import ast,datetime,fcntl,hashlib,json,py_compile,shutil,subprocess
ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';REPO=ROOT/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    target=BASE/'lease_priority_implementation.json';assert not target.exists();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    names=['lease_priority_support.py','wjb_tail_priority_worker.py','auxiliary_output_guard_worker.py','prefix_hb_incremental_worker.py','prefix_hb_cache_reuse.py','lease_priority_controller.py','lease_auxiliary_finish_queue.py','resume_wjb_wg_after_pair.py','lease_priority_handoff.py','test_lease_priority_cpu.py','freeze_lease_priority_implementation.py']
    code=['tools/handoff_20261106/'+n for n in names]
    for n in code:py_compile.compile(str(ROOT/n),doraise=True)
    # The two new classifier calls must use the frozen numerical generate kwargs.
    def calls(path):
        found=[]
        for x in ast.walk(ast.parse(path.read_text())):
            if isinstance(x,ast.Call)and ast.unparse(x.func)in ['mdl.generate','model.generate']:
                x.func=ast.Attribute(value=ast.Name(id='MODEL',ctx=ast.Load()),attr='generate',ctx=ast.Load());found.append(ast.dump(x,include_attributes=False))
        return found
    new=calls(ROOT/'tools/handoff_20261106/prefix_hb_incremental_worker.py');old=calls(ROOT/'tools/handoff_20261106/pair500_eval254.py');wjb=calls(ROOT/'tools/handoff_20261106/wjb_eval255_run.py')
    assert new[0] in old and new[1] in wjb
    # Capture CPU test receipt before dispatch, without loading models or labels.
    test=subprocess.check_output(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(ROOT/'tools/handoff_20261106/test_lease_priority_cpu.py')],text=True).strip();assert test.startswith('PASS:')
    deps=['results/audit/pair500/prefix254_publication.json','results/audit/pair500/gpu0_borrow_publication.json','results/audit/pair500/eval255_frozen_runtime_config.json','results/audit/pair500/prefix254_runtime.json','docs/254_ADDENDUM9_LEASE_PRIORITY_AND_INCREMENTAL_JUDGE.md','src/gen/common.py','src/eval/legal_val_batch.py','src/judge/refusal.py','repos/HarmBench/eval_utils.py','tools/handoff_20261106/wjb_eval255_run.py','tools/handoff_20261106/guard_qwen_output.py','tools/handoff_20261106/pair500_eval254.py','tools/handoff_20261106/wjb_top2_shared_window.py']
    manifest={'utc':now,'code_sha256':{n:sha(ROOT/n)for n in code},'dependencies_sha256':{n:sha(ROOT/n)for n in deps},'scheduling_only':True,'PAIR_effects_read':False,'tests':test,'classifier_numeric_generate_calls_AST_equal':True,'AST_comparison_normalization':'receiver identifier mdl/model canonicalized to MODEL; argument ASTs unchanged','old_running_sources_modified':False};target.write_text(json.dumps(manifest,indent=2)+'\n')
    files=code+['results/audit/pair500/lease_priority_implementation.json','results/audit/pair500/lease_priority_schedule_publication.json']
    with(ROOT/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{now} LEASE_PRIORITY_IMPLEMENTATION_PINNED SHA={sha(target)} CPU reservation/order/cache mutation tests passed; classifier generate-call AST matched frozen sources; no running source replaced; publish before launch.\n')
    files+=['docs/PREREG_LOG.txt']
    with(ROOT/'logs/prereg_publish.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip()
        for n in files:dst=REPO/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,dst)
        subprocess.run(['git','add',*files],cwd=REPO,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=REPO,check=True);subprocess.run(['git','commit','-m','Pin and test PAIR-priority auxiliary workers and incremental judge caches'],cwd=REPO,check=True);commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip();subprocess.run(['git','push','origin','main'],cwd=REPO,check=True)
    receipt={'utc':now,'implementation_sha256':sha(target),'commit':commit,'CPU_tests':test};(BASE/'lease_priority_implementation_publication.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
