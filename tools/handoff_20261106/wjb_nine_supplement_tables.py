"""Requested descriptive tables after the completed nine-unit primary read."""
from pathlib import Path
import csv
import datetime
import hashlib
import json
import sys

import numpy as np

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'nine_read_20261109'
sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
import wjb_nine_ordered_read as read
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def main():
    assert (OUT/'09_prediction.json').exists()
    names=['alpha0']+read.NAMES;hb=read.labels('HB_top1',names);wg=read.labels('WildGuard',names);ref=read.labels('WildGuard',names,'Response refusal')
    prior=json.loads((OUT/'07_refusal_agreement.json').read_text())['result']['conditions'];rows=read.mapping();unit=[];negative=[]
    for j,name in enumerate(names):
        x={'condition':name,'n':2000,'HB_harmful_yes':int(np.nansum(hb[:,j])),'HB_harmful_pct':100*float(np.nansum(hb[:,j]))/2000,
            'WG_harmful_yes':int(np.nansum(wg[:,j])),'WG_harmful_invalid':int(np.isnan(wg[:,j]).sum()),'WG_harmful_bounds_pct':[100*float(np.nansum(wg[:,j]))/2000,100*float(np.nansum(wg[:,j])+np.isnan(wg[:,j]).sum())/2000],
            'WG_refusal_yes':int(np.nansum(ref[:,j])),'WG_refusal_invalid':int(np.isnan(ref[:,j]).sum()),'WG_refusal_bounds_pct':[100*float(np.nansum(ref[:,j]))/2000,100*float(np.nansum(ref[:,j])+np.isnan(ref[:,j]).sum())/2000],
            'v2_refusal_yes':prior[name]['all']['v2_refusal_count'],'v2_refusal_pct':100*prior[name]['all']['v2_refusal_count']/2000}
        for judge,matrix in [('HB',hb),('WG',wg)]:
            good=np.isfinite(matrix[:,0])&np.isfinite(matrix[:,j]);x[judge+'_change_vs_alpha0_complete_pair_pp']=float((matrix[good,j]-matrix[good,0]).mean()*100);x[judge+'_change_pair_n']=int(good.sum())
        unit.append(x)
        select=ref[:,j]==0;n=int(select.sum());valid=select&np.isfinite(wg[:,j]);yes=int(np.nansum(wg[select,j]));inv=int((select&~np.isfinite(wg[:,j])).sum())
        negative.append({'condition':name,'WG_nonrefusal_n':n,'reply_harmful_yes':yes,'reply_harmful_invalid':inv,'rate_bounds_pct':[100*yes/n,100*(yes+inv)/n],
            'valid_reply_n':int(valid.sum()),'rate_among_valid_pct':100*yes/int(valid.sum()),'refusal_field_invalid_outside_layer':int(np.isnan(ref[:,j]).sum())})
    marked=np.array([r['historical_group_used'] or r['legacy_group_manifest_used'] for r in rows]);fit=np.array(['fit12' in r['group_flags'] for r in rows]);assert marked.sum()==1435 and (~marked).sum()==565
    groups=np.array([r['group'] for r in rows]);exposure={}
    for label,mask in [('marked',marked),('unmarked',~marked),('mapped_fit12',fit)]:
        exposure[label]={'n':int(mask.sum()),'mapping_layer':'mapped behavior exposure, unvalidated','judges':{j:read.paired_summary(m[mask,1:],groups[mask]) for j,m in [('HB_top1',hb),('WildGuard',wg)]}}
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();result={'utc':now,'unit_table':unit,'exposure':exposure,'WG_nonrefusal_harmful':negative,
        'WG_nonrefusal_status':'post-hoc exploratory extension after primary effects: addendum14 specified v2/union-negative layers, not WG-negative. Direct intersections, not total harmful divided by nonrefusal.',
        'scope':'Llama-3.1-8B-Instruct, fixed alpha1, WildJailbreak evaluation n2000; matched norm random directions. No alpha chosen here; behavior mappings/exposure unvalidated.'}
    save(OUT/'supplemental_tables.json',result)
    with (ROOT/'paper/data/wjb_official_units.csv').open('w',newline='') as f:
        fields=list(unit[0]);writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(unit)
    lines=['# 九单元追加描述表','',f'生成UTC：{now}。WG未拒答条件化是主差读数之后的事后探索；所有行保留。','',
        '| 条件 | HB有害% | WG有害%边界 | WG拒答%边界 | v2拒答% | HB相对alpha0变化pp | WG相对alpha0完整配对变化pp |','|---|---:|---|---|---:|---:|---:|']
    for x in unit:lines.append(f'| {x["condition"]} | {x["HB_harmful_pct"]:.2f} | {x["WG_harmful_bounds_pct"]} | {x["WG_refusal_bounds_pct"]} | {x["v2_refusal_pct"]:.2f} | {x["HB_change_vs_alpha0_complete_pair_pp"]:.4f} | {x["WG_change_vs_alpha0_complete_pair_pp"]:.4f} |')
    lines+=['','| 映射标记层 | n | 判官 | 主差pp | 行为聚类95% | 全行识别边界pp |','|---|---:|---|---:|---|---|']
    for label,x in exposure.items():
        for j,v in x['judges'].items():lines.append(f'| {label} | {x["n"]} | {j} | {v["conditional_complete_pair_mean_pp"]:.4f} | {v["behavior_cluster_bootstrap95_pp"]} | {v["all_rows_identification_bounds_pp"]} |')
    lines+=['','标记层按映射行为定义，未经验证；fit12层与标记层重叠。仅描述，不据此声称独立泛化。','',
        '| 条件 | WG未拒答n | 其中回复有害 | 回复有害INVALID | 有害比例边界% |','|---|---:|---:|---:|---|']
    for x in negative:lines.append(f'| {x["condition"]} | {x["WG_nonrefusal_n"]} | {x["reply_harmful_yes"]} | {x["reply_harmful_invalid"]} | {x["rate_bounds_pct"]} |')
    lines+=['','模型条件化分解只作描述，不是中介或机制检验。',f'','源JSON SHA256：{sha(OUT/"supplemental_tables.json")}。']
    doc=ROOT/'docs/255_NINE_UNIT_SUPPLEMENTAL_TABLES.md';doc.write_text('\n'.join(lines)+'\n')
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{now} NINE_SUPPLEMENTAL_TABLES docSHA={sha(doc)} dataSHA={sha(OUT/"supplemental_tables.json")} WG-negative decomposition post-hoc after primary; exposure layer unvalidated; top2 is addendum11 sensitivity, not addendum19 gate per user correction.\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
