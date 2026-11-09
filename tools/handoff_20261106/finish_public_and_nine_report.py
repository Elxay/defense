"""Export already-read numeric artifacts and update bounded manuscript text."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT=Path('/data/HZX/Def'); BASE=ROOT/'results/audit/pair500'; NINE=BASE/'nine_read_20261109'; PUBLIC=BASE/'public_read_20261109'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def rate(v):return f'{v[0]:.2f}' if v[0]==v[1] else f'{v[0]:.2f}--{v[1]:.2f}'

def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    data=load(NINE/'supplemental_tables.json'); main=load(NINE/'03_main_contrast.json')['result']
    tables=ROOT/'paper/tables'; generated=ROOT/'paper/generated'
    rows=[r'\begin{table*}[t]',r'\centering\small',r'\begin{tabular}{lrrrrr}',r'\toprule',r'Condition & HB harmful (\%) & WG harmful (\%) & WG refusal (\%) & v2 refusal (\%) & WG harmful among WG nonrefusals (\%) \\',r'\midrule']
    nonref={x['condition']:x for x in data['WG_nonrefusal_harmful']}
    for x in data['unit_table']:
        name=x['condition'].replace('old_','').replace('_',r'\_')
        rows.append(f'{name} & {x["HB_harmful_pct"]:.2f} & {rate(x["WG_harmful_bounds_pct"])} & {rate(x["WG_refusal_bounds_pct"])} & {x["v2_refusal_pct"]:.2f} & {rate(nonref[x["condition"]]["rate_bounds_pct"])} '+r'\\')
    rows += [r'\bottomrule',r'\end{tabular}',r'\caption{WildJailbreak official harmful evaluation, all 2000 rows. Ranges retain INVALID fields as all-row identification bounds, rather than defaulting to harmless or dropping rows. HB uses mapped top-1 references; its absolute rate is descriptive. WG nonrefusal harmfulness is an explicitly post-hoc joint-label intersection. Source hashes are in the manuscript provenance manifest.}',r'\label{tab:wjb-unit-rates}',r'\end{table*}']
    (tables/'wjb_official_units.tex').write_text('\n'.join(rows)+'\n')
    rows=[r'\begin{table*}[t]',r'\centering\small',r'\begin{tabular}{lrrrrr}',r'\toprule',r'Mapped exposure layer & Rows & Behavior groups & HB difference (pp) & WG difference (pp) & WG complete pairs \\',r'\midrule']
    for key,x in data['exposure'].items():
        h=x['judges']['HB_top1'];w=x['judges']['WildGuard'];name=key.replace('_',r'\_')
        rows.append(f'{name} & {x["n"]} & {h["behavior_count"]} & {h["conditional_complete_pair_mean_pp"]:+.2f} & {w["conditional_complete_pair_mean_pp"]:+.2f} & {w["complete_pair_rows"]} '+r'\\')
    rows += [r'\bottomrule',r'\end{tabular}',r'\caption{Five learned minus four random directions by unvalidated mapped exposure. All rows remain in the dataset; complete-pair counts and all-row bounds are separate. The fit12 layer has only three mapped behavior groups and cannot establish generalization or a reliable population interval. Full interval and bound tables are in the numeric source.}',r'\label{tab:wjb-exposure}',r'\end{table*}']
    (tables/'wjb_exposure.tex').write_text('\n'.join(rows)+'\n')
    h=main['HB_top1']['conditional_complete_pair_mean_pp'];w=main['WildGuard']['conditional_complete_pair_mean_pp']
    narrative=(r'\paragraph{Paired differences and their scope.}'+'\n'+
        f'On these 2000 official WildJailbreak adversarial harmful prompts, five learned vectors minus four norm-matched random directions give {h:+.2f} pp under mapped HarmBench and {w:+.2f} pp under WildGuard, at fixed $\\alpha=1.0$ in Llama-3.1-8B-Instruct. '+
        'Both judges and both mapping-confidence strata have negative differences under the frozen cross-judge rule. Intervals condition on these nine vectors. The exact 126-allocation statistic describes unit separation under an exchangeability assumption; its minimum attainable probability does not measure effect size or make the five seeds and four generated directions independent population samples.\n\n'+
        'Mapped HarmBench absolute rates are descriptive: changing top-1 to top-2 behavior references flips 36.65\\% of baseline decisions, and a random mismatched reference yields 1.0\\% harmful labels on its 200-row control. WildGuard was trained on data sharing the WildJailbreak source, making this an in-distribution evaluation for that judge. The official prompts were filtered against weak models. Neither judge is human-calibrated; their baseline harmfulness agreement has $\\kappa\\approx0.51$. The steering strength was not selected on this set, but fit12 training attacks derive from JBB behaviors that may overlap source behaviors here. The exposure layers use an unvalidated behavior mapping.\n\n'+
        r'\input{tables/wjb_official_units}'+'\n'+r'\input{tables/wjb_exposure}'+'\n'+
        'The mapped marked and unmarked layers both retain negative differences. Only three assigned behavior groups occur in the fit12 layer, so this descriptive breakdown cannot determine behavior-level out-of-training generalization. Among WildGuard nonrefusals, learned-vector harmfulness is lower than for the sampled random directions, but this post-hoc conditional decomposition does not identify a mechanism. It uses direct harmfulness/nonrefusal intersections and separately records invalid labels.\n\n'+
        'The alternate-reference analysis is supplementary sensitivity, not the cross-judge claim gate. Its already-read four-unit comparison is $-7.90$ pp. The remaining five conditions are queued in the first PAIR-500 HarmBench window after its fresh twenty-item numerical check; pending top-2 results do not delay the completed primary read.\n')
    (generated/'wjb_nine_scope.tex').write_text(narrative)
    p=ROOT/'paper/sections/04_results.tex';text=p.read_text()
    text=text.replace('Learned-versus-random paired comparisons are exploratory and await their prospectively specified alternate-reference sensitivity before any abstract claim.','Learned-versus-random paired comparisons are reported under the completed cross-judge and confidence-stratum rule; alternate-reference scoring is a separate sensitivity analysis.')
    marker='\\input{generated/wjb_nine_scope}'
    if marker not in text:text=text.replace('\\input{tables/wjb_official_nine}','\\input{tables/wjb_official_nine}\n'+marker)
    p.write_text(text)
    p=ROOT/'paper/sections/05_traps.tex';text=p.read_text().replace('Unit-level robustness remains unread until all nine units complete.','The nine-unit primary read is complete under both judges; alternate-reference scoring remains a separately labeled sensitivity analysis.')
    if '\\paragraph{Success selection and conditional refusal readings.}' not in text:
        text+='\n\\paragraph{Success selection and conditional refusal readings.}\nOn the historical success-selected 70-prompt set, norm-matched perturbation references lower HF judge ASR by 4--21 pp. On the official 2000-row WildJailbreak evaluation, the four random directions lower mapped-HarmBench harmfulness by 1.6--4.5 pp. These descriptive cross-set differences are compatible with amplification from different baseline harmfulness rates and success selection; they do not test that explanation. The baseline and random-direction nonrefusal harmfulness proportions are close under WildGuard, while learned-vector proportions are somewhat lower. Conditioning on refusal, itself changed by the intervention, does not identify a causal decomposition.\n'
    if '\\paragraph{Raw prompt versus classifier input length.}' not in text:
        text+='\n\\paragraph{Raw prompt versus classifier input length.}\nINVALID reply-harmfulness fields for IDs918 and2193 under rand0 and2109 under rand3 have raw WildGuard prompt lengths118,77 and159, but full formatted prompt-plus-response lengths4192,4467 and4305 tokens. The historical description of baseline ID701 as a4817-token prompt was incorrect: its raw prompt is138 tokens and4817 describes the full formatted input. The4096 sliding-window setting is not a hard context cap. These observations neither establish a length-caused parsing failure nor justify silently truncating inputs or recoding INVALID as harmless.\n'
    p.write_text(text)
    p=ROOT/'paper/sections/06_limitations.tex';text=p.read_text().replace('an independent PAIR test campaign was not run.','the fixed-prompt PAIR-style campaign is running and its final two-judge evaluation is not yet complete.').replace('The zero-restart count concerns the PAIR recovery watchdog only; it does not erase the undocumented third-arm seed3 restart.','The earlier zero-restart snapshot concerned the PAIR recovery watchdog at that time; a later recorded OOM restart and the undocumented third-arm seed3 restart are distinct events.')
    if '\\paragraph{Official evaluation and public refusal costs.}' not in text:
        text+='\n\\paragraph{Official evaluation and public refusal costs.}\nThe official WildJailbreak prompts were selected for success against at least one weak model, and source behaviors can overlap historical training or selection. HarmBench requires an unvalidated nearest-neighbor behavior mapping, whereas WildGuard shares the WildJailbreak training source; neither provides human ground truth. Public refusal comparisons use a matched batch-8 path and120-token replies, while harmful-side generation is single-row with2400-token replies. Refusal-style and truncation effects can change both regular-expression and model labels. The six fixed30-pair model samples contain no clear refusal misses but retain uncertain outputs; the benign WildJailbreak random sample fails the conservative line with five uncertain items. They therefore do not validate absolute recall.\n'
    p.write_text(text)
    # Preserve the prior export and derive caption counts from its numeric source.
    p=tables/'public_refusal_nine.tex';text=p.read_text();wg=load(PUBLIC/'06_sensitivity.json')['result']['wildjailbreak_benign']['all']['rules']['WG']
    old='WildGuard has204 complete nine-unit pairs on the210-row benign WildJailbreak set; its all-row difference bounds are8.83--9.43pp.'
    new=f'WildGuard has {wg["complete_n"]} complete nine-unit pairs on the {wg["retained_n"]}-row benign WildJailbreak set; its all-row difference bounds are {wg["all_rows_bounds_pp"][0]:.2f}--{wg["all_rows_bounds_pp"][1]:.2f} pp.'
    text=text.replace(old,new).replace('retain238,1301,210','retain 238, 1301, and 210').replace('at120','at 120');p.write_text(text)
    p=generated/'public_refusal_results.tex';text=p.read_text().replace('same120','same 120').replace('fixed30','fixed 30').replace('reported200','reported 200').replace('difference is-','difference is -');p.write_text(text)
    # Main abstract remains method-only under the still-active PAIR-500 read lock.
    report=ROOT/'docs/255_PUBLIC_ORDERED_READ_RESULTS.md'
    with report.open('a') as f:f.write('\n摘要决定：公开侧现已读取，不能只报有害侧收益。主摘要继续保留方法句，遵守此前PAIR-500两判官完成后再统一更新的要求；当前正文并列报告有害差与公开拒答代价。九单元top-2是#11敏感性，不是#19门槛。\n')
    files=[report,ROOT/'docs/255_NINE_UNIT_SUPPLEMENTAL_TABLES.md',NINE/'supplemental_tables.json',NINE/'token_length_diagnostic.json',NINE/'alpha0_701_prompt_length_correction.json',tables/'public_refusal_nine.tex',tables/'wjb_official_units.tex',tables/'wjb_exposure.tex',generated/'wjb_nine_scope.tex',generated/'public_refusal_results.tex',ROOT/'paper/sections/04_results.tex',ROOT/'paper/sections/05_traps.tex',ROOT/'paper/sections/06_limitations.tex']
    manifest={'utc':now,'files':{str(x.relative_to(ROOT)):sha(x) for x in files},'public_step_ledger_sha256':sha(PUBLIC/'step_ledger.json'),'previous_export_manifest_sha256':sha(PUBLIC/'export_manifest.json'),'abstract':'methods only pending completed PAIR500 two-judge read','model_annotations':'GPT-6 family in current session; exact serving snapshot unavailable; shared context; no independent human calibration','PAIR500_outcomes_read':False}
    save(BASE/'public_nine_manuscript_update.json',manifest)
    entry=f'{now} PUBLIC_AND_NINE_TABLES_COMPLETE reportSHA={sha(report)} manifestSHA={sha(BASE/"public_nine_manuscript_update.json")} WG-negative decomposition post-hoc after primary; fit12 mapped38rows/3groups descriptive; primary v2 retained; WJB-random conservative recall fails5/30U. ID701 correction rawprompt138 versus fullformatted4817, old wording superseded. Top2 is addendum11 sensitivity, not addendum19 gate. Main abstract stays methods-only pending final PAIR500 read; no outcome-driven scheduling changes.\n'
    for file in ['docs/PREREG_LOG.txt','docs/OPS_LOG.txt']:
        p=ROOT/file
        with p.open('a') as f:f.write(entry)
    print(json.dumps({'utc':now,'report_sha256':sha(report),'manuscript_manifest_sha256':sha(BASE/'public_nine_manuscript_update.json'),'supplemental_json_sha256':sha(NINE/'supplemental_tables.json')},ensure_ascii=False))

if __name__=='__main__':main()
