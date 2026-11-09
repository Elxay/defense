"""Activate logging-only generation change at a completed model boundary."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';T='tools/handoff_20261106/'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def main():
    memory=[int(x) for x in subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits','-i','2,3'],text=True).split()]
    if any(x>2000 for x in memory):print('WAIT_EXISTING_BATCH_MEMORY',memory);raise SystemExit(75)
    assert not subprocess.run(['pgrep','-f','python.*prefix_generate.py'],capture_output=True).stdout.strip(),'Wait for old target child exit'
    assert (Path('/proc/885736/status').read_text().split('State:',1)[1].splitlines()[0]).strip().startswith('T')
    assert sha(BASE/'prefix254_runtime.json')=='cf4c7167b76276c7019c8ad4267079e42e6c4cf994713b90655d908c0c4d517c'
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();assert not(BASE/'prefix254_dual_publication.json').exists()
    for name in ['prefix_generate.py','prefix_evaluate.py','pair500_wildguard_queue.py']:
        active=ROOT/(T+name);assert (ROOT/(T+name+'.dual_pending')).exists()
        active.write_bytes((ROOT/(T+name+'.dual_pending')).read_bytes())
    paths=[T+n for n in ['prefix_controller_dual.py','prefix_wildguard_queue.py','prefix_wg_batch_runner.py','prefix_wg_reuse.py','wjb_top2_shared_window.py','pair500_wildguard_queue.py','pair500_wildguard_run.py','prefix_generate.py','prefix_evaluate.py']]
    for n in paths:compile((ROOT/n).read_text(),n,'exec')
    remote="from pathlib import Path\nimport hashlib,json\nr=Path('/home/dell/Def');print(json.dumps({'model':hashlib.sha256((r/'models/WildGuard/DOWNLOAD_SHA256.json').read_bytes()).hexdigest(),'format':hashlib.sha256((r/'results/audit/pair500/wildguard/format5.json').read_bytes()).hexdigest()}))"
    pinned=json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=remote,text=True))
    doc=ROOT/'docs/254_ADDENDUM7_DUAL_PREFIX_AND_EARLY_WILDGUARD.md'
    doc.write_text(f'''# Scheduling addendum7: two innet lanes and early WildGuard scores

Frozen UTC {now}. This follows the user's instruction after the WJB harmful primary read but before any public-refusal condition effects are read. It changes scheduling and provenance, not analysis, prompts, vectors, alpha, or read locks. Existing prefix rows are retained. The original numeric runtime SHA remains cf4c7167b76276c7019c8ad4267079e42e6c4cf994713b90655d908c0c4d517c.

The old CPU dispatcher was paused; its already running CUDA batch finished without interruption. Source replacement occurs only after no prefix CUDA child remains and GPU2/3 both pass the existing <=2000MiB memory gate. Original generator numeric statements, single-row common helper and vector buffers are unchanged; new generator statements only write launch metadata before model loading. Old publication and every existing prefix file remain recorded. New dispatcher uses GPU2 andGPU3 with separate idle_gpu leases and wait_gpu; row-condition reservations prevent duplicate concurrent work. Alpha0 gets priority; another lane can process only rows whose uniform alpha0 already exists. Fixed condition order is traversed in bounded50-row chunks. Each launch saves accepted-prefix and batch layer counts before dispatch and before model loading. No intermediate labels are inspected.

Prefix generation signatures remain per-row prompt/row/runtime/core hashes. Device UUID/physical card are recorded. This does not claim an unperformed GPU2/GPU3 byte-equivalence test. Failed workers retain checkpoints and stop dispatch, with no gate relaxation. A termination request drains active batches before dispatcher exit. On search closure, drain both lanes, bind the final snapshot and use the already frozen completion/fallback policy. No WJB auxiliary conditions gain priority.

Early WildGuard uses only node01 physicalGPU0, neverPAIR GPU1/2. Immutable batches contain up to200 already generated rows in the existing interleaved condition order. The batch runner executes the original frozen pair500_wildguard_run.py main body verbatim, changing only its output directory and selecting an allowed condition. It verifies the same weights/template/format gate and uses the identical prompt+response, BF16 greedy32-token, per-field INVALID/length/copyright-applicability behavior. No new label totals, effects or summaries are read. Batch inputs, prompt/response hashes, generation-file hashes and raw classifier outputs remain private and immutable.

At search closure, stop new prescore batches and let the current batch finish. The normal final WG queue waits for this drain. It may reuse a score only after its original source SHA, model/template/runtime signatures, selected prompt and response hashes, and immutable prefix generation SHA all match the final canonical row. It preserves the original inference file/signature and adds an explicit provenance pointer while binding the unchanged labels to the final500-row input signature. Unscored rows are classified by the original final worker. A failed optional prescore never supplies invented scores; verified existing rows and remaining gaps stay explicit.

The PAIR reading lock remains: no alpha0 harmful labels or alpha-not-zero effects until search closes, final row coverage and both judges meet the previously frozen requirements. No prefix analysis. A cutoff-incomplete prefix is reported under the existing cutoff rule, never as a complete500-row census.

The first PAIR HarmBench window remains after target generation, with full model-file hashes and the fresh20-row gate before inference. Reuse that same loaded classifier to complete the five WJB top2 sensitivities old_s5/rand2/old_s6/rand3/old_s7, then scorePAIR. The original top2 template,512-token clip,greedy label and rawYes/No probability definition are retained. Store backend explicitly; original node fallback still applies only if its resource trigger holds. Top2 is addendum11 sensitivity, not addendum19's primary-read/wording gate, as now clarified by the user. Existing four-unit top2 result is labeled four-unit, not nine-unit.

No results-dependent stopping or resource change is introduced. The two-lane/early-score change is resource-driven and requested before public side reading; public and harmful sides will be reported together before any abstract result sentence is chosen. The previous overbroad interpretation treating full top2 as an additional#19 gate is corrected by this appended record.
''')
    pub={'utc':now,'doc_sha256':sha(doc),'code_sha256':{n:sha(ROOT/n) for n in paths},'pair_wildguard_source_sha256':sha(ROOT/(T+'pair500_wildguard_run.py')),'wildguard_model_manifest_sha256':pinned['model'],'wildguard_format_gate_sha256':pinned['format'],'numeric_runtime_sha256':sha(BASE/'prefix254_runtime.json')}
    save(BASE/'prefix254_dual_publication.json',pub)
    original=loadpub=json.loads((BASE/'prefix254_publication.json').read_text());save(BASE/'prefix254_publication_before_dual.json',original)
    for n in [T+'prefix_generate.py',T+'prefix_evaluate.py',T+'prefix_controller_dual.py',T+'wjb_top2_shared_window.py']:original['code_sha256'][n]=sha(ROOT/n)
    original['scheduling_amendment_sha256']=sha(doc);save(BASE/'prefix254_publication.json',original)
    cfgpath=BASE/'eval254_config.json';cfg=json.loads(cfgpath.read_text());save(BASE/'eval254_config_before_dual.json',cfg)
    for n in cfg['source_sha256']:cfg['source_sha256'][n]=sha(ROOT/n)
    cfg['dual_prefix_scheduling']={'utc':now,'doc_sha256':sha(doc)}
    for n in paths:cfg['source_sha256'][n]=sha(ROOT/n)
    save(cfgpath,cfg);ep=BASE/'eval254_publication.json';e=json.loads(ep.read_text());e['config_sha256']=sha(cfgpath);e['dual_prefix_addendum_sha256']=sha(doc);save(ep,e)
    copy=list(dict.fromkeys(paths+list(original['code_sha256'])+['results/audit/pair500/prefix254_publication.json','results/audit/pair500/prefix254_dual_publication.json','results/audit/pair500/wjb_mapping255.json','repos/HarmBench/data/behavior_datasets/harmbench_behaviors_text_all.csv']))
    subprocess.run(['rsync','-aR',*copy,'node01:/home/dell/Def/'],cwd=ROOT,check=True)
    for name in ['old_s5','rand2','old_s6','rand3','old_s7']:
        relative='results/audit/pair500/public255/harmful.private/'+name+'/wildjailbreak_harmful/'
        subprocess.run(['rsync','-aR',relative,'node01:/home/dell/Def/'],cwd=ROOT,check=True)
    for log in ['docs/PREREG_LOG.txt','docs/OPS_LOG.txt']:
        with (ROOT/log).open('a') as f:f.write(f'{now} DUAL_PREFIX_AND_EARLY_WG_SCHEDULING_FROZEN docSHA={sha(doc)} pubSHA={sha(BASE/"prefix254_dual_publication.json")} oldCUDA_batch_completed_untouched; original runtime/vector/core unchanged, GPU3 target generation not yet started. Top2 is sensitivity, not#19 gate; public results remain unread.\n')
    files=['docs/PREREG_LOG.txt','docs/OPS_LOG.txt',str(doc.relative_to(ROOT))]+paths+[T+'freeze_prefix_dual.py']
    files+=['results/audit/pair500/'+n for n in ['prefix254_dual_publication.json','prefix254_publication.json','prefix254_publication_before_dual.json','eval254_config.json','eval254_config_before_dual.json','eval254_publication.json','prefix254_dual_handoff.json']]
    save(BASE/'prefix254_dual_publish_files.json',list(dict.fromkeys(files)))
    print(json.dumps({'utc':now,'doc_sha256':sha(doc),'publication_sha256':sha(BASE/'prefix254_dual_publication.json'),'memory_mib':memory}))


if __name__=='__main__':main()
