"""Apply the user's cancellation of today's18:00 cutoff without editing old pins."""
from pathlib import Path
import ast,datetime,fcntl,hashlib,json,shutil,subprocess,tempfile,types,sys
from unittest.mock import patch
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';G=R/'prereg_repo';sys.path.insert(0,str(R/'tools/handoff_20261106'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();doc=R/'docs/254_ADDENDUM13_GPU0_DAY_AUTHORIZATION.md';assert not doc.exists();doc.write_text(f'''# GPU0 scheduling authorization for the rest of today

UTC {now}. The user explicitly cancels the18:00 JST handback and says today's cards belong to the project owner. GPU0 may continue today; the old18:00 cutoff is superseded. Interpret today's authorization through2026-11-09 24:00 JST (2026-11-09 15:00 UTC), without extending it into the next day. No18:00 reclaim signal is sent. Existing reclaim-on-explicit-request, compute-context checks, leases, >2GB memory admission and the passed20-row gate remain.

Preserve the original borrowed-card publication and all pinned numerical sources. A separate authorization adapter replaces only the deadline-config lookup in the existing eligibility function. A pinned bootstrap applies this adapter to unchanged worker files; target generation, vector hashes, prompt order, model/reference gates and all reading locks remain unchanged. Do not edit any source of an active worker. Drain the registered owned dispatcher at its existing atomic boundaries, preserve/check existing generation bytes, then start dispatcher_v3 through launch_job. A brief checkpoint handoff is permitted; no colleague or unrelated process is stopped.

GPU0/2/3 continue by the existing leases. Existing jobs on other cards are preserved; the authorization is not an instruction to terminate them. The token, human-review and manuscript tasks are unchanged. This amendment is scheduling-only and is not based on PAIR effect labels, which remain unread.
''')
    names=['gpu0_day_authorization.py','gpu0_authorized_bootstrap.py','lease_priority_controller_v3.py'];workers=['prefix_generate_borrowed.py','wjb_tail_priority_worker_v2.py','auxiliary_output_guard_worker.py','prefix_hb_incremental_worker.py']
    for n in names:ast.parse((R/'tools/handoff_20261106'/n).read_text())
    a={'utc':now,'valid_until_utc':'2026-11-09T15:00:00+00:00','supersedes_18_JST_cutoff':True,'authorization_source':'user in current chat:18:00不需要让出GPU，今天都是属于我的','document':str(doc.relative_to(R)),'document_sha256':sha(doc),'original_borrow_publication_sha256':sha(B/'gpu0_borrow_publication.json'),'new_code_sha256':{'tools/handoff_20261106/'+n:sha(R/'tools/handoff_20261106'/n)for n in names},'workers_sha256':{n:sha(R/'tools/handoff_20261106'/n)for n in workers},'controller_sha256':sha(R/'tools/handoff_20261106/lease_priority_controller_v3.py'),'PAIR_effects_read':False};p=B/'gpu0_day_authorization.json';assert not p.exists();p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
    from gpu0_day_authorization import install
    import borrowed_gpu_support as old
    install();f=old.gpu0_must_yield
    with tempfile.TemporaryDirectory(prefix='def_gpu0_day_auth_')as directory:
        temp=Path(directory)
        def run(hour,minute=0,external=False):
            class Fixed(datetime.datetime):
                @classmethod
                def now(cls,tz=None):return datetime.datetime(2026,11,9,hour,minute,tzinfo=datetime.timezone.utc)
            def query(args,**kwargs):return('123, gpu-test\n'if external else'')if'--query-compute-apps=pid,gpu_uuid'in args else'gpu-test\n'
            with patch.dict(f.__globals__,{'BASE':temp,'datetime':types.SimpleNamespace(datetime=Fixed,timezone=datetime.timezone),'subprocess':types.SimpleNamespace(check_output=query)}):return f()
        assert run(9) is False;assert run(14,59)is False;assert run(15)is True;assert run(9,external=True)is True;(temp/'gpu0_reclaim.flag').touch();assert run(9)is True
    test={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'18JST_continues':'PASS','23_59JST_continues':'PASS','24JST_expires_today_authorization':'PASS','external_compute_context_still_yields':'PASS','explicit_reclaim_still_yields':'PASS','GPU_inference_performed':False};q=B/'gpu0_day_authorization_tests.json';q.write_text(json.dumps(test,indent=2)+'\n')
    for n in ['PREREG_LOG.txt','OPS_LOG.txt']:
        with(R/'docs'/n).open('a')as out:out.write(f'{now} GPU0_DAY_AUTHORIZATION_USER_CONFIRMED SHA={sha(doc)} old18JST_cutoff superseded, today valid_until15UTC/24JST; old publication preserved; tests_SHA={sha(q)}; no effect reads or numerical changes.\n')
    files=[str(doc.relative_to(R)),str(p.relative_to(R)),str(q.relative_to(R)),'docs/PREREG_LOG.txt','docs/OPS_LOG.txt',*['tools/handoff_20261106/'+n for n in names+['freeze_gpu0_day_authorization.py']]]
    with(R/'logs/prereg_publish.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
        for n in files:d=G/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,d)
        subprocess.run(['git','add',*files],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Honor user authorization to keep GPU0 past18JST today'],cwd=G,check=True);commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip();subprocess.run(['git','push','origin','main'],cwd=G,check=True)
    print(json.dumps({'utc':now,'doc_sha256':sha(doc),'commit':commit,'authorization_sha256':sha(p),'tests':test}))
if __name__=='__main__':main()
