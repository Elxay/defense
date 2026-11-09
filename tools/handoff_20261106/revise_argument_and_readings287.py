"""Revise prose from already-read CSVs; keep PAIR effect files unopened."""
from pathlib import Path
import csv, datetime, hashlib, json, math, re
R=Path('/data/HZX/Def');P=R/'paper';O=R/'results/audit/crossmodel287'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(name):return list(csv.DictReader((P/'data'/name).open()))
def main():
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 z=rows('zero_line.csv');base=next(x for x in z if x['group']=='Baseline');r0=100*int(base['harmful'])/int(base['n'])
 sampled=[x for x in z if x['group']in ['Gaussian','Init-only']];assert len(sampled)==11
 maximum=max(r0-100*int(x['harmful'])/int(x['n'])for x in sampled)
 unit=rows('wjb_official_units.csv');nine=rows('wjb_official_nine.csv');cost=rows('benefit_cost_posthoc.csv')
 all_effects=[float(x['difference_pp'])for x in nine if x['stratum']=='all'];assert len(all_effects)==2
 harms={x['condition']:x for x in unit};hb_random=[float(harms['rand'+str(i)]['HB_change_vs_alpha0_complete_pair_pp'])for i in range(4)]
 wg_random=[float(harms['rand'+str(i)]['WG_change_vs_alpha0_complete_pair_pp'])for i in range(4)]
 bycost={x['prompt_set']:x for x in cost};wrapped=bycost['wildjailbreak_benign'];xsafe=bycost['xstest_safe'];orb=bycost['or_hard']
 checked={'utc':now,'source_sha256':{n:sha(P/'data'/n)for n in ['zero_line.csv','wjb_official_units.csv','wjb_official_nine.csv','benefit_cost_posthoc.csv']},
   'val_random_maximum_drop_pp':maximum,'WJB_additional_drop_pp':sorted(abs(x)for x in all_effects),
   'WJB_random_drop_range_pp':[min(-x for x in hb_random+wg_random),max(-x for x in hb_random+wg_random)],
   'public_learned_minus_alpha0_pp':{'wrapped':float(wrapped['learned_minus_alpha0_pp']),'OR':float(orb['learned_minus_alpha0_pp']),'Xsafe':float(xsafe['learned_minus_alpha0_pp'])},
   'public_learned_minus_random_pp':{'wrapped':float(wrapped['learned_minus_random_pp']),'OR':float(orb['learned_minus_random_pp']),'Xsafe':float(xsafe['learned_minus_random_pp'])},
   'PAIR_outcome_reads':False,'refusal_decomposition':'post-hoc association, not causal attribution'}
 (O/'argument_numeric_receipt.json').write_text(json.dumps(checked,indent=2)+'\n')
 macros='\n'.join([r'\newcommand{\valRandomMaxDrop}{'+str(round(maximum))+'}',r'\newcommand{\wjbRandomMinDrop}{'+str(round(checked['WJB_random_drop_range_pp'][0]))+'}',r'\newcommand{\wjbRandomMaxDrop}{'+str(math.ceil(checked['WJB_random_drop_range_pp'][1]))+'}',r'\newcommand{\wjbExtraMinDrop}{'+str(round(min(abs(x)for x in all_effects)))+'}',r'\newcommand{\wjbExtraMaxDrop}{'+str(round(max(abs(x)for x in all_effects)))+'}',r'\newcommand{\wrappedBaselineCost}{'+str(round(float(wrapped['learned_minus_alpha0_pp'])))+'}',r'\newcommand{\xsafeBaselineCost}{'+f"{float(xsafe['learned_minus_alpha0_pp']):.1f}"+'}'])+'\n'
 (P/'generated/argument_numbers.tex').write_text(macros)
 intro=r'''\section{Introduction}
\label{sec:introduction}
Activation steering is often proposed as a lightweight way to alter refusal behavior: a vector is added to the residual stream, and safety is assessed through the resulting automated attack success rate (ASR) \citep{cao2024bipo,arditi2024refusal}. A lower ASR alone does not establish a better defense. In our own pipeline, verdicts depend on output truncation and the behavior text supplied to the judge, while decoding paths and retraining variation also change measured outcomes. Without a benign control, additional refusals can look like a safety improvement. We ask how much of a learned vector's ASR reduction survives two controls: norm-matched random vectors and benign requests carrying comparable adversarial packaging.

We study one learned vector added once at the final prompt token of Llama-3.1-8B-Instruct. On a success-filtered prompt set, norm-matched random vectors already lower judged ASR by up to \valRandomMaxDrop{} percentage points; on the official WildJailbreak evaluation, their decreases are about \wjbRandomMinDrop{}--\wjbRandomMaxDrop{} points. Learned vectors lower ASR a further \wjbExtraMinDrop{}--\wjbExtraMaxDrop{} points relative to those random directions under our two model judges. A post-hoc decomposition associates most of this additional decrease with added refusals. Relative to the unmodified model, benign refusal rises by about \wrappedBaselineCost{} points on wrapped WildJailbreak requests, versus \xsafeBaselineCost{} points on XSTest safe, where the interval includes zero. Paired original--wrapper tests reproduce a wrapper-associated refusal gap. These observations motivate reporting a harmfulness score together with its random reference, benign cost, and measurement protocol.

The scope is this single-position, prefill-only additive intervention. The historical selection set is distinguished from subsequent fixed-prompt evaluations, and rows with prior training or selection exposure remain marked rather than removed. Qwen2.5-7B-Instruct currently supplies supplementary zero-training baselines; model ports without completed evaluations do not increase the model count in our claims. We make three contributions:
\begin{itemize}
\item \textbf{Controls.} Norm-matched random vectors account for up to \valRandomMaxDrop{} judged-ASR points on success-filtered prompts but at most about \wjbRandomMaxDrop{} on the official WildJailbreak evaluation. Learned vectors exceed that sampled reference by \wjbExtraMinDrop{}--\wjbExtraMaxDrop{} points there under both judges.
\item \textbf{Costs.} We pair the harmfulness score with public and wrapper-paired benign refusal tests. In a post-hoc decomposition, most of the additional ASR decrease accompanies added refusals, and benign costs are concentrated on wrapped requests in the paired tests.
\item \textbf{Measurement.} We measure how truncation, baseline-set mismatch, decoding path, refusal rules, and retraining variation shift reported quantities in our own pipeline, and distill a reporting checklist.
\end{itemize}
'''
 (P/'sections/01_introduction.tex').write_text(intro)
 results=(P/'sections/04_results.tex').read_text();start=results.index('\\subsection{Evaluation choices move the reported quantities}');end=results.index('\\subsection{Positioning zero-training baselines}')
 results=results[:start]+results[end:];(P/'sections/04_results.tex').write_text(results)
 old=P/'sections/05_traps.tex';appendix=P/'sections/appendix_pitfalls.tex';assert not appendix.exists()
 appendix.write_text(old.read_text().replace('\\section{Evaluation Pitfalls}','\\section{Detailed measurement audit}',1).replace('\\label{sec:pitfalls}','\\label{app:pitfalls}',1))
 table=r'''\begin{table*}[t]
\small
\centering
\begin{tabular}{p{0.17\textwidth}p{0.24\textwidth}p{0.24\textwidth}p{0.26\textwidth}}
\toprule
Trigger & Observed impact & How found & Reporting safeguard \\
\midrule
Reference behavior changes & Top-1 vs. top-2: 49.65 vs. 15.20\% baseline harmfulness; 36.65\% labels flip & Rejudge identical outputs with alternate and random behavior references & Qualify mapped absolute rates; report paired effects under two judges \\
Baseline membership/path mismatch & 1--2 additions on 388 legal rows; HF baseline 63/70 vs. old vLLM 62/70 with one INVALID & Item-matched alternative baselines and backend audit & Name both baseline files, backends, and invalid fields \\
Batch vs. single decoding & 36/80 text differences, but 0/80 v2-label changes on 20 fixed prompts under four vectors & Same-prompt replays; zero-vector control & Preserve path and batch composition; cluster repeated prompts \\
Repeated training & 3--5 label changes on 70 prompts between highly similar vectors & Same-code, same-initialization reruns & Report repeated runs; do not interpret a single seed ranking as stable \\
Reading scope and refusal rules & 6/12 selected rule positives confirmed by full model review & Preview/full-text and category audit & Preserve reading scope and uncertainty; do not call model self-agreement human calibration \\
Filter threshold ties & 4/70 remaining harmful labels depend on $>$ vs. $\geq$ at 0.5 & Exact probability-boundary comparison & State input, scoring position, comparator, and tie counts \\
\bottomrule
\end{tabular}
\caption{Measurement audit in our own pipeline. Selected-sample counts do not estimate population error rates. Detailed checks and provenance appear in Appendix~\ref{app:pitfalls}.}
\label{tab:measurement-checklist}
\end{table*}
'''
 (P/'tables/measurement_checklist.tex').write_text(table)
 old.write_text(r'''\section{Measurement audit and reporting checklist}
\label{sec:pitfalls}
Table~\ref{tab:measurement-checklist} summarizes failures and checks in our own pipeline. Some shifts are comparable to the small contrasts being tested; judge-reference differences are substantially larger. These are distinct sources of uncertainty, not corrections that can be combined into one calibrated ASR.
\input{tables/measurement_checklist}

\paragraph{The evaluator and its input are part of the outcome.} On the same official WildJailbreak baseline outputs, mapped HarmBench gives 49.65\% harmfulness with the top-1 behavior reference and15.20\% with top-2; random mismatches give1.0\% on200 rows. Top-1/top-2 labels flip on36.65\% of rows. These figures show sensitivity to the reference, not mapping error rates. WildGuard gives38.8--38.85\%, with cross-judge $\kappa\approx0.51$. The unvalidated behavior mapping and WildGuard's same-source training prevent treating either absolute rate as ground truth. We report their paired differences together; agreement between them is a robustness check, not human calibration.

\paragraph{A matched implementation remains a condition of comparison.} Replaying the original batch composition reproduces20/20 zero-vector outputs byte for byte. Batch-versus-single decoding nevertheless differs on12/20 zero-vector texts and36/80 nonzero-vector texts. The same fixed20 prompts underlie all comparisons, and v2 refusal labels do not change in this sample. The prompt-level exact upper bound for any label disagreement is16.84\%; neither a population guarantee nor path equivalence follows. Public and historical legal comparisons retain their matched batch-8 baseline, while harmful-side outputs use the single-row path.

\paragraph{Near-identical vectors need not preserve item labels.} Four seed3 observations give harmful counts19,16,15,18 on70 prompts: one historical frozen vector and three reruns. Between two modern same-pipeline runs,3 labels change; reconstruction versus the frozen vector changes5. The descriptive ASR standard deviations are2.61pp within this set and3.64pp across the old eight seeds, too little evidence to partition training and seed variance. The five reconstruction-flip outputs exceed700 tokens, with the earliest retokenized divergence at token11. A single-run ranking or small item-discordance difference should therefore be interpreted against repeated-training variation.

\paragraph{Refusal measurement needs a scope and a contrast.} Full model review confirms6 of12 selected Qwen candidate rule additions, with condition counts5/5,1/3 and0/4. This selected sample is evidence of condition-dependent agreement, not calibrated precision for every condition. Truncated replies, knowledge nonanswers, apologies, and refusals with alternatives must stay distinguishable. Model annotations, including GPT review, remain without human calibration. We report new refusals against the matched alpha-zero baseline separately from learned-minus-random differences. The full truncation, language, classifier-position, interpolation, metadata and restart audits remain in Appendix~\ref{app:pitfalls}.
''')
 related=r'''\section{Related Work}
\paragraph{Learned representation interventions.} ReFT defines interventions through an edit function, token positions and a layer; LoReFT learns a representation-dependent low-rank edit while freezing model weights \citep{wu2024reft}. Our setup instead learns one constant vector at one prompt position (Section~\ref{sec:setup}). Its parameter-efficiency results on other tasks are not safety comparisons with our protocol. BiPO learns a fixed vector through bidirectional preference optimization and applies steering across token positions \citep{cao2024bipo}. Its safety study uses different training pairs, direction signs, attack prompts and judge. The ability to steer both toward and away from compliance motivates our random and benign controls, but does not contradict or numerically replicate our results.

\paragraph{Efficacy and preservation under distribution shifts.} \citet{goyal2026specificity} separate general capability preservation, related control behavior and robustness under shifts. Their over-refusal intervention aims to increase benign compliance, whereas ours is trained toward refusal. Their finding that improvements in one behavior can coexist with degraded robustness motivates reporting both harmful and benign outcomes (Section~\ref{sec:results}); it does not establish a common mechanism for our wrapper gap. \citet{arditi2024refusal} study a refusal direction in chat models, which provides context rather than a universal identity for our learned vector.

\paragraph{Random perturbations under a different protocol.} \citet{korznikov2026rogue} report increased harmful compliance under random fixed-vector steering (1--13\% in v2). They intervene across prompt and generated tokens; ours is a single final-prompt-token injection. Their initially refused requests and our success-filtered prompts also differ. The opposite movement of our judge score therefore concerns different protocols, rather than a failed numerical replication or evidence for a shared mechanism.

\paragraph{Judge reliability.} \citet{gao2026judge} compare model judges with human-majority labels on HarmBench validation pairs, test content-preserving framing changes, and separately attack a classifier. This bears on our measurement audit (Section~\ref{sec:pitfalls}), but their calibration is not used to correct our WildJailbreak rates. \citet{mu2026evaluators} compare six evaluators on two human-labeled corpora, one selected to exclude refusals, while controlling the backbone for applicable prompted judges. Their StrongReject variant is the rubric judge, not its released trained scorer. The finding that evaluator choice matters is consistent with our cross-judge analysis; their accuracy ranking need not transfer to our outputs, precision, or input protocol.

\paragraph{Attack and benign collections.} PAIR uses iterative black-box interactions \citep{chao2023pair}; our length-and-rule-scored search is described as PAIR-style rather than the original judge-scored algorithm. HarmBench \citep{mazeika2024harmbench} and JailbreakBench \citep{chao2024jbb} provide behavior collections. WildTeaming supplies WildJailbreak harmful and benign requests with adversarial packaging \citep{jiang2024wildteaming}. Our paired wrapper tests use that structure, with shared source behaviors and exposure marks retained. The closed data-composition experiment is incomplete and supplies no main-text intervention result.
'''
 (P/'sections/02_related_work.tex').write_text(related)
 lim=P/'sections/06_limitations.tex';text=lim.read_text();text=text.replace('The plain-data supplement has been expanded to five seeds, remains limited in precision, and is not content-matched.','The data-composition experiment and its plain-data supplement were closed incomplete and do not contribute a main-text intervention result. The supplement was not content-matched.')
 text=text.replace('A second seed3 control is queued for the full holdout to contextualize the 2-pp criterion; a single observed repeat cannot validate that criterion generally.','A proposed second seed3 holdout control does not supply a completed noise-floor estimate; a single observed repeat would not validate that criterion generally.')
 lim.write_text(text)
 ethics=r'''\section*{Ethical Considerations}
This study audits an existing intervention and the measurements used to assess it. Activation steering can also weaken safeguards, so both vectors and jailbreak material have dual-use potential. The manuscript repository contains scripts, aggregate counts, coded labels, row identifiers and hashes, but no raw attack prompts, harmful outputs, model weights or steering vectors. Examples are benign paraphrases or abbreviated descriptions. This release choice reduces direct misuse and limits fully public reproduction; provenance hashes and named public source collections support verification within those limits.

We use WildGuard under its Apache-2.0 model-card license and the accepted AI2 Responsible Use Guidelines associated with access. That does not confer rights to redistribute unrelated datasets or model weights. Dataset and model terms remain attached to their original sources. All refusal and harmfulness judgments in this study are model-generated without independent human calibration; agreement is not represented as expert or human verification. No human-subject annotation outcome is claimed for the pending review materials.
'''
 (P/'sections/07_ethics.tex').write_text(ethics)
 main=P/'main.tex';t=main.read_text();assert '\\input{generated/argument_numbers}'not in t;t=t.replace('\\maketitle','\\input{generated/argument_numbers}\n\\maketitle',1)
 t=t.replace('\\bibliography{references}','\\input{sections/07_ethics}\n\\bibliography{references}',1)
 t=t.replace('\\input{sections/appendix_support}','\\input{sections/appendix_support}\n\\input{sections/appendix_pitfalls}',1);main.write_text(t)
 # Keep every edited TeX file clean; no engine is installed, so this is source QA.
 for p in [main,*sorted((P/'sections').glob('*.tex')),P/'tables/measurement_checklist.tex',P/'generated/argument_numbers.tex']:
  p.write_text('\n'.join(l.rstrip()for l in p.read_text().splitlines()).rstrip()+'\n')
 visited=set();labels=[];inputs=[]
 def visit(path):
  if path in visited:return
  visited.add(path);s=path.read_text();labels.extend(re.findall(r'\\label\{([^}]+)\}',s))
  for n in re.findall(r'\\input\{([^}]+)\}',s):
   q=P/(n+'.tex');assert q.exists(),n;inputs.append(n);visit(q)
 visit(main);assert len(labels)==len(set(labels))
 cited=set()
 for p in visited:
  for z in re.findall(r'\\cite\w*\{([^}]+)\}',p.read_text()):cited.update(z.split(','))
 bib=(P/'references.bib').read_text();assert all(re.search(r'@\w+\{'+re.escape(k)+',',bib)for k in cited)
 (O/'manuscript_revision_receipt.json').write_text(json.dumps({'utc':now,'source_QA':'input paths, duplicate labels, citation keys','PDF_rebuilt':False,'PAIR_outcomes_read':False,'numeric_receipt_sha256':sha(O/'argument_numeric_receipt.json'),'files':{str(p.relative_to(R)):sha(p)for p in visited if 'tables'in p.parts or 'sections'in p.parts or p==main}},indent=2)+'\n')
 print(json.dumps({'utc':now,'intro_sha256':sha(P/'sections/01_introduction.tex'),'source_QA':'passed','PDF_rebuilt':False,'numeric_receipt_sha256':sha(O/'argument_numeric_receipt.json')}))
if __name__=='__main__':main()
