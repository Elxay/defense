"""Publish narrative revision and provenance without new test outcomes."""
from pathlib import Path
import csv,datetime,fcntl,hashlib,json,re,shutil,subprocess
R=Path('/data/HZX/Def');P=R/'paper';O=R/'results/audit/crossmodel287';G=R/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 table=P/'tables/measurement_checklist.tex';text=table.read_text();a,b=text.split('\\midrule\n',1);body,end=b.split('\\bottomrule',1)
 parsed=[]
 for line in body.splitlines():
  if not line.strip():continue
  values=[v.strip()for v in line.removesuffix('\\\\').split('&')];assert len(values)==4
  parsed.append(dict(zip(['trigger','impact','detection','safeguard'],values))|{'source_file':'paper/sections/appendix_pitfalls.tex','source_sha256':sha(P/'sections/appendix_pitfalls.tex')})
 data=P/'data/measurement_checklist.csv'
 with data.open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(parsed[0]),lineterminator='\n');w.writeheader();w.writerows(parsed)
 rendered=list(csv.DictReader(data.open()));table.write_text(a+'\\midrule\n'+'\n'.join(' & '.join(x[k]for k in ['trigger','impact','detection','safeguard'])+' \\\\'for x in rendered)+'\n\\bottomrule'+end)
 intro=(P/'sections/01_introduction.tex').read_text();macros={k:v for k,v in re.findall(r'\\newcommand\{\\(\w+)\}\{([^}]+)\}',(P/'generated/argument_numbers.tex').read_text())}
 plain=intro
 for name,value in macros.items():plain=plain.replace('\\'+name+'{}',value)
 plain=re.sub(r'\\cite\w*\{[^}]+\}','',plain);plain=plain.replace('\\section{Introduction}\n\\label{sec:introduction}\n','').replace('\\begin{itemize}','').replace('\\end{itemize}','')
 plain=re.sub(r'\\item \\textbf\{([^}]+)\}',r'- **\1**',plain)
 doc=R/'docs/288_ARGUMENT_READINGS_AND_ARR_CHECK.md'
 doc.write_text(f'''# Narrative argument, readings and official submission requirements

UTC {now}. Editorial revision after completed WJB/public reads; PAIR-500 labels remain unopened. Numeric prose macros come from argument_numeric_receipt.json, SHA256 {sha(O/'argument_numeric_receipt.json')}. Harmful additional19--23pp is learned-minus-random. Public9pp and0.4pp in the introduction are explicitly learned-minus-alpha0; OR is5.883pp against alpha0 and3.950pp against random. Most-refusal association is post-hoc and is not causal attribution. The abstract remains method-only until the all13/two-judge PAIR read.

## Introduction and contributions

{plain}

## Current directory

1 Introduction; 2 Related Work; 3 Experimental Setup (models/intervention, samples/exposure, outcomes/judges, statistics/log chronology); 4 Results (random controls, refusal association, wrapper-associated costs, zero-training baselines); 5 Measurement Audit and Reporting Checklist; 6 Limitations; unnumbered Ethical Considerations; references. Appendices retain initialization/decomposition, exposure and closed incomplete data composition, detailed measurement audit, provenance/chronology and auxiliary frontier sensitivity. The duplicate main results4.4 audit was merged into section5. The original eight detailed audit subsections remain in the appendix; the main text has one six-row checklist table and four prose explanations.

## Five required readings: evidence and comparison

The existing docs282 already records the five primary full texts, version identifiers, three-line notes and PDF hashes. This update reopens the following primary method/result/limitation sections, rather than claiming that only one paper had previously been read. No cited effect size is imported as calibration of our output distribution.

**ReFT, v3, §§3--6** https://arxiv.org/html/2404.03592v3
1. It learns representation-dependent low-rank edits with the base weights frozen and specified prompt positions/layers.
2. It informs our setup section; our constant one-position vector is a restricted, differently trained intervention.
3. No direct conflict: task-adaptation performance does not establish jailbreak-defense safety or our random/benign contrasts.

**BiPO, v2, §3.2/Algorithm1, §4.2/Table4 and §4.3** https://arxiv.org/html/2406.00045v2
1. It learns a fixed vector from paired preferences using random positive/negative direction signs and applies steering across tokens.
2. It informs the learned-vector comparison; its safety example uses different data, signs, injection positions and model judge.
3. No numerical replication claim: directional controllability does not contradict our fixed-protocol safety-versus-benign-cost audit.

**Steering Safely or Off a Cliff?, EACL2026, §§3--7 and Limitations** https://aclanthology.org/2026.eacl-long.268/
1. It evaluates general specificity, related control preservation and robustness under distribution shifts.
2. It informs our paired harmful/benign results and limitations; its over-refusal intervention increases benign compliance.
3. The opposite training direction and different safety metrics preclude a common-mechanism claim; efficacy alone being insufficient is compatible with our framing.

**How Reliable Is Your Jailbreak Judge?, v2, §§3--6** https://arxiv.org/html/2606.25487v2
1. It compares judges on596 human-majority HarmBench validation pairs and separates content-preserving framing tests from a classifier attack.
2. It informs the measurement section and our requirement to distinguish a harmfulness flip from refusal labels.
3. Its corpus, quantization and prompted judges differ; we neither transfer its precision nor apply its proposed numeric correction to WJB.

**An Empirical Measurement of Jailbreaking Evaluators, v1, §§3--7** https://arxiv.org/html/2609.10594v1
1. It compares six evaluators on two human-labeled corpora, including a nonrefusal-selected corpus, with a shared backbone where applicable.
2. It informs our cross-judge and sampling-scope discussion; its StrongReject variant is the rubric judge rather than the trained scorer.
3. Evaluator dependence is compatible with our results; its evaluator ranking does not validate our model labels or transfer across distributions.

**Rogue Scalpel, v2, §§3.2/3.4/5** https://arxiv.org/html/2509.22067v2
The v2 text gives1--13% increased compliance and applies a fixed vector across prompt and generated tokens; §3.4 identifies JailbreakBench. We use a once-only final-prompt intervention and observe random-direction judged-ASR decreases. These are different protocols and input selection, not the same measured phenomenon or an explanation established by our experiments.

## Official ACL/ARR check, read today

Primary pages: https://2027.aclweb.org/calls/main/ ; https://aclrollingreview.org/cfp ; https://aclrollingreview.org/authorchecklist ; https://aclrollingreview.org/responsibleNLPresearch/ .

The current ACL2027 call lists ARR submission on2027-01-04,23:59 UTC-12 (AoE), rather than an assumed deadline. ARR long papers allow8 content pages, with required Limitations and optional Ethical Considerations after the conclusion outside that limit, and unlimited references. The current sources have no conclusion section yet; add a concise evidence-bounded conclusion before Limitations in the complete draft. No compiled page count is asserted: no TeX engine is installed here.

The review PDF and supplements/repository links must be anonymized. The post-2024 preprint rule does not remove review-PDF anonymity; a selected no-nonanonymous-preprint commitment is binding. The Responsible NLP checklist is part of the submission form and needs section pointers or explanations, including artifact licenses, annotation and AI assistance. AI writing/coding/research assistance must be disclosed in the applicable checklist/acknowledgment form, with authors responsible for all claims. The sustainable reviewing policy applies fromOctober2026: a qualified service contributor may cover at most2 submissions and must register within48h after the deadline. This check does not perform account registration or claim service eligibility.

No checked rule requires publishing raw attack material. ID/hash-only release is our disclosed choice, with a reproducibility limitation, not an ACL ban. Ethics text covers attack/steering dual use, no raw attacks/harmful outputs in Git, and WildGuard's Apache-2.0 model-card license plus accepted AI2 Responsible Use Guidelines. Source https://huggingface.co/allenai/wildguard . A model license does not license every underlying dataset.

## Remaining states

The data-composition intervention stays closed incomplete, appendix only. New-model ports are not counted as completed evidence. Model annotation/GPT review remains without human calibration; precise historical annotator snapshots are not reconstructed. The12/10 human-review date and token expiry check remain pending. Methods, measurement audit, dataset scope and limitations can be revised before11/12; results, abstract and numeric contributions receive the locked PAIR update only after admission. No new mechanism claim or PAIR result was added.

Source QA checks input existence, duplicate labels and citation keys. New checklist table is regenerated from paper/data/measurement_checklist.csv. No rebuilt PDF or page-count guarantee is claimed.
''')
 for name in ['PREREG_LOG.txt','OPS_LOG.txt']:
  with(R/'docs'/name).open('a')as f:f.write(f'{now} NARRATIVE_AND_READING_REVISION doc288_SHA={sha(doc)} intro_SHA={sha(P/"sections/01_introduction.tex")} three contributions; one main checklist; detailed audit appendix; primary readings/ARR checked; abstract pending lockedPAIR read; no PAIR outcomes read, no PDF rebuilt.\n')
 files=[str(doc.relative_to(R)),'docs/PREREG_LOG.txt','docs/OPS_LOG.txt',
  'tools/handoff_20261106/revise_argument_and_readings287.py','tools/handoff_20261106/finalize_manuscript287.py',
  'tools/handoff_20261106/crossmodel287_template_checks.py','tools/handoff_20261106/crossmodel287_vicuna_http_download.py',
  'results/audit/crossmodel287/argument_numeric_receipt.json','results/audit/crossmodel287/manuscript_revision_receipt.json',
  'paper/main.tex','paper/data/measurement_checklist.csv','paper/tables/measurement_checklist.tex','paper/generated/argument_numbers.tex',
  *['paper/sections/'+n for n in ['01_introduction.tex','02_related_work.tex','04_results.tex','05_traps.tex','06_limitations.tex','07_ethics.tex','appendix_pitfalls.tex']]]
 for key in ['qwen','gemma','vicuna']:
  q=O/(key+'_actual_AB_render.json')
  if q.exists():files.append(str(q.relative_to(R)))
 for key in ['qwen']:
  p=O/(key+'_preflight.json')
  if p.exists():
   # Copy a stable, coded-only snapshot, not the live mutable receipt.
   x=json.loads(p.read_text());q=O/(key+'_preflight_published_snapshot.json');q.write_text(json.dumps(x,indent=2)+'\n');files.append(str(q.relative_to(R)))
 with(R/'logs/prereg_publish.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
  for name in files:
   assert not re.search(r'hf_[A-Za-z0-9]{20,}',(R/name).read_text())
   p=G/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,p)
  manifest='manifests_narrative287.json';(G/manifest).write_text(json.dumps({'utc':now,'files':{n:sha(G/n)for n in files},'PAIR_effects_read':False,'raw_attack_or_output_added':False,'PDF_rebuilt':False},indent=2)+'\n')
  subprocess.run(['git','add',*files,manifest],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Tighten introduction, consolidate measurement audit and verify primary readings'],cwd=G,check=True);commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip();subprocess.run(['git','push','origin','main'],cwd=G,check=True)
 print(json.dumps({'utc':now,'commit':commit,'document288_sha256':sha(doc),'intro_sha256':sha(P/'sections/01_introduction.tex'),'checklist_CSV_sha256':sha(data)}))
if __name__=='__main__':main()
