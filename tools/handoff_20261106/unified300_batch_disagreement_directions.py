from pathlib import Path
import json,datetime,hashlib,math
R=Path('/home/dell/Def');U=R/'results/audit/unified300'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
plan=load(U/'S0_followup_diagnostics_execution.json');assert sha(__file__)==plan['direction_worker_sha256'];result=[]
def pvalue(a,b):
 n=a+b
 return 1.0 if n==0 else min(1.0,2*sum(math.comb(n,k)for k in range(min(a,b)+1))/2**n)
for version,tag in [('',32),('_v3',16),('_v4',8)]:
 inp=U/('acceptance_cap2400_inputs'+version+'.private.json');rows=[x for x in load(inp)if x['model']=='qwen'];folder=U/('acceptance_cap2400_labels'+version)/'scores.private';lookup={(x['condition'],x['path'],x['id']):x for x in rows}
 for condition in ['alpha0','s3','random']:
  ids=sorted({x['id']for x in rows if x['condition']==condition});assert len(ids)==100
  discord={k:{'batch_more_refusal':[],'batch_less_refusal':[],'unknown':[]}for k in ['WG','v2']}
  for k in ids:
   a=lookup[(condition,'legacy_single',k)];b=lookup[(condition,'candidate_batch',k)];x=load(folder/(a['cache_id']+'.json'));y=load(folder/(b['cache_id']+'.json'));assert x['generation_record_sha256']==a['generation_record_sha256']and y['generation_record_sha256']==b['generation_record_sha256']
   for rule,left,right in [('WG',{'yes':1,'no':0}.get(x['WG_labels']['Response refusal']),{'yes':1,'no':0}.get(y['WG_labels']['Response refusal'])),('v2',x['v2'],y['v2'])]:
    if left is None or right is None:discord[rule]['unknown'].append(k)
    elif left==0 and right==1:discord[rule]['batch_more_refusal'].append(k)
    elif left==1 and right==0:discord[rule]['batch_less_refusal'].append(k)
  for rule,d in discord.items():
   more=len(d['batch_more_refusal']);less=len(d['batch_less_refusal']);result.append(dict(batch_size=tag,condition=condition,rule=rule,N=100,more_refusal=more,less_refusal=less,unknown=len(d['unknown']),McNemar_two_sided_exact=pvalue(more,less),discordant_IDs=d))
p=U/'batch_disagreement_directions.json';assert not p.exists();p.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_sha256=sha(U/'S0_followup_diagnostics_execution.json'),records=result,absolute_condition_rates_aggregated=False,meaning='Operational filter diagnostics only; same fixed prompts across candidates, no claim of population equivalence or candidate ranking.'),indent=2)+'\n');print(json.dumps(result,indent=2));print('SHA',sha(p))
