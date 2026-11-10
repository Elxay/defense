"""Read S0 reference scores only after all gates/files; no target-condition analysis."""
from pathlib import Path
import datetime, hashlib, json
import numpy as np

R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stats(gold,pred):
 valid=np.array([v in [0,1]for v in pred]);p=np.array([v if v in[0,1]else 0 for v in pred],dtype=int);g=np.asarray(gold,dtype=int)
 tn=int(np.sum(valid&(g==0)&(p==0)));fp=int(np.sum(valid&(g==0)&(p==1)));fn=int(np.sum(valid&(g==1)&(p==0)));tp=int(np.sum(valid&(g==1)&(p==1)));n=tn+fp+fn+tp;total=len(g);invalid=total-n
 pe=((tn+fp)*(tn+fn)+(fn+tp)*(fp+tp))/(n*n)if n else None
 kappa=((tn+tp)/n-pe)/(1-pe)if n and pe!=1 else None
 return dict(N=total,valid=n,invalid=invalid,confusion_human0_1_by_model0_1=[[tn,fp],[fn,tp]],accuracy_all_lower=(tn+tp)/total,accuracy_all_upper=(tn+tp+invalid)/total,accuracy_valid=(tn+tp)/n if n else None,kappa_valid=kappa)
def bootstrap(gold,pred,qids,seed=20261260,B=2000):
 keys=sorted(set(qids));groups=[np.where(qids==k)[0]for k in keys];rng=np.random.default_rng(seed);a=[];k=[]
 for _ in range(B):
  ix=np.concatenate([groups[i]for i in rng.integers(0,len(groups),len(groups))]);s=stats(gold[ix],[pred[i]for i in ix]);a.append(s['accuracy_all_lower'])
  if s['kappa_valid']is not None:k.append(s['kappa_valid'])
 return {'unit':'base instruction','clusters':len(keys),'replicates':B,'seed':seed,'accuracy_all_lower_CI95':np.quantile(a,[.025,.975]).tolist(),'kappa_valid_CI95':np.quantile(k,[.025,.975]).tolist()if k else None}
def main():
 plan=load(U/'human_reference_plan.json');assert sha(U/'human_gold.private.json')==plan['gold_sha256'];assert sha(U/'human_inputs.private.json')==plan['input_sha256']
 assert load(U/'HB_gate20.json')['passed']and load(U/'SORRY_gate20.json')['passed']
 assert load(U/'HB_complete.json')['n']==4400 and load(U/'SORRY_complete.json')['n']==4400
 for shard in range(3):assert load(U/f'WG_gate20_{shard}.json')['passed'];assert load(U/f'WG_complete_{shard}.json')['n']in[1466,1467]
 gold=load(U/'human_gold.private.json');ids=[r['id']for r in gold];y=np.array([r['human_label']for r in gold]);qid=np.array([r['question_id']for r in gold]);pred={};invalid={};files={}
 for judge in['SORRY','HB','WG']:
  d=U/(judge+'_scores');assert len(list(d.glob('*.json')))==4400
  values=[];bad={};manifest={}
  for key in ids:
   p=d/(key+'.json');x=load(p);assert x['id']==key and x['signature']['input_sha256']==plan['input_sha256'];manifest[key]=sha(p)
   if judge=='WG':
    labels=x['labels'];v={'yes':1,'no':0}.get(labels['Harmful response'])
    for field,label in labels.items():
     if label not in['yes','no']:bad.setdefault(field,[]).append(key)
   else:
    v=x['label']
    if v not in[0,1]:bad.setdefault('fulfillment'if judge=='SORRY'else'raw_YesNo',[]).append(key)
   values.append(v)
  pred[judge]=values;invalid[judge]=bad;files[judge]=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'S0 heldout human reference, not steering effect','human_test_sha256':plan['test_source_sha256'],'N':4400,'judges':{},'pairwise':{},'INVALID_IDs':invalid,'score_file_manifest_sha256':files,'interpretation':'WG harmfulness/HB completion versus human fulfillment are related but distinct constructs; no judge dropped or threshold tuned'}
 for j,v in pred.items():
  result['judges'][j]={**stats(y,v),'cluster_CI':bootstrap(y,v,qid),'strata':{}}
  for group,mask in [('base',np.array([r['prompt_style']=='base'for r in gold])),('OOD',np.array([r['prompt_style']!='base'for r in gold]))]:
   ix=np.where(mask)[0];result['judges'][j]['strata'][group]=stats(y[ix],[v[i]for i in ix])
 for a,b in[('SORRY','HB'),('SORRY','WG'),('HB','WG')]:
  valid=[i for i in range(4400)if pred[a][i]in[0,1]and pred[b][i]in[0,1]];result['pairwise'][a+'__'+b]={**stats([pred[a][i]for i in valid],[pred[b][i]for i in valid]),'common_valid_N':len(valid)}
 common=[i for i in range(4400)if all(pred[j][i]in[0,1]for j in pred)];result['three_common_valid_N']=len(common);result['common_valid_accuracy']={j:stats(y[common],[v[i]for i in common])for j,v in pred.items()}
 path=U/'human_agreement_results.json';assert not path.exists(),'Preserve previous read output';path.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({j:{k:v[k]for k in['N','valid','invalid','accuracy_all_lower','kappa_valid']}for j,v in result['judges'].items()},indent=2));print('OUTPUT_SHA',sha(path))
if __name__=='__main__':
 assert stats([0,1,0,1],[0,1,0,1])['kappa_valid']==1
 assert stats([0,1,0,1],[1,0,1,0])['kappa_valid']==-1
 assert stats([0,1],[None,1])['accuracy_all_lower']==.5
 main()
