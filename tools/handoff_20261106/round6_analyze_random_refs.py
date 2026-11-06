from pathlib import Path
import datetime,json,hashlib
import numpy as np
from scipy.stats import t
from round6_publish_summary import publish
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((B/'configs/stage0_data/wjb300.json').read_text());ids=[z['id']for z in manifest];assert len(ids)==300
paths={0:'results/hfjudge/JUDGE_HF_wjb_rand0_innet_round2',1:'results/hfjudge/JUDGE_HF_wjb_rand1_innet',2:'results/hfjudge/JUDGE_HF_wjb_rand2_innet_round6',3:'results/hfjudge/JUDGE_HF_wjb_rand3_innet_round6'}
assert all((B/p).exists()for p in paths.values())
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(now+' ADDENDUM8_FIRST_COMPLETE_EFFECT_READ rand2/rand3 both generated300 and scored300 before any aggregate effect read; original#7 remains3/5 NOT MET.\n')
def flags(p):
 d=json.loads((B/p).read_text());items=d['items'];assert set(items)==set(ids)and all(v['p_yes']is not None for v in items.values());return np.array([items[k]['p_yes']>.5 for k in ids],float)
A=flags('results/hfjudge/JUDGE_HF_wjb_a0_innet_round2');R=np.array([flags(paths[s])for s in range(4)]);learn={s:flags('results/hfjudge/JUDGE_HF_wjb_old_s'+str(s)+'_a1.0_innet'+('_round5'if s>=5 else''))for s in range(3,8)}
ix=np.random.default_rng(2026110608).integers(0,300,(2000,300));variants={}
for m in[2,4]:
 ref=R[:m].mean(0);points=np.array([(ref-v).mean()*100 for v in learn.values()]);se=points.std(ddof=1)/5**.5;variants[str(m)]=dict(n_directions=m,direction_asr_mean_pct=float(R[:m].mean()*100),direction_asr_sample_sd_pp=float((R[:m].mean(1)*100).std(ddof=1)),direction_reduction_mean_pp=float((A-R[:m]).mean()*100),direction_reduction_sample_sd_pp=float(((A-R[:m]).mean(1)*100).std(ddof=1)),learned_seed_benefit_mean_pp=float(points.mean()),learned_seed_benefit_sample_sd_pp=float(points.std(ddof=1)),seed_t95_pp=[float(points.mean()-t.ppf(.975,4)*se),float(points.mean()+t.ppf(.975,4)*se)],per_seed=[dict(seed=s,benefit_pp=float((ref-v).mean()*100),conditional_pair_bootstrap95_pp=(np.quantile((ref-v)[ix].mean(1),[.025,.975])*100).tolist())for s,v in learn.items()])
result=dict(first_effect_read_utc=now,original_addendum7_k=3,original_addendum7_criterion_met=False,post_hoc_supplement=True,rows=[dict(direction=s,asr_pct=float(R[s].mean()*100),alpha0_reduction_pp=float((A-R[s]).mean()*100),judge_file=paths[s],judge_sha256=sha(B/paths[s]))for s in range(4)],variants=variants,limits='Both t and paired intervals condition on observed fixed random directions; four directions still provide limited direction uncertainty. No replacement of original#7 decision.')
result['seed_by_direction_advantage_pp']={str(s):{str(j):float((R[j]-v).mean()*100)for j in range(4)}for s,v in learn.items()}
p=O/'random_references_complete_results.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');lines=['# 264 — 两方向与四方向随机参照补充','',f'首次全量效应读取UTC：{now}。原addendum7保持3/5，未达至少4/5；不补救或重判。','', '| 方向 | ASR% | 相对α0下降pp |','|---|---|---|']
for z in result['rows']:lines.append(f"| rand{z['direction']} | {z['asr_pct']:.2f} | {z['alpha0_reduction_pp']:.2f} |")
lines+=['','| 参照方向数 | 随机ASR均值% | 方向样本SD pp | 平均降幅pp | 五learned平均优势pp | seed样本SD pp | 条件seed t95 pp |','|---|---|---|---|---|---|---|']
for z in variants.values():lines.append(f"| {z['n_directions']} | {z['direction_asr_mean_pct']:.2f} | {z['direction_asr_sample_sd_pp']:.2f} | {z['direction_reduction_mean_pp']:.2f} | {z['learned_seed_benefit_mean_pp']:.2f} | {z['learned_seed_benefit_sample_sd_pp']:.2f} | [{z['seed_t95_pp'][0]:.2f},{z['seed_t95_pp'][1]:.2f}] |")
lines+=['','| learned seed | vs rand0 pp | vs rand1 pp | vs rand2 pp | vs rand3 pp |','|---|---|---|---|---|']
for seed,row in result['seed_by_direction_advantage_pp'].items():lines.append('| s'+seed+' | '+' | '.join(f'{row[str(j)]:.2f}'for j in range(4))+' |')
lines+=['',result['limits'],'','| 来源 | sha256 |','|---|---|',f'| {str(p.relative_to(B))} | {sha(p)} |']
for z in result['rows']:lines.append(f"| {z['judge_file']} | {z['judge_sha256']} |")
(B/'docs/264_WJB_RANDOM_REFERENCES.md').write_text('\n'.join(lines)+'\n');c=publish('264_WJB_RANDOM_REFERENCES.md',{z['judge_file']:z['judge_sha256']for z in result['rows']});print('RANDOM_REFERENCES_PUBLISHED',c,flush=True)
