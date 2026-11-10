from pathlib import Path
import json,hashlib,datetime,math
R=Path('/home/dell/Def');U=R/'results/audit/unified300'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=load(U/'B4_direction_execution_plan.json');assert sha(__file__)==plan['worker_sha256'];inp=U/'acceptance_cap2400_inputs_v5.private.json';assert sha(inp)==plan['inputs_sha256'];rows=load(inp);table={(r['condition'],r['path'],r['id']):r for r in rows};folder=U/'acceptance_cap2400_labels_v5/scores.private';out=[]
for condition in ['alpha0','s3','random']:
 IDs=sorted({r['id']for r in rows if r['condition']==condition});assert len(IDs)==100;d={rule:{'more':[],'less':[],'unknown':[]}for rule in ['WG','v2']}
 for k in IDs:
  a=table[(condition,'legacy_single',k)];b=table[(condition,'candidate_batch',k)];x=load(folder/(a['cache_id']+'.json'));y=load(folder/(b['cache_id']+'.json'));assert x['generation_record_sha256']==a['generation_record_sha256']and y['generation_record_sha256']==b['generation_record_sha256']
  for rule,left,right in [('WG',{'yes':1,'no':0}.get(x['WG_labels']['Response refusal']),{'yes':1,'no':0}.get(y['WG_labels']['Response refusal'])),('v2',x['v2'],y['v2'])]:
   if left is None or right is None:d[rule]['unknown'].append(k)
   elif left==0 and right==1:d[rule]['more'].append(k)
   elif left==1 and right==0:d[rule]['less'].append(k)
 for rule,v in d.items():
  a=len(v['more']);b=len(v['less']);n=a+b;p=1.0 if n==0 else min(1.,2*sum(math.comb(n,j)for j in range(min(a,b)+1))/2**n);out.append(dict(condition=condition,rule=rule,N=100,batch_more_refusal=a,batch_less_refusal=b,unknown=len(v['unknown']),McNemar_exact_two_sided=p,discordant_IDs=v))
p=U/'B4_disagreement_directions.json';assert not p.exists();p.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_plan_sha256=sha(U/'B4_direction_execution_plan.json'),batch_size=4,records=out,no_absolute_condition_rates=True),indent=2)+'\n');print(json.dumps(out,indent=2));print('SHA',sha(p))
