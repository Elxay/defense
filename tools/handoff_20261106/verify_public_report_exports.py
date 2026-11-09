"""Check source tables and retain prior export bytes after manuscript-only edits."""
from pathlib import Path
import datetime
import hashlib
import json
import re

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'public_read_20261109'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    previous=json.loads((OUT/'export_manifest.json').read_text());archive=OUT/'export_v1';archive.mkdir(exist_ok=True)
    for name,value in previous['files'].items():
        p=ROOT/name;text=p.read_text()
        if name.endswith('255_PUBLIC_ORDERED_READ_RESULTS.md'):text=text.split('\n摘要决定：')[0]
        if name.endswith('public_refusal_nine.tex'):
            text=text.replace('retain 238, 1301, and 210','retain238,1301,210').replace('at 120','at120').replace('WildGuard has 204 complete nine-unit pairs on the 210-row benign WildJailbreak set; its all-row difference bounds are 8.83--9.43 pp.','WildGuard has204 complete nine-unit pairs on the210-row benign WildJailbreak set; its all-row difference bounds are8.83--9.43pp.')
        if name.endswith('public_refusal_results.tex'):text=text.replace('same 120','same120').replace('fixed 30','fixed30').replace('reported 200','reported200').replace('difference is -','difference is-')
        q=archive/p.name;q.write_text(text);assert sha(q)==value,(name,'previous export reconstruction mismatch')
    # Compact generated headers so they fit a two-column spanning table.
    p=ROOT/'paper/tables/wjb_official_units.tex';text=p.read_text().replace('Condition & HB harmful (\\%) & WG harmful (\\%) & WG refusal (\\%) & v2 refusal (\\%) & WG harmful among WG nonrefusals (\\%)','Condition & HB harm \\% & WG harm \\% & WG refusal \\% & v2 refusal \\% & WG harm $|$ nonrefusal \\%');p.write_text(text)
    p=ROOT/'paper/tables/wjb_exposure.tex';text=p.read_text().replace('Mapped exposure layer & Rows & Behavior groups & HB difference (pp) & WG difference (pp) & WG complete pairs','Mapped layer & Rows & Groups & HB difference (pp) & WG difference (pp) & WG pairs');p.write_text(text)
    checks=[]
    for p in (ROOT/'paper').rglob('*.tex'):
        if p.name=='acl.tex':continue
        text=p.read_text()
        for target in re.findall(r'\\input\{([^}]+)\}',text):
            if not target.endswith('.tex'):target+='.tex'
            assert (ROOT/'paper'/target).exists(),(p.name,target)
        checks.append(str(p.relative_to(ROOT)))
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tex_input_paths_checked':len(checks),'prior_export_bytes_recovered_and_hash_verified':{str((archive/Path(name).name).relative_to(ROOT)):value for name,value in previous['files'].items()},'current_report_sha256':sha(ROOT/'docs/255_PUBLIC_ORDERED_READ_RESULTS.md'),'pdf_rebuilt':False,'tex_engine_available':False,'PAIR500_outcomes_read':False}
    (BASE/'public_report_export_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    # Refresh the current manifest after formatting changes; prior immutable export stays intact.
    p=BASE/'public_nine_manuscript_update.json';manifest=json.loads(p.read_text())
    for name in manifest['files']:manifest['files'][name]=sha(ROOT/name)
    manifest['export_checks_sha256']=sha(BASE/'public_report_export_checks.json');p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
