"""Publish manuscript structure and metadata audits, excluding all new outcomes."""
from pathlib import Path
import datetime,fcntl,hashlib,json,re,shutil,subprocess
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';P=R/'paper';O=B/'argument_revision_20261109';G=R/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();intro=(P/'sections/01_introduction.tex').read_text();first=intro.split('\n\n')[0].split('\\label{sec:introduction}\n',1)[1];items=intro.split('\\begin{itemize}',1)[1].split('\\end{itemize}',1)[0]
    mditems=[]
    for z in items.split('\\item')[1:]:mditems.append('- '+re.sub(r'\\textbf\{([^}]+)\}',r'**\1**',z.strip()))
    outline='''1. Introduction
2. Related Work
3. Experimental Setup
   3.1 Models and intervention
   3.2 Prompt samples and historical use
   3.3 Outcomes and model judges
   3.4 Statistics and versioned decisions
4. Results
   4.1 Random controls change the interpretation of lower ASR
   4.2 The additional decline accompanies more refusals
   4.3 Benign costs concentrate on wrapped requests
   4.4 Evaluation choices move the reported quantities
   4.5 Positioning zero-training baselines
5. Evaluation Pitfalls
   5.1 Baseline membership and backend alignment
   5.2 Reading scope, nonanswers, and truncation
   5.3 Judge flips and refusal labels
   5.4 Classifier position and threshold convention
   5.5 Interpolation and unsupported draws
   5.6 Training repeat variation and decoding amplification
   5.7 Missing generation metadata
   5.8 Restart provenance
6. Limitations
References
Appendix A. Initialization and residual decomposition
Appendix B. Exposure strata and closed data-composition evaluation
Appendix C. Provenance and protocol chronology
Appendix D. Auxiliary frontier sensitivity
'''
    doc=R/'docs/286_ARGUMENT_AND_MANUSCRIPT_STRUCTURE.md';doc.write_text(f'''# Argument-first manuscript revision

UTC {now}. User-requested editorial change after the completed WJB/public reads, with PAIR outcomes still unread. The central argument is that a lower judged ASR alone does not establish a better defense; random controls and wrapper-paired benign tests change its interpretation. This is a claim about this audited protocol, not a universal mechanism result.

The placeholder-heavy docs284 abstract template is historical and is no longer to be filled. Main.tex retains its interim method-only abstract; the narrative abstract is written last after the locked PAIR read, using a few checked numeric findings and the contrast definitions from the result tables. No new abstract result sentence or PAIR number was inserted. The prose candidates21, about5,19--23 and public9/6/0 are independently recomputed in prose_numeric_candidates_check.json. The public9/6/0 contrast is learned-minus-alpha0, whereas the harmful additional19--23 is learned-minus-random; OR's learned-minus-random value is3.95 rather than5.88. Small uncertain XSTest change is not equivalence. Refusal decomposition is post-hoc and descriptive.

## Current introduction opening

{first}

## Contributions

{chr(10).join(mditems)}

## Actual manuscript directory

```text
{outline}```

The introduction now has four paragraphs followed by its contribution list. The result chapter is ordered by findings, with the initialization decomposition and incomplete data-composition experiment moved to appendices. Existing numerical statements/tables are preserved, with the primary scope and caveats retained. The editor checked input-file existence and duplicate labels; no TeX engine is installed in the environment, so no rebuilt PDF is claimed.

The supplied judge-reliability example was checked against the primary arXiv abstract/metadata: https://arxiv.org/abs/2606.25487 (v2). It is used here as an organizational reference, without adding unverified full-text numerical claims to the manuscript.

## Operational clarifications retained

The original1144 contextual input audit is88 prompts x13 conditions, not all1300. Addendum12 records the full1300 audit, overflow fallback and all13 admission. The old midpoint +/-200 indices imply400 shared tokens; the frozen contingency and CPU tests make that explicit. Current PAIR numeric sources are not hot-edited and no chunked GPU inference is claimed.

The render audit verifies4000/4000 old input hashes against current Llama rendering: the knowledge/date header stays, and the custom system body follows it. This is not Qwen's four replace/append conditions. Public batch8/120token and harmful single-row/2400token A/B rates remain separate. Original227 prompt bodies are unchanged; effective system/header hashes are in the companion addendum.

Today's18:00 GPU0 cutoff is superseded by the user's later authorization, addendum13. Old release plans are historical; current authorization runs through today's24:00 JST. Existing processes and admission gates remain protected.
''')
    render=json.loads((O/'llama_system_header_audit.json').read_text());rdoc=R/'docs/227_LLAMA_RENDERING_ADDENDUM.md';rdoc.write_text(f'''# Llama system rendering clarification

UTC {now}. Original docs227_SYSTEM_PROMPTS.txt is unchanged. The custom A/B body follows the tokenizer's default knowledge/date header, inside the same system segment. It does not replace that header, and it is not an additional system role appended after a separately rendered default system message. The user segment is unchanged. All4000 input-ID hashes match the original2000x2 rendering audit.

Header SHA256: {render['header_sha256'][0]}
A effective system-segment SHA256: {render['effective_system_segment_sha256']['SYS_A'][0]}
B effective system-segment SHA256: {render['effective_system_segment_sha256']['SYS_B'][0]}
A body SHA256: {render['custom_body_sha256']['SYS_A']}
B body SHA256: {render['custom_body_sha256']['SYS_B']}

Public A/B uses the matched batch8/120token path; harmful A/B uses the single-row/2400token path. Do not pool them into a single refusal rate. Hook-count versus nonzero-injection fields retain their documented meanings. Render audit SHA256 {sha(O/'llama_system_header_audit.json')}.
''')
    log=f'{now} ARGUMENT_FIRST_MANUSCRIPT_REVISION doc_SHA={sha(doc)} intro_SHA={sha(P/"sections/01_introduction.tex")} results_SHA={sha(P/"sections/04_results.tex")} historical abstract-placeholder template superseded; narrative abstract last afterPAIR; no PAIR outcome read/no rebuiltPDF. Render_addendum_SHA={sha(rdoc)}.\n'
    for n in ['PREREG_LOG.txt','OPS_LOG.txt']:
        with(R/'docs'/n).open('a')as f:f.write(log)
    files=[str(doc.relative_to(R)),str(rdoc.relative_to(R)),'docs/PREREG_LOG.txt','docs/OPS_LOG.txt','paper/main.tex',*['paper/sections/'+n for n in ['01_introduction.tex','03_setup.tex','04_results.tex','05_traps.tex','appendix_support.tex']],*['paper/generated/'+n for n in ['public_refusal_body.tex','wjb_nine_contrast_view.tex']],*['tools/handoff_20261106/'+n for n in ['reframe_paper_argument.py','audit_llama_system_header_and_eta.py','observe_contextual_all1300.py','publish_argument_revision.py','handoff_lease_priority_v3.py']]]
    files +=[str(p.relative_to(R))for p in O.glob('*.json')if'.private.'not in p.name]
    files+=['results/audit/pair500/lease_priority/v3_handoff_complete.json']
    for n in files:assert not re.search(r'hf_[A-Za-z0-9]{20,}',(R/n).read_text())
    with(R/'logs/prereg_publish.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        pending=subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True)
        allowed=set(files)|{'manifests_argument_revision_20261109.json'}
        assert all(l[3:]in allowed for l in pending.splitlines()),'Unrelated working-tree changes; do not overwrite'
        for n in files:p=G/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
        m='manifests_argument_revision_20261109.json';(G/m).write_text(json.dumps({'utc':now,'files':{n:sha(G/n)for n in files},'PAIR_outcomes_read':False,'raw_attack_text_or_outputs_added':False,'PDF_rebuilt':False},indent=2)+'\n')
        subprocess.run(['git','add',*files,m],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Reframe manuscript around controls, refusal costs and measurement choices'],cwd=G,check=True);commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip();subprocess.run(['git','push','origin','main'],cwd=G,check=True)
    print(json.dumps({'utc':now,'commit':commit,'argument_doc_sha256':sha(doc),'intro_sha256':sha(P/'sections/01_introduction.tex'),'render_addendum_sha256':sha(rdoc),'full1300_observer_source_sha256':sha(R/'tools/handoff_20261106/observe_contextual_all1300.py')}))
if __name__=='__main__':main()
