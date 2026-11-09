"""Publish post-hoc tables/coded review and immutable handoff evidence only."""
from pathlib import Path
import datetime,fcntl,hashlib,json,re,shutil,subprocess
ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';REPO=ROOT/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(x,name):
    if isinstance(x,dict):
        for k,v in x.items():
            assert k not in {'prompt','response','text','baseline_response','task','generation'},(name,k)
            check(v,name)
    elif isinstance(x,list):
        for v in x:check(v,name)
def main():
    files=['docs/255_BENEFIT_COST_POSTHOC_AND_XSTEST_UNSAFE.md','paper/data/benefit_cost_posthoc.csv','paper/tables/benefit_cost_posthoc.tex','paper/generated/benefit_cost_posthoc.tex','paper/sections/04_results.tex','docs/PREREG_LOG.txt','docs/OPS_LOG.txt','results/audit/pair500/lease_priority_implementation_publication.json']
    files+=['tools/handoff_20261106/'+n for n in ['benefit_cost_posthoc_and_unsafe_sample.py','export_benefit_cost_posthoc.py','lease_priority_status.py','measure_prefix_loading_cost.py','verify_tail_source_rows.py','lease_priority_event_monitor.py','publish_benefit_cost_posthoc.py']]
    files +=[str(p.relative_to(ROOT))for p in(BASE/'lease_priority_followup_20261109').glob('*.json')if'.private.'not in p.name]
    files +=['results/audit/pair500/lease_priority/'+n for n in ['handoff_before.json','handoff_complete.json','held_wjb_WG_queue.json','source_rows_preflight.json','system_config_preflight.json','contextual_length_preflight.json','prefix_loading_cost.json']]
    for name in files:
        p=ROOT/name;assert p.is_file(),name
        if p.suffix=='.json':check(json.loads(p.read_text()),name)
        assert not re.search(r'hf_[A-Za-z0-9]{20,}',p.read_text()),('credential',name)
    with(ROOT/'logs/prereg_publish.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip()
        for name in files:p=REPO/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
        manifest='manifests_benefit_cost_posthoc_20261109.json';(REPO/manifest).write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{n:sha(REPO/n)for n in files},'post_hoc':True,'PAIR_effects_read':False,'no_raw_prompt_or_response_text':True,'narrow_and_broad_unsafe_coding_both_retained':True},indent=2)+'\n')
        subprocess.run(['git','add',*files,manifest],cwd=REPO,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=REPO,check=True);subprocess.run(['git','commit','-m','Report post-hoc benefit-cost juxtaposition and targeted unsafe refusal wording audit'],cwd=REPO,check=True);content=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
        with(ROOT/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} BENEFIT_COST_POSTHOC_CONTENT_COMMIT={content} codedlabels/counts/hashes/scripts only, no raw attacks/outputs; primary v2 unchanged.\n')
        shutil.copy2(ROOT/'docs/PREREG_LOG.txt',REPO/'docs/PREREG_LOG.txt');subprocess.run(['git','add','docs/PREREG_LOG.txt'],cwd=REPO,check=True);subprocess.run(['git','commit','-m','Log post-hoc table publication'],cwd=REPO,check=True);subprocess.run(['git','push','origin','main'],cwd=REPO,check=True)
        result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'content_commit':content,'head_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'table_json_sha256':sha(BASE/'lease_priority_followup_20261109/benefit_cost_posthoc.json'),'report_sha256':sha(ROOT/'docs/255_BENEFIT_COST_POSTHOC_AND_XSTEST_UNSAFE.md')};(BASE/'lease_priority_followup_20261109/publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
