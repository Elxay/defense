"""Organize the existing manuscript by findings; preserve unread PAIR results."""
from pathlib import Path
import datetime,hashlib,json,re,shutil
R=Path('/data/HZX/Def');P=R/'paper';O=R/'results/audit/pair500/argument_revision_20261109'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    O.mkdir(exist_ok=True);before={str(p.relative_to(R)):sha(p)for p in [P/'main.tex',*sorted((P/'sections').glob('*.tex'))]}
    assert not(O/'before_sources.json').exists();(O/'before_sources.json').write_text(json.dumps(before,indent=2)+'\n')
    intro=r'''\section{Introduction}
\label{sec:introduction}
A lower automated attack success rate (ASR) does not by itself establish a better jailbreak defense. The same score can fall because an intervention resists harmful requests, because a perturbation disrupts responses, or because the evaluator reacts to changes in wording. For activation steering, a safety claim therefore needs two comparisons: learned directions against norm-matched random directions, and harmful requests against benign requests with comparable adversarial packaging.

Comparing a learned vector only with the unmodified model leaves the contribution of learning unresolved. Testing benign behavior only on unrelated prompts can also miss refusals associated with jailbreak-like packaging. Automated judgments introduce a further dependency: harmfulness, refusal, and task completion are different outcomes, and agreement with one classifier does not establish all three. Work on judge reliability motivates checking the evaluator as well as the intervention \citep{gao2026judge,mu2026evaluators}.

We audit one minimal intervention in Llama-3.1-8B-Instruct: a learned vector added once at the final prompt token during prefill. We compare it with norm-matched random directions, paired benign requests with and without adversarial wrappers, system prompts, and an output filter. We separate prompts selected for success against the target model from prompts not selected in that way, retain historical-use marks, and report harmfulness and benign refusal costs together. The audit concerns this injection protocol; Qwen2.5-7B-Instruct supplies only supplementary zero-training baselines.

The completed evaluations show why these comparisons change the interpretation of a lower ASR. Random directions account for a substantial decrease on success-filtered prompts, while learned vectors retain an additional advantage on the official WildJailbreak evaluation under both model judges. That advantage accompanies additional refusals and uneven benign costs. Paired wrapper tests and audits of our own pipeline help distinguish these observations without turning them into a mechanism claim. We make four contributions:
\begin{itemize}
\item \textbf{Random controls change the reference.} We measure the score changes produced by norm-matched random directions and the learned-vector difference beyond that reference, separating success-filtered attacks from the WildJailbreak evaluations.
\item \textbf{Safety scores and refusal costs are evaluated together.} We relate judge-score changes to refusal labels in a post-hoc decomposition, report public benign costs, and reproduce a wrapper-associated refusal gap on paired benign samples. These are descriptive findings, not evidence that the vector identifies a particular harmful intent or style mechanism.
\item \textbf{Measurement choices are part of the result.} We document how baseline membership, refusal rules, reading scope, truncation, decoding paths, and retraining variation change measurements in our own pipeline, and provide a reporting checklist.
\item \textbf{Zero-training alternatives remain explicit.} We evaluate system prompts and output filtering alongside steering, preserving their generation paths, thresholds, and model-annotation limits instead of inferring a calibrated ranking from ASR alone.
\end{itemize}
'''
    (P/'sections/01_introduction.tex').write_text(intro)
    old=(P/'sections/04_results.tex').read_text();a='\\subsection{Random references and learned residuals}';b='\\subsection{Benign wrappers and data composition}';c='\\subsection{Zero-training prompts and output filtering}';d='\\subsection{Official WildJailbreak evaluation: reference sensitivity}'
    assert all(old.count(z)==1 for z in [a,b,c,d]);random=old.split(a,1)[1].split(b,1)[0];benign=old.split(b,1)[1].split(c,1)[0];zero=old.split(c,1)[1].split(d,1)[0];official=old.split(d,1)[1]
    first,rest=random.split('\\input{tables/zero_line}',1);lmi,randomtail=rest.split('On the 300 attacks',1);randommain=first+'\nOn the 300 attacks'+randomtail
    c2,augmentation=benign.split('The augmentation setup used',1);public=(P/'generated/public_refusal_results.tex').read_text();assert public.startswith('\\subsection{Public benign refusal costs}');public=public.split('\n',1)[1];(P/'generated/public_refusal_body.tex').write_text(public)
    scope=(P/'generated/wjb_nine_scope.tex').read_text();contrast=scope.split('\\input{tables/wjb_exposure}',1)[0];exposure=scope.split('\\input{tables/wjb_exposure}',1)[1].split('The alternate-reference analysis',1)[0]
    conditional=exposure.split('Among WildGuard nonrefusals,',1)[1];exposure=exposure.split('Among WildGuard nonrefusals,',1)[0]
    (P/'generated/wjb_nine_contrast_view.tex').write_text(contrast)
    oldbaseline=official.split('\\input{tables/wjb_official_nine}',1)[0]
    results=r'''\section{Results}
\label{sec:results}
\subsection{Random controls change the interpretation of lower ASR}
'''+randommain+r'''
On the official WildJailbreak evaluation, the learned-minus-random comparison is retained under both judges. It is a conditional comparison of the sampled vectors, not a claim of a universally superior defense.
\input{tables/wjb_official_nine}
\input{generated/wjb_nine_contrast_view}

\subsection{The additional decline accompanies more refusals}
We distinguish harmfulness-judge flips from refusal labels. The completed post-hoc decomposition associates most of the additional score decline with increased refusal, while also finding changes among outputs not labelled as refusals. The unit-level harmfulness and refusal rates are shown together in Table~\ref{tab:wjb_official_units}. This association does not establish a causal mechanism, and rule recall can vary with response style.

Among WildGuard nonrefusals,'''+conditional+r'''
\subsection{Benign costs concentrate on wrapped requests}
\input{generated/public_refusal_body}
\input{generated/benefit_cost_posthoc}
The public collections have different constructions and are not content-matched. The paired original--wrapper tests below provide the more direct comparison of request packaging.
'''+c2+r'''
\subsection{Evaluation choices move the reported quantities}
The same outputs and interventions can receive different measurements when reference behaviors, baseline membership, refusal definitions, output scope, or decoding paths change. We distinguish large judge-dependent differences from smaller shifts that are comparable to some of the contrasts being tested; the detailed audit is in Section~\ref{sec:pitfalls}.
'''+oldbaseline+r'''
The magnitude of a paired judge difference, its uncertainty conditional on the vectors, and its sensitivity to the measurement path are separate reporting obligations. Similarity between retrained vectors does not imply identical decoded responses or stable item-level rankings.

\subsection{Positioning zero-training baselines}
'''+zero
    (P/'sections/04_results.tex').write_text(results)
    appendix=r'''\section{Initialization and residual decomposition}
\label{app:initialization}
The decomposition is supporting evidence for the scope of the learned intervention. It is not the central safety--utility claim.
\input{tables/zero_line}
'''+lmi+r'''
\section{Exposure strata and closed data-composition evaluation}
\input{tables/wjb_exposure}
'''+exposure+'\nThe augmentation setup used'+augmentation
    (P/'sections/appendix_support.tex').write_text(appendix)
    main=(P/'main.tex').read_text();title=re.search(r'\\title\{.*?\}\n\\author',main,re.S);assert title
    main=main[:title.start()]+r'\title{A Lower Attack Success Rate Is Not a Better Defense:\\Auditing One-Vector Prefill Steering for Jailbreak Robustness}'+'\n\\author'+main[title.end():]
    assert main.count('\\appendix')==1;main=main.replace('\\appendix','\\appendix\n\\input{sections/appendix_support}',1);(P/'main.tex').write_text(main)
    traps=(P/'sections/05_traps.tex').read_text();traps=traps.replace('\\section{Evaluation Pitfalls}','\\section{Evaluation Pitfalls}\n\\label{sec:pitfalls}',1);(P/'sections/05_traps.tex').write_text(traps)
    setup=(P/'sections/03_setup.tex').read_text();models=setup.split('\\paragraph{Models and intervention.}',1)[1].split('\\paragraph{Prompt samples.}',1)[0];prompts=setup.split('\\paragraph{Prompt samples.}',1)[1].split('\\paragraph{Outcomes.}',1)[0];outcomes=setup.split('\\paragraph{Outcomes.}',1)[1].split('\\paragraph{Statistical and chronological limits.}',1)[0];stats=setup.split('\\paragraph{Statistical and chronological limits.}',1)[1].split('\\paragraph{Exposure strata and shared sources.}',1)[0];exposure_setup=setup.split('\\paragraph{Exposure strata and shared sources.}',1)[1].split('\\paragraph{Official WildJailbreak primary model judge.}',1)[0];judge=setup.split('\\paragraph{Official WildJailbreak primary model judge.}',1)[1]
    setup='\\section{Experimental Setup}\n\\label{sec:setup}\n\\subsection{Models and intervention}\n'+models+'\n\\subsection{Prompt samples and historical use}\n'+prompts+'\n'+exposure_setup+'\n\\subsection{Outcomes and model judges}\n'+outcomes+'\n\\paragraph{Official WildJailbreak primary model judge.}'+judge+'\n\\subsection{Statistics and versioned decisions}\n'+stats
    (P/'sections/03_setup.tex').write_text(setup)
    generated=[]
    for p in [P/'main.tex',*sorted((P/'sections').glob('*.tex'))]:
        for line in p.read_text().splitlines():
            if re.match(r'\\(?:sub)*section\{',line):generated.append({'file':str(p.relative_to(R)),'heading':line})
    missing=[]
    visited=set();labels=[]
    def visit(p):
        if p in visited:return
        visited.add(p);t=p.read_text();labels.extend(re.findall(r'\\label\{([^}]+)\}',t))
        for name in re.findall(r'\\input\{([^}]+)\}',t):
            q=P/(name+'.tex')
            if not q.exists():missing.append(str(q))
            else:visit(q)
    visit(P/'main.tex');assert not missing,missing;duplicates=sorted({z for z in labels if labels.count(z)>1});assert not duplicates,duplicates
    # Validate the new table reference against the actual generated table label.
    actual=re.findall(r'\\label\{([^}]+)\}',(P/'tables/wjb_official_units.tex').read_text());assert len(actual)==1
    text=(P/'sections/04_results.tex').read_text().replace('tab:wjb_official_units',actual[0]);(P/'sections/04_results.tex').write_text(text)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();result={'utc':now,'before_sha256':before,'after_sha256':{str(p.relative_to(R)):sha(p)for p in visited},'missing_inputs':missing,'duplicate_labels':duplicates,'PAIR_outcomes_read':False,'abstract_text_unchanged':True,'abstract_placeholder_template_use':'superseded by user narrative direction; do not fill docs284','new_result_numbers_added':False,'directory':generated,'latex_engine':next((shutil.which(n)for n in ['latexmk','pdflatex','tectonic']if shutil.which(n)),None)};(O/'manuscript_revision.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'utc':now,'missing_inputs':missing,'duplicate_labels':duplicates,'latex_engine':result['latex_engine'],'PAIR_outcomes_read':False,'intro_first_paragraph':intro.split('\n\n')[0],'contributions':intro.split('\\begin{itemize}',1)[1].split('\\end{itemize}',1)[0]}))
if __name__=='__main__':main()
