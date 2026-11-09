"""Publish the borrowed-card evidence, coded follow-ups and numeric reports."""
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
def check(x,name):
    if isinstance(x,dict):
        for k,v in x.items():
            assert k not in {'prompt','response','text','completion','adversarial','vanilla','stored120','replay120','replay400','at120','at400'},(name,k)
            check(v,name)
    elif isinstance(x,list):
        for v in x:check(v,name)
def main():
    # Preserve byte-exact raw captures and the already-hashed generated report.
    attrs=ROOT/'.gitattributes';text=attrs.read_text() if attrs.exists() else ''
    for name in ['docs/255_PUBLIC_FOLLOWUP_AND_GPU0_HANDOFF.md','results/audit/pair500/gpu23_performance_check.txt','results/audit/pair500/gpu23_performance_after_borrow.txt']:
        entry=name+' whitespace=-blank-at-eof'
        if entry not in text:text+=entry+'\n'
    attrs.write_text(text)
    files=['.gitattributes','docs/255_PUBLIC_FOLLOWUP_AND_GPU0_HANDOFF.md','docs/PREREG_LOG.txt','docs/OPS_LOG.txt','paper/generated/public_refusal_followup.tex','paper/generated/public_refusal_results.tex']
    names=['public_nine_additional_counts.py','public_uncertain400.py','handoff_borrowed_controller.py','capture_borrowed_gpu_projects.py','borrowed_gpu_throughput.py','verify_gpu0_cooperative_release.py','export_gpu0_and_public_followup.py','publish_gpu0_public_followup.py']
    files += ['tools/handoff_20261106/'+n for n in names]
    artifacts=['gpu0_borrow_freeze_receipt.json','gpu0_zero20_result.json','gpu0_handoff_prefix_before.json','gpu0_handoff_checked.json','gpu0_handoff_launch.json','gpu0_cooperative_release_check.json','borrowed_hardware_signature_check.json','borrowed_gpu_projects_status.json','borrowed_gpu_measured_throughput.json','gpu23_thermal_counter_comparison.json','gpu23_performance_check.txt','gpu23_performance_after_borrow.txt','gpu0_public_followup_report_manifest.json']
    files += ['results/audit/pair500/'+n for n in artifacts]
    files += [str(p.relative_to(ROOT)) for p in (BASE/'public_followup_20261109').glob('*.json')]
    files=sorted(set(files));assert all('.private.' not in Path(n).name for n in files)
    for name in files:
        p=ROOT/name;assert p.is_file(),name
        if p.suffix=='.json':check(json.loads(p.read_text()),name)
        assert not re.search(r'hf_[A-Za-z0-9]{20,}',p.read_text()),('possible credential',name)
    with (ROOT/'logs/prereg_publish.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        pending=subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).splitlines()
        allowed=set(files)|{'manifests_gpu0_public_followup_20261109.json'}
        assert all(line[3:] in allowed for line in pending),'unrelated mirror modifications; refuse'
        now=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{now} GPU0_BORROWED_AND_PUBLIC_FOLLOWUP_READY hardware UUID prefix-normalization fix only, original generation/execution signatures retained; zero20 passed; borrowed row-boundary yield verified; PAIR restart count1; no PAIR condition effects read. reportSHA={sha(ROOT/"docs/255_PUBLIC_FOLLOWUP_AND_GPU0_HANDOFF.md")}\n')
        for name in files:
            p=REPO/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
        manifest='manifests_gpu0_public_followup_20261109.json';(REPO/manifest).write_text(json.dumps({'utc':now,'files':{n:sha(REPO/n) for n in files},'no_raw_prompt_or_reply_text':True,'PAIR_effects_read':False,'v2_primary_and_original120_guard_unchanged':True,'GPU0_expiry':'2026-11-09T18:00:00+09:00','PDF_rebuilt':False},ensure_ascii=False,indent=2)+'\n')
        subprocess.run(['git','add',*files,manifest],cwd=REPO,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=REPO,check=True)
        subprocess.run(['git','commit','-m','Record GPU0 gate and row-boundary release with public refusal follow-ups'],cwd=REPO,check=True);content=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
        with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} GPU0_PUBLIC_FOLLOWUP_CONTENT_COMMIT={content} aggregate/coded/hash/script artifacts only; no raw attack or output texts, vectors or weights.\n')
        shutil.copy2(ROOT/'docs/PREREG_LOG.txt',REPO/'docs/PREREG_LOG.txt');subprocess.run(['git','add','docs/PREREG_LOG.txt'],cwd=REPO,check=True);subprocess.run(['git','commit','-m','Log GPU0 and public follow-up publication'],cwd=REPO,check=True)
        subprocess.run(['git','push','origin','main'],cwd=REPO,check=True)
        result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'content_commit':content,'head_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'report_sha256':sha(ROOT/'docs/255_PUBLIC_FOLLOWUP_AND_GPU0_HANDOFF.md'),'manifest_sha256':sha(REPO/manifest),'files':len(files),'mirror_clean':not bool(subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip())}
        (BASE/'gpu0_public_followup_publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
