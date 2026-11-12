"""Direct-address alpha0 score access. No cache scan or nonzero inputs allowed."""
from pathlib import Path
import hashlib,json
def alpha0_cache_path(root,row,schedule_sha256):
 if row.get('condition')!='alpha0':raise ValueError('Only alpha0 input manifests admitted')
 fields={k:row[k] for k in ['generation_sha256','prompt_sha256','response_sha256','behavior_sha256']};fields.update(preprocessing_sha256=row.get('preprocessing_sha256'),judge='SORRY',schedule_sha256=schedule_sha256)
 key=hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest();return Path(root)/'results/audit/unified300/main_scores/SORRY/records.private'/(key+'.json')
def load_alpha0_cache(root,row,schedule_sha256):
 p=alpha0_cache_path(root,row,schedule_sha256);z=json.loads(p.read_text())
 assert z['condition']=='alpha0' and z['model']==row['model'] and z['family']==row['family']
 assert z['generation_sha256']==row['generation_sha256'] and z.get('preprocessing_sha256')==row.get('preprocessing_sha256')
 assert z['signature']['schedule_sha256']==schedule_sha256
 return z
