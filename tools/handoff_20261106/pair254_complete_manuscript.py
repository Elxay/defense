"""Update prose only after the immutable eight-step read is complete."""
from pathlib import Path
import datetime,hashlib,json,re,shutil
R=Path('/data/HZX/Def');P=R/'paper';B=R/'results/audit/pair500';D=B/'read_order10/ordered_results';O=B/'read_order10/published_tables'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert all((D/f'{i:02d}.json').exists()for i in range(1,9))
 effect=json.loads((D/'04.json').read_text())['data']['primary']
 numbers=P/'generated/pair500_numbers.tex'
 numbers.write_text(''.join('\\newcommand{\\'+name+'}{'+f'{abs(effect[judge]["all_retained"]["estimate"]["row_mean_pp"]):.0f}'+'}\n'for name,judge in [('pairExtraHB','HB'),('pairExtraWG','WildGuard')]))
 main=P/'main.tex';s=main.read_text()
 if '\\input{generated/pair500_numbers}'not in s:s=s.replace('\\input{generated/argument_numbers}','\\input{generated/argument_numbers}\n\\input{generated/pair500_numbers}')
 abstract=r'''A lower automated attack success rate (ASR) does not by itself establish a better jailbreak defense. We audit a minimal learned intervention: one vector added once at the final prompt token of Llama-3.1-8B-Instruct. Our evaluation pairs harmfulness scores with norm-matched random controls, public refusal benchmarks, and benign requests with and without adversarial wrappers. Random vectors alone lower judged ASR by up to\valRandomMaxDrop{} percentage points on success-filtered prompts but at most about\wjbRandomMaxDrop{} on the WildJailbreak evaluation. Learned vectors lower it a further\wjbExtraMinDrop{}--\wjbExtraMaxDrop{} points there; on a new fixed rule-scored PAIR-style prompt set, the additional decrease is about\pairExtraWG{}--\pairExtraHB{} points across two model judges. In a post-hoc decomposition, most decreases accompany refusals. Benign refusal costs relative to random controls are about9 points on wrapped WildJailbreak requests and4 on OR-Bench-Hard; the XSTest safe difference is small and uncertain. Paired benign tests reproduce a wrapper-associated refusal gap. In our own pipeline, truncation, reference behaviors, decoding paths, refusal rules, and retraining variation also shift reported quantities. Model judgments remain uncalibrated by humans. We recommend reporting harmfulness scores alongside random controls, benign costs, and the measurement choices needed to interpret them.'''
 # Separate numeric macros from the adjacent word, preserving LaTeX spacing.
 for a,b in [('up to\\','up to \\'),('about\\','about \\'),('further\\','further \\'),('about9','about 9'),('and4','and 4')]:abstract=abstract.replace(a,b)
 s=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda m:'\\begin{abstract}\n'+abstract+'\n\\end{abstract}',s,flags=re.S);main.write_text(s)
 results=P/'sections/04_results.tex';s=results.read_text()
 marker='\\input{generated/pair500_completed_read}'
 if marker not in s:s=s.replace('\\subsection{The additional decline accompanies more refusals}',marker+'\n\n\\subsection{The additional decline accompanies more refusals}')
 results.write_text(s)
 intro=P/'sections/01_introduction.tex';s=intro.read_text();needle='A post-hoc decomposition associates most of this additional decrease with added refusals.'
 line='On a new fixed rule-scored PAIR-style prompt set, the additional decrease is about \\pairExtraWG{}--\\pairExtraHB{} points on the harmfulness-applicable strata, with the same direction under both judges. '
 if line not in s:s=s.replace(needle,line+needle)
 intro.write_text(s)
 limits=P/'sections/06_limitations.tex';s=limits.read_text()
 old='There is no trained Qwen steering vector, and the fixed-prompt PAIR-style campaign is running and its final two-judge evaluation is not yet complete. WildJailbreak supplies a different attack family but does not substitute for that missing test.'
 new='There is no trained Qwen steering vector. The completed PAIR-style campaign provides a new fixed prompt set, with all 500 source rows retained, but most behaviors have historical training or selection exposure. The 228 untouched rows are reported separately by functional stratum; they do not turn the full sample into a behavior-independent test. Attacks were optimized against the undefended Llama model rather than each defense.'
 assert old in s or new in s;s=s.replace(old,new)
 old='Cross-layer results differ both in usable search effort and in evaluation metric (MinHash for copyright). Copyright does not support an abstract effectiveness claim. Search settings are unchanged; post-search diagnostics have not been run.'
 new='The final search diagnostics retain this imbalance: 96/100 copyright rows and 5/400 other rows have fewer than 40 usable candidates. Cross-layer results differ both in usable search effort and in evaluation metric (MinHash for copyright). Copyright does not support an abstract effectiveness claim. Search settings were unchanged; post-search diagnostics were read after the main comparisons.'
 assert old in s or new in s;s=s.replace(old,new)
 extra='''\n\\paragraph{Missing labels and model ports.}
PAIR-style WildGuard scoring retains field-specific INVALID rows rather than treating them as safe. The pooled nine-unit complete-case comparison uses 397 of 400 harmfulness-applicable rows; the full-denominator identification bounds are reported separately. Complete-case intervals do not cover uncertainty about why labels are missing. Crossing WildGuard's 4096-token sliding window is logged and is not itself proof of invalidity. For pending model ports, the native donor-target gate and subsequent Llama-target-transfer amendment were decided after the Qwen baseline was known. The original failed gate is preserved. No pending port or target-transfer result is counted as a completed model replication.\n'''
 if '\\paragraph{Missing labels and model ports.}'not in s:s+=extra
 limits.write_text(s)
 # Source QA only: no local TeX engine is available, so never claim a built PDF.
 missing=[];labels=[];refs=[];texfiles=[]
 for p in P.rglob('*.tex'):
  if 'build'in p.parts:continue
  texfiles.append(p);text=p.read_text()
  for f in re.findall(r'\\input\{([^}]+)\}',text):
   if not(P/(f+'.tex')).exists():missing.append((str(p.relative_to(P)),f))
  labels+=re.findall(r'\\label\{([^}]+)\}',text);refs+=re.findall(r'\\(?:ref|pageref)\{([^}]+)\}',text)
 duplicate=sorted({v for v in labels if labels.count(v)>1});unresolved=sorted(set(refs)-set(labels))
 assert not missing and not duplicate and not unresolved,(missing,duplicate,unresolved)
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (O/'manuscript_update.json').write_text(json.dumps({'utc':now,'source_read_receipts':{f'{i:02d}':sha(D/f'{i:02d}.json')for i in range(1,9)},'modified_files':{str(p.relative_to(R)):sha(p)for p in [main,results,intro,limits,numbers]},'tex_inputs_checked':len(texfiles),'missing_inputs':missing,'duplicate_labels':duplicate,'unresolved_refs':unresolved,'PDF_rebuilt':False,'abstract_differences':'all harmfulness contrasts learned-minus-random; benign costs also learned-minus-random; paired-model judgments uncalibrated','new_model_vectors_counted':False},indent=2)+'\n')
 for name in ['PREREG_LOG.txt','OPS_LOG.txt']:
  with(R/'docs'/name).open('a')as f:f.write(f'{now} PAIR254_EIGHT_STEPS_COMPLETE report_SHA={sha(R/"docs/289_PAIR500_COMPLETED_ORDERED_READ.md")} manuscript_update_SHA={sha(O/"manuscript_update.json")} source_QA_pass; no_PDF_engine; fixed_sequences_unchanged; Qwen_transfer_not_trained.\n')
 print(json.dumps({'utc':now,'update_sha256':sha(O/'manuscript_update.json'),'abstract_tex_wordlike_tokens':len(abstract.split()),'source_QA':'PASS','PDF_rebuilt':False}))
if __name__=='__main__':main()
