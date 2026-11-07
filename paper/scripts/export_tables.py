from pathlib import Path
import argparse,csv,json,hashlib,re
P=Path(__file__).resolve().parents[1];B=P.parent
p=argparse.ArgumentParser();p.add_argument('--from-csv',action='store_true');args=p.parse_args()
def read(n):return json.loads((B/n).read_text())
def sha(n):return hashlib.sha256((B/n).read_bytes()).hexdigest()
def dump(name,rows):
 path=P/'data'/name
 with path.open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def load(name):
 with(P/'data'/name).open()as f:return list(csv.DictReader(f))
def score(file):
 d=read(file);assert d['n']==70 and d['invalid']==0;return sum(r['p_yes']>.5 for r in d['items'].values())
sources=set()
if not args.from_csv:
 z=[]
 source='results/hfjudge/JUDGE_HF_RERUN_v70_a0.0_b8f62434.json';sources.add(source);z.append(dict(group='Baseline',unit='a0',harmful=score(source),n=70))
 for seed,root in[(0,'hfjudge_batch2'),(1,'hfjudge_batch2'),(2,'hfjudge_batch3')]:
  source=f'results/{root}/JUDGE_HF_rand{seed}_a1.0';sources.add(source);z.append(dict(group='Gaussian',unit=str(seed),harmful=score(source),n=70))
 for seed in range(8):
  source=f'results/hfjudge_init/JUDGE_HF_init_seed{seed}';sources.add(source);z.append(dict(group='Init-only',unit=str(seed),harmful=score(source),n=70))
 source='results/audit/handoff_round7/window_frontier_results.json';sources.add(source)
 for r in read(source)['old8_cloud']:z.append(dict(group='Learned',unit=str(r['seed']),harmful=round(r['asr_pct']*70/100),n=70))
 dump('zero_line.csv',z)
 source='results/audit/handoff_round8/doc250_descriptive_stats.json';sources.add(source);dump('c2.csv',[dict(seed=r['seed'],val296_DD_pp=r['val296_DD_pp'],docs250_DD_pp=r['docs250_DD_pp'],vanilla_new=r['docs250_vanilla_new'])for r in read(source)['rows']])
 source='results/style_retrained/alpha_matches_frozen.json';sources.add(source);dump('matching.csv',list(read(source)['rows'].values()))
 matched=read(source);dump('style_alpha_grid.csv',[dict(seed=r['seed'],arm='wrapped',alpha=r['alpha'],ASR_pct=r['asr_pct'],harmful=round(r['asr_pct']*70/100),n_attack=70,new_legal=r['new_legal'],n_legal=388,distance_pp=r['distance_pp'])for r in matched['grid']]+[dict(seed=r['seed'],arm='control',alpha=1.0,ASR_pct=r['control_asr_pct'],harmful=round(r['control_asr_pct']*70/100),n_attack=70,new_legal=r['control_new_legal'],n_legal=388,distance_pp=0)for r in matched['rows'].values()])
 source='results/audit/handoff_round10/training_repeat_dispersion.json';sources.add(source);dump('repeats.csv',[dict(run=label,harmful=k,n=70,ASR_pct=k/70*100)for label,k in zip(['Frozen','Rebuild','Repeat A','Repeat B'],read(source)['four_counts'])])
 source='results/audit/handoff_round10/verified_card_mapping.json';sources.add(source);fields=['seed','train_host','control_GPU','wrapped_GPU','plain_GPU_planned','generation_host','generation_GPU'];dump('card_mapping.csv',[{k:r[k]for k in fields}for r in read(source)])
 rows=[]
 configs=[('Llama','Baseline','results/hfjudge/JUDGE_HF_RERUN_v70_a0.0_b8f62434.json'),('Llama','A','results/hfjudge_sys/JUDGE_HF_SYS_A'),('Llama','B','results/hfjudge_sys/JUDGE_HF_SYS_B'),('Qwen','Baseline','results/hfjudge_lmi/JUDGE_HF_qwen_a0_2400')]+[('Qwen',x,('results/hfjudge/'if x=='B_append'else'results/hfjudge_qab/')+'JUDGE_HF_qwen_'+x)for x in['A_replace','A_append','B_replace','B_append']]
 for model,cond,source in configs:sources.add(source);k=score(source);rows.append(dict(model=model,condition=cond,harmful=k,n=70,ASR_pct=k/70*100))
 dump('zero_training.csv',rows)
 source='docs/254_FRONTIER_APPENDIX.md';sources.add(source);intervals=re.findall(r'\| (固定五seed[^|]*|再重抽seed簇|超界点截至端点诊断) \| \[([^,]+),([^\]]+)\]',(B/source).read_text());assert len(intervals)==3
 dump('frontier_joint.csv',[dict(variant=label,lower_pp=lo.replace('−','-'),upper_pp=hi.replace('−','-'))for label,(_,lo,hi)in zip(['Item resampling (conditional)','Also resample seeds (conditional)','Boundary clipping diagnostic'],intervals)])
 (P/'data/source_manifest.json').write_text(json.dumps(dict(sources={n:sha(n)for n in sorted(sources)},csv_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in(P/'data').glob('*.csv')}),indent=2)+'\n')
