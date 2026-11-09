"""Publish only coded/aggregate artifacts and source; never raw model texts."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import re
import shutil
import subprocess

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';REPO=ROOT/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()
def check_json(x,path):
    if isinstance(x,dict):
        for key,value in x.items():
            assert key not in {'prompt','response','text','completion','adversarial','vanilla','original_prompt','model_output'},(path,'raw content key',key)
            check_json(value,path)
    elif isinstance(x,list):
        for value in x:check_json(value,path)

def main():
    files=['docs/255_PUBLIC_ORDERED_READ_RESULTS.md','docs/255_NINE_UNIT_SUPPLEMENTAL_TABLES.md','docs/PREREG_LOG.txt','docs/OPS_LOG.txt',
        'paper/sections/04_results.tex','paper/sections/05_traps.tex','paper/sections/06_limitations.tex',
        'paper/data/wjb_official_units.csv','paper/data/public_refusal_nine.csv','paper/data/wjb_harm_public_refusal_points.csv',
        'paper/tables/public_refusal_nine.tex','paper/tables/wjb_official_units.tex','paper/tables/wjb_exposure.tex','paper/generated/public_refusal_results.tex','paper/generated/wjb_nine_scope.tex']
    scripts=['public_refusal_ordered_read.py','public_refusal_scatter.py','recall_labels_io.py','finalize_public_recall.py','export_public_refusal_read.py','wjb_nine_supplement_tables.py','finish_public_and_nine_report.py','check_prefix_wg_reuse.py','capture_public_nine_completion_status.py','verify_public_report_exports.py','publish_public_nine_completion.py']
    files += ['tools/handoff_20261106/'+name for name in scripts]
    files += [str(p.relative_to(ROOT)) for p in (BASE/'public_read_20261109').glob('*.json') if '.private.' not in p.name]
    files += [str(p.relative_to(ROOT)) for p in (BASE/'public_read_20261109/export_v1').iterdir()]
    files += ['results/audit/pair500/nine_read_20261109/'+name for name in ['supplemental_tables.json','token_length_diagnostic.json','alpha0_701_prompt_length_correction.json']]
    files += ['results/audit/pair500/'+name for name in ['public_nine_manuscript_update.json','public_report_export_checks.json','public_nine_completion_status.json','prefix254_dual_launches.json','prefix254_dual_handoff.json']]
    for stem in ['wjb_harm_public_refusal_all','wjb_harm_public_refusal_keep60_unseen','wjb_harm_public_refusal_all_labels_v2','wjb_harm_public_refusal_keep60_unseen_labels_v2']:
        for ext in ['png','pdf']:files.append(f'paper/figures/{stem}.{ext}')
    files=sorted(set(files))
    for name in files:
        p=ROOT/name;assert p.is_file(),name;assert '.private.' not in p.name
        if p.suffix=='.json':check_json(json.loads(p.read_text()),name)
        if p.suffix not in ['.pdf','.png']:
            assert not re.search(r'hf_[A-Za-z0-9]{20,}',p.read_text()),('possible credential',name)
    with (ROOT/'logs/prereg_publish.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);assert not git('status','--porcelain'),'publication mirror must be clean'
        now=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{now} PUBLIC_NINE_FINAL_MANUSCRIPT_MANIFEST_SHA={sha(BASE/"public_nine_manuscript_update.json")} supersedes prior manuscript export hashes only; numeric read stages unchanged. Prior export bytes retained in export_v1 and independently hash-checked. Early-WG cache-rebind synthetic check passed (same-input reuse; changed-prompt rejection; original inference bytes retained).\n')
        for name in files:
            dst=REPO/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
        manifest={'utc':now,'files':{name:sha(REPO/name) for name in files},'no_raw_attack_or_output_text':True,'public_primary':'v2 unchanged','public_annotator':'current GPT-6-family conversation, exact serving snapshot unavailable; shared context; not human calibration','PAIR500_outcomes_read':False,'PDF_rebuilt':False}
        manifestpath='manifests_public_nine_completion_20261109.json';(REPO/manifestpath).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        subprocess.run(['git','add',*files,manifestpath],cwd=REPO,check=True)
        subprocess.run(['git','diff','--cached','--check'],cwd=REPO,check=True)
        subprocess.run(['git','commit','-m','Report public refusal costs and coded audits alongside nine-unit harmfulness results'],cwd=REPO,check=True)
        content=git('rev-parse','HEAD')
        with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} PUBLIC_NINE_RESULTS_CONTENT_COMMIT={content} counts/codedlabels/hashes/scripts/figures only; no attack texts, outputs, vectors or weights.\n')
        shutil.copy2(ROOT/'docs/PREREG_LOG.txt',REPO/'docs/PREREG_LOG.txt')
        subprocess.run(['git','add','docs/PREREG_LOG.txt'],cwd=REPO,check=True)
        subprocess.run(['git','commit','-m','Log public refusal results publication'],cwd=REPO,check=True)
        subprocess.run(['git','push','origin','main'],cwd=REPO,check=True)
        result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'content_commit':content,'head_commit':git('rev-parse','HEAD'),'report_sha256':sha(ROOT/'docs/255_PUBLIC_ORDERED_READ_RESULTS.md'),'supplemental_sha256':sha(BASE/'nine_read_20261109/supplemental_tables.json'),'manifest_sha256':sha(REPO/manifestpath),'files':len(files),'mirror_clean':not bool(git('status','--porcelain'))}
        (BASE/'public_nine_completion_publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
