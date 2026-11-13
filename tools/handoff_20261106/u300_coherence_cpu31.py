from u300_schedule_prepare import *
import sys,numpy as np,concurrent.futures,collections
sys.path.insert(0,str(T));from coherence300_metrics import metrics
O=U/'followup31';P=L(U/'coherence_metrics_frozen_v3.json');assert H(T/'coherence300_metrics.py')==P['worker_sha256']
fields=['word4_repeated_occurrence_fraction','character4_repeated_occurrence_fraction','nonlanguage_character_fraction']
def cell(job):
 f,c=job;d=U/'static_alpha0/qwen'/f if c=='alpha0' else U/'ready_generated/qwen'/f/c;rows=[]
 for p in sorted((d/'generation.private').glob('*.json')):rows.append(metrics(L(p)['result']['text']))
 assert len(rows)==440
 z=dict(family=f,condition=c,N=440,empty=sum(r['empty'] for r in rows),language_failures=sum(r['language_identification_failed'] for r in rows),language_counts=dict(collections.Counter(str(r['language']) for r in rows)))
 for name in fields:
  a=[r[name] for r in rows if r[name] is not None];z[name]=dict(N_eligible=len(a),mean=float(np.mean(a)) if a else None,median=float(np.median(a)) if a else None)
 return z
if __name__=='__main__':
 base=L(U/'ready_generation_plan.json');families=[f for f in base['models']['qwen']['families'] if not f.startswith('translate-')];jobs=[(f,c) for f in families for c in base['condition_order']['qwen']];done=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=6) as pool:
  for z in pool.map(cell,jobs):done.append(z);save(O/'coherence31_progress.json',dict(utc=utc(),complete_cells=len(done),total_cells=len(jobs),no_gpu=True))
 save(O/'Qwen_R1_coherence31.json',dict(utc=utc(),parent_plan_sha256=H(U/'coherence_metrics_frozen_v3.json'),scope='Qwen R1 English raw generated continuation; no language-stage effect read',cells=done,descriptive_only=True));print('Coherence60 complete')
