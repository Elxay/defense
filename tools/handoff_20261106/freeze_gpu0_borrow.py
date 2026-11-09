"""Freeze and publish the borrowed-card gate before any GPU0 generation."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import shutil
import subprocess

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';REPO=ROOT/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    target=BASE/'gpu0_borrow_publication.json';assert not target.exists(),'already frozen'
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    scripts=['build_gpu0_borrow_extension.py','borrowed_gpu_support.py','prefix_generate_borrowed.py','prefix_controller_borrowed.py','gpu0_zero20_gate.py','freeze_gpu0_borrow.py']
    sources=['tools/handoff_20261106/'+s for s in scripts]
    manifest={'frozen_utc':now,'borrow_until_utc':'2026-11-09T09:00:00+00:00','hzx_notification':'user confirmed advance notification in this chat before GPU0 launch','old_prefix_publication_sha256':sha(BASE/'prefix254_publication.json'),'runtime_sha256':sha(BASE/'prefix254_runtime.json'),'code_sha256':{s:sha(ROOT/s) for s in sources},'PAIR500_effects_read':False,'node01_gpu0':'reserved for existing WildGuard queue, no generation','failed_gate':'GPU0 remains disabled; existing GPU2/3 results retained'}
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    doc=ROOT/'docs/254_ADDENDUM8_BORROWED_GPU0_GATE_AND_RELEASE.md'
    doc.write_text(f'''# Scheduling addendum8: borrowed innet GPU0

Frozen UTC {now}, before any GPU0 gate or PAIR-prefix generation. The user has confirmed advance notification to hzx. GPU0 is borrowed until 2026-11-09 18:00 JST at the latest. If hzx requests it earlier, create results/audit/pair500/gpu0_reclaim.flag; the worker finishes the current row, atomically saves it, and exits before another row. An external compute context on GPU0 also triggers cooperative yield; external processes are never killed or modified.

This changes scheduling only. PAIR configuration, fixed condition traversal, prompts, alpha, vectors, target/helper numeric calls, read lock, handoff priorities, existing node fallback and WJB deferred-condition rules are unchanged. No PAIR-500 alpha-not-zero effects or alpha-zero harmfulness labels have been read. node01 GPU0 remains reserved for the registered early WildGuard classifier, including between-batch model loading; its desktop graphics baseline does not make it available to generation.

Before production on GPU0, replay the first20 frozen-order prompts at alpha0 using the same single-row generate_with_injection path and2400-token cap. Compare their full text bytes and input-ID hashes against the immutable GPU2/3 reference files. Record reference/new hashes, injection_count=1, rho_runtime=0 and actual device_uuid. Only20/20 byte and input agreement permits GPU0 production; otherwise disable the borrowed lane, retain the existing two-card outputs, and report the failed gate without changing a threshold or interpreting outcomes.

The old dispatcher drains its active batches before relinquishing controller.lock. The new single dispatcher reserves disjoint(condition,row-ID) work in memory for GPU2, GPU3 and gated GPU0. Each card has its existing idle_gpu lease, wait_gpu<=2000MiB gate and launch_job registry. Repeated rows are verified and skipped. A new execution signature binds the unchanged prompt/row/runtime signature to device_uuid and physical card; the original computational signature remains compatible with previously saved rows. Numeric model-load and generate_with_injection call ASTs are identical to the old worker. Existing source files and inference results are preserved.

Dispatch metadata saves prefix/batch functional-layer counts before launch. Every new row records elapsed seconds. Report per-condition/card rows per hour from measured completed work, separately from model loading and waiting; do not assume a1.5x speedup. At18:00 JST or early reclaim, GPU0 closes at a row boundary while the other two lanes continue. After search closure, existing final-generation and classifier-window fallback rules still apply; the borrowed card does not change classifier precision or placement.

Additional requested reporting remains post-hoc descriptive: absolute refusal rates, per-seed learned-minus-alpha0 differences and a t interval across the five seed differences; XSTest unsafe per-condition counts; exact regeneration of the six fixed-seed sample selections and hashes. Re-read the five previously uncertain benign WildJailbreak random outputs after400-token regeneration, explicitly check the120-token prefix, retain the frozen120-token labels and failed conservative line, and store only coded labels/hashes in Git. No new thresholds or outcome-driven scheduling.

Runtime SHA256: {manifest['runtime_sha256']}.
Borrowed-card publication SHA256: {sha(target)}.
''')
    line=f'{now} GPU0_BORROW_SCHEDULE_FROZEN docSHA={sha(doc)} publicationSHA={sha(target)} hzx notified confirmed by user; expires18JST or early reclaim; zero20 gate required; PAIR outcomes unread; OOM restart count remains1 (historical worker2295103, not a new restart).\n'
    for name in ['docs/PREREG_LOG.txt','docs/OPS_LOG.txt']:
        with (ROOT/name).open('a') as f:f.write(line)
    paths=sources+[str(p.relative_to(ROOT)) for p in [target,doc,BASE/'gpu0_borrow_numeric_check.json']]+['docs/PREREG_LOG.txt','docs/OPS_LOG.txt']
    with (ROOT/'logs/prereg_publish.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip()
        for name in paths:
            dest=REPO/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
        subprocess.run(['git','add',*paths],cwd=REPO,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=REPO,check=True)
        subprocess.run(['git','commit','-m','Freeze borrowed GPU0 row-boundary release and twenty-row gate before launch'],cwd=REPO,check=True);commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
        subprocess.run(['git','push','origin','main'],cwd=REPO,check=True)
    result={'frozen_utc':now,'commit':commit,'doc_sha256':sha(doc),'publication_sha256':sha(target),'notification_confirmed':True}
    (BASE/'gpu0_borrow_freeze_receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
