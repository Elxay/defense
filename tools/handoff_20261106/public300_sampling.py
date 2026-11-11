"""WG-conditioned public audit sampling. Selecting IDs never reads response text."""
from pathlib import Path
import json,hashlib
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def select_one(rank,prompt_ids,normalized_rows):
 keys=[f"{rank['model']}/{rank['dataset']}/{c}/{i}"for c in rank['condition_order']for i in sorted(prompt_ids)]
 assert hashlib.sha256(canonical(keys)).hexdigest()==rank['pool_keys_sha256']
 ordered=[keys[i]for i in rank['permutation']];assert hashlib.sha256(canonical(ordered)).hexdigest()==rank['ranked_record_IDs_sha256']
 want=rank['WG_stratum']=='WG_plus';selected=[]
 for key in ordered:
  row=normalized_rows[key];label=row['WG_response_refusal'];assert type(label)is bool or label is None
  if label is not None and label==want:selected.append(key)
  if len(selected)==30:break
 return selected
if __name__=='__main__':
 # Harmless synthetic label mask only; no real output or score cache read.
 rank=dict(model='fixture',dataset='safe',condition_order=['s3'],pool_keys_sha256=hashlib.sha256(canonical(['fixture/safe/s3/a','fixture/safe/s3/b'])).hexdigest(),permutation=[1,0],ranked_record_IDs_sha256=hashlib.sha256(canonical(['fixture/safe/s3/b','fixture/safe/s3/a'])).hexdigest(),WG_stratum='WG_plus')
 rows={'fixture/safe/s3/a':{'WG_response_refusal':True},'fixture/safe/s3/b':{'WG_response_refusal':None}}
 assert select_one(rank,['a','b'],rows)==['fixture/safe/s3/a'];print('synthetic selection passed; real WG-conditioned IDs not selected')
