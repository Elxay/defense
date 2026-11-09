"""Wait for all contextual target outputs, then audit token lengths only on CPU."""
from pathlib import Path
import datetime,hashlib,json,os,sys,time
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';O=B/'argument_revision_20261109';NAMES=['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');os.replace(q,p)
def main():
    rows=json.loads((B/'rows.private.json').read_text());ids=[x['id']for x in rows if x['layer']=='contextual'];assert len(ids)==100;O.mkdir(exist_ok=True);deadline=datetime.datetime(2026,11,11,15,tzinfo=datetime.timezone.utc);script=R/'tools/handoff_20261106/audit_pair254_contextual_length.py';source=script.read_text();assert source.count("'contextual_length_audit.json'")==1;bound=source.replace("'contextual_length_audit.json'","'contextual_all1300_length_audit.json'")
    while datetime.datetime.now(datetime.timezone.utc)<deadline:
        counts={n:sum((B/'prefix254/generation.private'/n/(k+'.json')).is_file()for k in ids)for n in NAMES};save(O/'contextual_full_observer_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'waiting_full1300','counts':counts,'outcome_labels_read':False})
        if all(n==100 for n in counts.values()):
            scope={'__name__':'cpu_full_contextual_audit','__file__':str(script)};exec(compile(bound,str(script),'exec'),scope);scope['main']();p=B/'tail_contextual_followup_20261109/contextual_all1300_length_audit.json';x=json.loads(p.read_text());assert x['measured_generated_inputs']==1300 and all(v['n']==100 for v in x['per_condition'].values());receipt={'utc':utc(),'file':str(p.relative_to(R)),'sha256':sha(p),'source_audit_script_sha256':sha(script),'observer_sha256':sha(Path(__file__)),'total':1300,'max_tokens':x['max_tokens'],'over1900':x['over1900'],'over2048':x['over2048'],'outcome_labels_read':False};save(O/'contextual_full1300_receipt.json',receipt)
            with(R/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{utc()} CONTEXTUAL_FULL1300_LENGTH_AUDIT SHA={sha(p)} max={x["max_tokens"]} >1900={x["over1900"]} >2048={x["over2048"]} metadata only/no outcome labels.\n')
            save(O/'contextual_full_observer_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'complete_full1300_length_only','receipt_sha256':sha(O/'contextual_full1300_receipt.json'),'outcome_labels_read':False});return
        time.sleep(60)
    save(O/'contextual_full_observer_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'cutoff_incomplete1300','outcome_labels_read':False})
if __name__=='__main__':main()
