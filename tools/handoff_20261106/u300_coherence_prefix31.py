from u300_schedule_prepare import *
import sys,numpy as np,concurrent.futures,collections
sys.path.insert(0,str(T));from coherence300_metrics import metrics
O=U/'followup31';P=L(U/'coherence_metrics_frozen_v3.json');assert H(T/'coherence300_metrics.py')==P['worker_sha256']
def cell(job):
 f,c=job;d=U/'static_alpha0/qwen'/f if c=='alpha0' else U/'ready_generated/qwen'/f/c;lookup={r['id']:r['prefill'] for r in L(U/'static_alpha0_inputs.private.json')['qwen'][f]};vals=[]
 for p in sorted((d/'generation.private').glob('*.json')):
  z=L(p);prefix=lookup[z['id']];assert prefix;vals.append(metrics(prefix+z['result']['text']))
 assert len(vals)==440;r=dict(family=f,condition=c,N=440,empty=sum(v['empty'] for v in vals),language_failures=sum(v['language_identification_failed'] for v in vals))
 for k in ['word4_repeated_occurrence_fraction','character4_repeated_occurrence_fraction','nonlanguage_character_fraction']:
  a=[v[k] for v in vals if v[k] is not None];r[k]=dict(N_eligible=len(a),mean=float(np.mean(a)),median=float(np.median(a)))
 return r
if __name__=='__main__':
 jobs=[(f,c) for f in ['prefix_P1','prefix_P2'] for c in L(U/'ready_generation_plan.json')['condition_order']['qwen']]
 with concurrent.futures.ProcessPoolExecutor(max_workers=4) as p:rows=list(p.map(cell,jobs))
 save(O/'Qwen_prefix_full_coherence31.json',dict(utc=utc(),parent_plan_sha256=H(U/'coherence_metrics_frozen_v3.json'),known_frozen_prefill_only=True,cells=rows));print('Full-prefix sensitivity12 complete')
