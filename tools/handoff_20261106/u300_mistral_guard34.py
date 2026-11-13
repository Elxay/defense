from pathlib import Path
import os,sys,json,hashlib,datetime,time,collections,statistics
R=Path('/home/dell/Def');U=R/'results/audit/unified300';sys.path.insert(0,str(R/'tools/handoff_20261106'))
from u300_calibration_contract34 import assert_runtime_norm,assert_distinct_adjacent
L=lambda p:json.loads(Path(p).read_text());P=L(U/'Mistral_calibration32_plan.json');D=Path(P['output_root']);O=U/'followup34'
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
while True:
 result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),conditions=[],adjacent=[],selection_execution_contract_passed=False)
 try:
  for c in [('alpha0',None,0.)]+[(f's{s}_a{a:.2f}',s,a) for s in [3,4,5] for a in P['alpha_grid']]:
   name,s,a=c;records=[L(p) for p in sorted((D/name/'generation.private').glob('*.json'))];rho=0 if s is None else P['vectors'][str(s)]['norm'];vals=[r['result']['rho_runtime'] for r in records]
   for r in records:assert_runtime_norm(r['result']['rho_runtime'],a,rho)
   result['conditions'].append(dict(condition=name,N=len(records),complete=(D/name/'complete.json').exists(),alpha=a,expected=a*rho,runtime_min=min(vals) if vals else None,runtime_median=statistics.median(vals) if vals else None,runtime_max=max(vals) if vals else None,max_relative_error=max((abs(x-a*rho)/(a*rho) if a*rho else abs(x)) for x in vals) if vals else None,completed_utc=L(D/name/'complete.json')['utc'] if (D/name/'complete.json').exists() else None))
  for s in [3,4,5]:
   for a,b in zip(P['alpha_grid'][:-1],P['alpha_grid'][1:]):
    A=D/f's{s}_a{a:.2f}';B=D/f's{s}_a{b:.2f}'
    if not ((A/'complete.json').exists() and (B/'complete.json').exists()):continue
    maps=[]
    for folder in [A,B]:maps.append({r['id']:hashlib.sha256(r['result']['text'].encode()).hexdigest() for r in [L(p) for p in (folder/'generation.private').glob('*.json')]})
    result['adjacent'].append(dict(seed=s,alpha_pair=[a,b],**assert_distinct_adjacent(*maps)))
  result['selection_execution_contract_passed']=(D/'complete22.json').exists() and len(result['adjacent'])==18
 except Exception as e:result['error']=type(e).__name__+': '+str(e)
 save(O/'Mistral_norm_and_adjacent_guard.json',result)
 if result['selection_execution_contract_passed'] or result.get('error'):break
 time.sleep(20)