def tex_escape(s):
 for old,new in[('&',r'\&'),('%',r'\%'),('_',r'\_')]:s=s.replace(old,new)
 return s
def table(name,columns,headers,rows,caption,label):
 lines=[r'\begin{table}['+('H'if name=='frontier_joint.tex'else't')+']',r'\centering',r'\small',r'\setlength{\tabcolsep}{3pt}',r'\begin{tabular}{'+columns+'}',r'\toprule',' & '.join(headers)+chr(32)+chr(92)*2,r'\midrule']
 lines +=[' & '.join(r)+chr(32)+chr(92)*2 for r in rows];lines +=[r'\bottomrule',r'\end{tabular}',r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{table}'];(P/'tables'/name).write_text('\n'.join(lines)+'\n')
z=load('zero_line.csv');rows=[]
for group in['Baseline','Gaussian','Init-only','Learned']:
 values=[100*int(r['harmful'])/int(r['n'])for r in z if r['group']==group];rng=f'{min(values):.1f}'if len(values)==1 else f'{min(values):.1f}--{max(values):.1f}';rows.append([group,str(len(values)),rng])
table('zero_line.tex','lrr',['Condition','Units',r'ASR (\%)'],rows,'HF judge ASR on val70. Random and learned vectors have norm 5.21. Units are directions or training seeds, not prompts.','tab:zeroline')
table('c2.tex','rrrr',['Seed','val-source DD','WJB DD','Van. new'],[[r['seed'],f"{float(r['val296_DD_pp']):.2f}",f"{float(r['docs250_DD_pp']):.2f}",r['vanilla_new']]for r in load('c2.csv')],'Benign wrapper gaps (pp) for the same five old vectors on different prompt samples. The denominators are 293 and 292 baseline-eligible pairs. Vanilla additions are operational rule counts on the 292-pair sample.','tab:c2')
table('matching.tex','rrrrrr',['Seed',r'$\alpha_T$','ASR C','ASR T','New C','New T'],[[r['seed'],r['selected_alpha'],f"{float(r['control_asr_pct']):.1f}",f"{float(r['selected_asr_pct']):.1f}",r['control_new_legal'],r['selected_new_legal']]for r in load('matching.csv')],'First frozen matching table: retrained control C at alpha 1 and wrapped-data treatment T. ASR is a percentage on 70 prompts; legal new counts use 388 eligible items after full 400-item batch-8 generation. Holdout outcomes remain unreported until complete.','tab:matching')
table('repeats.tex','lrr',['Seed 3 run','Harmful /70',r'ASR (\%)'],[[r['run'],r['harmful'],f"{float(r['ASR_pct']):.2f}"]for r in load('repeats.csv')],'Four seed 3 runs: one historical frozen vector and three modern reruns sharing target cache, initialization and optimization path. A/B are the explicitly paired same-script repeats. The samples are too small for variance decomposition.','tab:repeats')
table('zero_training.tex','llrr',['Model','Condition','Harmful /70',r'ASR (\%)'],[[r['model'],tex_escape(r['condition']),r['harmful'],f"{float(r['ASR_pct']):.1f}"]for r in load('zero_training.csv')],'Zero-training prompt baselines, using HF judgments with zero INVALID. Legal-side model counts and uncalibrated ranges are discussed separately.','tab:zerotraining')


table('frontier_joint.tex',r'p{0.61\columnwidth}r',['Joint sensitivity',r'95\% interval'],[[tex_escape(r['variant']),'['+r['lower_pp']+', '+r['upper_pp']+']']for r in load('frontier_joint.csv')],'Joint frontier sensitivity in pp. The first two intervals condition on all points being interpolable. In 4764/10000 draws at least one point was unsupported; clipping changes the estimand. None establishes equivalence within plus/minus 3 pp.','tab:frontierjoint')

print('CSV_TABLES_GENERATED',len(list((P/'tables').glob('*.tex'))))
