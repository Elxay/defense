"""Final admission checks only. Do not select outcome/INVALID values."""
from pathlib import Path
import argparse,datetime,hashlib,json
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';NAMES=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def status():
    snap=B/'frozen_prompt_snapshot.json';rows=load(snap)['rows']if snap.exists()else[];ids=[r['id']for r in rows];counts={n:{'generation':sum((B/'canonical254/generation.private'/n/(k+'.json')).is_file()for k in ids),'HB_or_MinHash':sum((B/'canonical254/scores'/n/(k+'.json')).is_file()for k in ids),'WildGuard':sum((B/'wildguard_pair254'/(n+'_scores')/(k+'.json')).is_file()for k in ids)}for n in NAMES}
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'n':len(ids),'snapshot_ready':bool(ids),'full500_all13_ready':len(ids)==500 and len(set(ids))==500 and all(v==500 for x in counts.values()for v in x.values()),'counts':counts,'outcome_values_selected':False,'INVALID_counted':False}
def verify_prompt_chain():
    snap=B/'frozen_prompt_snapshot.json';rows=load(snap)['rows'];ss=sha(snap);checked=0
    for name in NAMES:
        inputs=B/'wildguard_pair254'/(name+'_inputs.private.json');payload={r['id']:r for r in load(inputs)};ih=sha(inputs);assert len(payload)==len(rows)
        for row in rows:
            key=row['id'];p=B/'canonical254/generation.private'/name/(key+'.json');c=load(p);assert c['signature']['snapshot_sha256']==ss
            prefix=R/c['prefix_source'];g=load(prefix);assert sha(prefix)==c['signature']['prefix_generation_sha256'];assert g['signature']['prompt_sha256']==row['prompt_sha256']
            assert hashlib.sha256(payload[key]['prompt'].encode()).hexdigest()==row['prompt_sha256'];assert hashlib.sha256(payload[key]['response'].encode()).hexdigest()==hashlib.sha256(c['result']['text'].encode()).hexdigest()
            hb_sig=load(B/'canonical254/scores'/name/(key+'.json'))['signature'];assert hb_sig['generation_sha256']==sha(p)
            wg_sig=load(B/'wildguard_pair254'/(name+'_scores')/(key+'.json'))['signature'];assert wg_sig['input_sha256']==ih;checked+=1
    return checked
def main():
    p=argparse.ArgumentParser();p.add_argument('--assert-ready',action='store_true');a=p.parse_args();x=status()
    if a.assert_ready:
        assert x['full500_all13_ready'],'All13 target outputs and both judges, including alpha0, must be complete before reading'
        x['prompt_and_cache_chains_verified']=verify_prompt_chain()
    dest=B/'read_order10/all13_admission_status.json';dest.write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
if __name__=='__main__':main()
