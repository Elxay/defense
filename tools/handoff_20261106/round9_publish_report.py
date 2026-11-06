"""Publish numeric repeat report, manuscript paragraph, and code/hash provenance only."""
from pathlib import Path
import json,datetime,hashlib,subprocess,fcntl,shutil
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round9';R=B/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert(O/'repeat_comparison.json').exists();subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(B/'tools/handoff_20261106/round9_report.py')],check=True)
repeat=json.loads((O/'repeat_comparison.json').read_text());now=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=B/'docs/236_PAPER_POSITION_v2.md';text=p.read_text();key='2026-11-07追加2生效：'
if key not in text:
 text+='\n\n'+key+'原旧seed3复建≤1标签门槛仍为失败记录，当前按用户授权的252_ADDENDUM2_RETRAINED_CONTROLS.md比较同流水线重训对照与处理，不用历史冻结向量作主对照。五seed配对均值改善≥2pp+t区间排除0及均值护栏不变，alpha匹配重训对照自身ASR。所有目标已完成全文任务完成筛选；重复性及事后敏感性见272。\n';q=p.with_suffix('.tmp');q.write_text(text);q.replace(p)
with(B/'docs/PREREG_LOG.txt').open('a')as log:log.write(now+' SAMEPIPELINE_REPEAT_AB_COMPLETE sameinit/targets/worker/card_verified, cos='+str(repeat['cosine'])+' labelchanges='+str(repeat['label_changes'])+' up='+str(repeat['up'])+' down='+str(repeat['down'])+' harmfulcounts='+str(repeat['harmful_counts'])+'; A remains predetermined maincontrol; oldgatefailedrecord unchanged; rootcause limited to observedrepeatvariation, no seedcloud variance decomposition.\n')
public=['docs/272_RETRAINED_CONTROLS_AND_REPEATS.md','docs/251_EVAL_TRAPS_DRAFT.md','docs/236_PAPER_POSITION_v2.md','docs/PREREG_LOG.txt']+[str(p.relative_to(B))for p in(B/'tools/handoff_20261106').glob('round9*')]+['tools/handoff_20261106/node01_launch_round9.sh']
private=['historical_rebuild_details.json','repeat_comparison.json','doc250_posthoc_exclusion_spec.json','doc250_posthoc_sensitivity.json','style_top_neighbors_final60.json','target_followup_review.json']
with(B/'logs/prereg_publish.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True).strip()
 for name in public:shutil.copy2(B/name,R/name)
 manifest='manifests_round9_repeats_and_targets.json';(R/manifest).write_text(json.dumps(dict(utc=now,public_files={n:sha(B/n)for n in public},private_source_hashes={n:sha(O/n)for n in private},final_targets_sha256=sha(B/'results/style_retrained/style_training_targets.json'),addendum2_sha256=sha(B/'docs/252_ADDENDUM2_RETRAINED_CONTROLS.md'),no_raw_attack_or_output_text=True),indent=2)+'\n')
 subprocess.run(['git','add',*public,manifest],cwd=R,check=True);subprocess.run(['git','commit','-m','Record same-pipeline seed repeat and paired-control intervention protocol'],cwd=R,check=True);content=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
 with(B/'docs/PREREG_LOG.txt').open('a')as log:log.write(now+' ROUND9_REPEAT_REPORT_CONTENT_COMMIT='+content+'\n')
 shutil.copy2(B/'docs/PREREG_LOG.txt',R/'docs/PREREG_LOG.txt');subprocess.run(['git','add','docs/PREREG_LOG.txt'],cwd=R,check=True);subprocess.run(['git','commit','-m','Log repeat report publication'],cwd=R,check=True);subprocess.run(['git','push','origin','main'],cwd=R,check=True)
 result=dict(content_commit=content,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),report_sha256=sha(B/'docs/272_RETRAINED_CONTROLS_AND_REPEATS.md'));(O/'report_publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
