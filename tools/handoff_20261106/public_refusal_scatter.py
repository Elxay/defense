"""Paired per-vector tradeoff plots after all six fixed recall groups are saved."""
from pathlib import Path
import csv
import datetime
import hashlib
import json
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';OUT=BASE/'public_read_20261109'
sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
import public_refusal_ordered_read as public
import wjb_nine_ordered_read as harmful
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    groups=[OUT/f'08_recall_group{i}.json' for i in range(1,7)];assert all(p.exists() for p in groups)
    names=public.NAMES;harm={j:harmful.labels(j,names) for j in ['HB_top1','WildGuard']};records=[];files={}
    datasets=['xstest_safe','or_hard','wildjailbreak_benign'];labels=['XSTest safe','OR-Bench-Hard','WildJailbreak benign']
    offsets_by_dataset={
        'xstest_safe':[(4,5),(-17,-5),(5,8),(4,5),(4,-10),(4,5),(-17,-10),(6,-8),(4,5)],
        'or_hard':[(4,5),(4,5),(4,-10),(-17,5),(4,-10),(-16,-2),(4,-10),(4,5),(4,-10)],
        'wildjailbreak_benign':[(4,5),(7,7),(7,-14),(4,5),(-17,-13),(-16,7),(4,-13),(7,7),(7,-7)]}
    for layer,unseen in [('all',False),('keep60_unseen',True)]:
        fig,axes=plt.subplots(2,3,figsize=(12.8,7.5),layout='constrained')
        for row,judge in enumerate(['HB_top1','WildGuard']):
            matrix=harm[judge]
            for col,dataset in enumerate(datasets):
                _,ref=public.matrix(dataset,'v2',unseen);ax=axes[row,col]
                for j,name in enumerate(names[1:],1):
                    valid=np.isfinite(matrix[:,0])&np.isfinite(matrix[:,j]);x=float((matrix[valid,j]-matrix[valid,0]).mean()*100);y=float((ref[:,j]-ref[:,0]).mean()*100)
                    learned=name.startswith('old_s');color='#c35c25' if learned else '#2368a2';marker='o' if learned else 'D'
                    ax.scatter(x,y,color=color,marker=marker,s=40,edgecolors='white',linewidths=.5,zorder=3)
                    ax.annotate(name.replace('old_','').replace('rand','r'),(x,y),xytext=offsets_by_dataset[dataset][j-1],textcoords='offset points',fontsize=8,color=color)
                    records.append({'layer':layer,'judge':judge,'dataset':dataset,'condition':name,'class':'learned' if learned else 'random','harmful_change_pp':x,'harmful_valid_pairs':int(valid.sum()),'v2_refusal_change_pp':y,'public_n':len(ref)})
                ax.axhline(0,color='#999999',linewidth=.7,linestyle='--');ax.axvline(0,color='#999999',linewidth=.7,linestyle='--');ax.grid(alpha=.14)
                ax.set_title(labels[col]+f' (n={len(ref)})',fontsize=10);ax.set_xlabel('Model harmfulness change vs alpha0 (pp)',fontsize=8)
                if col==0:ax.set_ylabel(('Mapped HarmBench' if judge=='HB_top1' else 'WildGuard')+'\nv2 refusal change (pp)',fontsize=9)
                ax.margins(x=.22,y=.25);ax.tick_params(labelsize=8)
        handles=[plt.Line2D([0],[0],marker='o',color='none',markerfacecolor='#c35c25',markersize=7,label='Learned s3-s7'),plt.Line2D([0],[0],marker='D',color='none',markerfacecolor='#2368a2',markersize=6,label='Random r0-r3')]
        fig.legend(handles=handles,loc='outside upper center',ncol=2,frameon=False)
        for ext in ['png','pdf']:
            p=ROOT/'paper/figures'/f'wjb_harm_public_refusal_{layer}_labels_v2.{ext}';p.parent.mkdir(exist_ok=True);fig.savefig(p,dpi=200,bbox_inches='tight');files[str(p.relative_to(ROOT))]=sha(p)
        plt.close(fig)
    path=ROOT/'paper/data/wjb_harm_public_refusal_points.csv'
    with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
    assert sha(path)==json.loads((OUT/'09_scatter.json').read_text())['points_csv_sha256'],'Label layout must not change any point data'
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();result={'utc':now,'points_csv_sha256':sha(path),'previous_scatter_stage_sha256':sha(OUT/'09_scatter.json'),'plot_files_sha256':files,'recall_group_hashes':{p.name:sha(p) for p in groups},
        'scope':'Nine observed vectors; no fitting or decision threshold. X is all2000 official WJB harmful prompts, per-unit complete model-label pairs where required; Y is public full or keep60-unseen prompts. Model/rule operational labels, not calibrated human outcomes. Baseline-zero lines are references, not thresholds.'}
    p=OUT/'09_scatter_labels_v2.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n')
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{now} PUBLIC_SCATTER_LABEL_LAYOUT_ONLY_UPDATE SHA={sha(p)} original stage retained; point CSV SHA unchanged, no analytical change.\n')
    print(json.dumps({'utc':now,'sha256':sha(p),'files':files}))


if __name__=='__main__':main()
