"""Freeze the resource correction before controller v2 runs; preserve old numerical paths."""
from pathlib import Path
import ast,datetime,fcntl,hashlib,json,shutil,subprocess
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';G=R/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();doc=R/'docs/254_ADDENDUM11_AUXILIARY_WINDOW_PRIORITY.md';assert not doc.exists();assert not(B/'frozen_prompt_snapshot.json').exists();code=R/'tools/handoff_20261106/lease_priority_controller_v2.py';wrapper=R/'tools/handoff_20261106/wjb_tail_priority_worker_v2.py'
    for p in [code,wrapper]:ast.parse(p.read_text())
    original=(R/'tools/handoff_20261106/lease_priority_controller.py').read_text();expected=original.replace('if len(pending)>=256 or optional_hb_pending():','if len(pending)>=256:  # Auxiliary classification never opens a window by itself.').replace('signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);verify()','signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);verify();assert sha(Path(__file__))==load(BASE/"lease_priority_v2_publication.json")["controller_sha256"]').replace('wjb_tail_priority_worker.py','wjb_tail_priority_worker_v2.py');assert code.read_text()==expected
    def generate_calls(p):return[ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(p.read_text()))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='generate']
    assert generate_calls(wrapper)==generate_calls(R/'tools/handoff_20261106/wjb_tail_priority_worker.py')
    doc.write_text(f'''# PAIR500 addendum11: auxiliary judging must not repeatedly reserve two cards

Frozen UTC {now}, before controller_v2 or metadata wrapper_v2 starts. PAIR search is ongoing and PAIR outcome labels remain unread. A progress-only audit found the original auxiliary-pending trigger repeatedly opening GPU2/3 windows for WJB top2/tail caches. Tail generation progressed slowly despite prefix catch-up. This correction changes scheduling, not numerical generation/classification or analysis.

The incremental two-card window opens only when at least256 PAIR prefix classifier rows are pending, or through the unchanged final-search-closure scorer. WJB top2/tail pending files alone never open a new pre-closure window. An already-needed PAIR window may still use remaining bounded residency for the frozen sensitivities. Remaining auxiliary classification waits for a necessary PAIR window or the post-PAIR auxiliary queue; it does not gate PAIR reading. WJB/public generation keeps fixed s0,A,B order within each family, original shards and public batch8 composition. PAIR generation has priority; low-priority workers yield at existing atomic boundaries. GPU0 still releases18:00 JST; no colleague card/process or memory gate is changed.

Do not hot-edit a source used by a running worker. Preserve the old implementation and manifest. Request the old owned controller to drain; use its existing cooperative HB-yield signal and row/batch yielding, record before/after file-hash evidence, then launch the separately pinned v2 dispatcher through launch_job. The old four-line ownership/source checks remain; failure stops/checkpoints and never relaxes a gate. The new controller's only dispatch-policy change removes the auxiliary-only trigger; it additionally pins its own source and selects the metadata-only v2 tail wrapper. Underlying original generate calls are AST-identical.

## Metadata semantics for systemA/B

Public batch8 records already use injection_count=0 with a zero vector and prefill_hook_count=1. The common single-row generator's historical injection_count means hook calls, even for a zero vector, so its raw generation.injection_count remains1. Do not overwrite it or remove the zero hook to make a field equal0. The new wrapper additionally records nonzero_vector_injection_count=0, rho_runtime=0, prefill_hook_count=1 for systemA/B, system_text_sha256 and exact input hash, new_tokens, eos/observed EOS and cap flags. Original generation metadata remains intact. Existing and new wrapper provenance are distinguished by wrapper SHA, with no backfill. This is metadata observation only and preserves the passed zero-vector path and numeric behavior.

## Contextual and copyright reporting

PAIR does not call night/judge_all.py. It uses the official contextual template with original context, behavior and the frozen512-token generation clip. Both incremental and final HF classifiers stop on input>2048; the legacy >1900 overlapping split is not this path. Current CPU-only token-length audit is reported without outcome labels; repeat after full generation. No silent truncation or new chunking is introduced. WildGuard's >4096 sliding-window count remains separately reported at the frozen read.

Main tables retain the HarmBench400-row dataset inventory and separate standard200/contextual100/copyright100 rows, plus JBB100. Copyright MinHash is not harmfulness: do not show a pooled mixed-type ASR or average it with the other layers in the main table/abstract. Earlier permission for a labelled heterogeneous operational total is historical; this presentation is narrowed at user request before PAIR outcome reading. Raw per-layer results and all rows are retained.

## Draft dependencies

Before11/12, methods, dataset inventory/table, documented pipeline traps and limitations can be finalized now; results, abstract and introduction contribution claims await the locked PAIR read. The abstract result template is fixed separately with numeric placeholders, no absolute ASR and no mechanism sentence. Fill only from generated tables after both judges and benefit/cost results are read. Human review12/10 and manual token-expiry verification remain incomplete.
''')
    template=R/'docs/284_ABSTRACT_RESULT_SENTENCES_TEMPLATE.md';assert not template.exists();template.write_text('''# Abstract result-sentence template (numeric placeholders only)

Use after complete500-row/two-judge reading. If incomplete, leave this template unfilled and report incompleteness; do not silently edit the claims. Placeholder replacements are signed numeric table cells (and intervals where shown). HB/WG means HarmBench/WildGuard, not a pooled estimate. No absolute harmfulness rate is inserted.

With rule-scored PAIR-style prompts on HarmBench text behaviors (n=400) and JBB-Behaviors (n=100), paired learned-minus-norm-matched-random differences in judge ASR were {{HB_STANDARD_PP}}/{{WG_STANDARD_PP}} pp for standard behaviors (n=200), {{HB_CONTEXTUAL_PP}}/{{WG_CONTEXTUAL_PP}} pp for contextual behaviors (n=100), and {{HB_JBB_PP}}/{{WG_JBB_PP}} pp for JBB-Behaviors. Copyright behaviors (n=100) were assessed separately by MinHash, without a harmfulness claim. On the WildJailbreak evaluation set (n=2,000 adversarial harmful prompts), paired differences were {{WJB_HB_MAPPED_PP}}/{{WJB_WG_PP}} pp under HarmBench mapped-behavior/WildGuard judgments. Using refusal rule v2, learned-minus-random refusal differences were {{XSTEST_SAFE_PP}} pp on XSTest safe (n=250), {{OR_HARD_PP}} pp on OR-Bench-Hard (n=1,319), and {{WJB_BENIGN_PP}} pp on WildJailbreak evaluation benign prompts (n=210). The WildJailbreak behavior mapping is unverified; WildGuard uses related WildJailbreak training data; both judges are models without human calibration.
''')
    publication={'utc':now,'doc_sha256':sha(doc),'template_sha256':sha(template),'controller_sha256':sha(code),'tail_wrapper_sha256':sha(wrapper),'base_implementation_sha256':sha(B/'lease_priority_implementation.json'),'unchanged_numeric_source_sha256':{n:sha(R/n)for n in ['src/gen/common.py','tools/handoff_20261106/wjb_eval255_run.py','tools/handoff_20261106/prefix_hb_incremental_worker.py']},'generate_call_AST_identical':True,'PAIR_outcomes_read':False}
    p=B/'lease_priority_v2_publication.json';assert not p.exists();p.write_text(json.dumps(publication,indent=2)+'\n')
    for name in ['PREREG_LOG.txt','OPS_LOG.txt']:
        with(R/'docs'/name).open('a')as f:f.write(f'{now} PAIR254_RESOURCE_ADDENDUM11_FROZEN SHA={sha(doc)} controller_v2_SHA={sha(code)} remove auxiliary-only HB windows; no outcome read; raw hook count preserved/nonzero count explicit. Draft methods/traps/datasets/limits ready now; results/abstract/intro claims wait.\n')
    files=[str(doc.relative_to(R)),str(template.relative_to(R)),str(p.relative_to(R)),str(code.relative_to(R)),str(wrapper.relative_to(R)),'docs/PREREG_LOG.txt','docs/OPS_LOG.txt','tools/handoff_20261106/freeze_pair254_resource11.py','tools/handoff_20261106/audit_pair254_contextual_length.py','results/audit/pair500/tail_contextual_followup_20261109/contextual_length_audit.json']
    with(R/'logs/prereg_publish.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
        for n in files:p=G/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
        subprocess.run(['git','add',*files],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Freeze auxiliary-window correction, contextual audit and neutral result template'],cwd=G,check=True);commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip();subprocess.run(['git','push','origin','main'],cwd=G,check=True)
    print(json.dumps({'commit':commit,**publication}))
if __name__=='__main__':main()
