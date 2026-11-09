"""Drain only the registered owned dispatcher; preserve every existing generated row."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';S=B/'lease_priority';OLD=1886520
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
    q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');os.replace(q,p)
def pulse(phase,**kw):put(S/'v3_handoff_live.json',{'utc':utc(),'pid':os.getpid(),'phase':phase,**kw})
def main():
    pub=json.loads((B/'gpu0_day_authorization.json').read_text());assert sha(R/'tools/handoff_20261106/lease_priority_controller_v3.py')==pub['controller_sha256'];assert sha(R/'tools/handoff_20261106/wjb_tail_priority_worker_v2.py')==pub['workers_sha256']['wjb_tail_priority_worker_v2.py'];assert not(S/'v3_handoff_complete.json').exists()
    cmd=Path('/proc',str(OLD),'cmdline').read_bytes();assert b'lease_priority_controller_v2.py'in cmd and b'controller_v3'not in cmd;assert any(l.startswith(str(OLD)+'|')for l in(R/'logs/pid_registry.txt').read_text().splitlines())
    pulse('hashing_existing_outputs');files=list((B/'prefix254/generation.private').glob('*/*.json'))+[p for kind in ['harmful','public'] for name in ['old_s0','SYS_A','SYS_B'] for p in (B/'public255'/f'{kind}.private'/name).glob('*/*.json')];hashes={str(p.relative_to(R)):sha(p)for p in files};manifest=S/'v3_handoff_existing_files.private.json';put(manifest,hashes)
    pulse('draining_owned_old_dispatcher',files=len(hashes));put(S/'hb_yield.json',{'utc':utc(),'reason':'frozen addendum11 dispatcher handoff, no numerical change'});result=subprocess.run(['bash',str(R/'night/safe_kill.sh'),str(OLD)],cwd=R,capture_output=True,text=True);assert result.returncode==0,result.stdout+result.stderr
    start=time.monotonic()
    while Path('/proc',str(OLD)).exists():
        if time.monotonic()-start>900:raise RuntimeError('owned controller did not drain within15min; do not launch replacement')
        pulse('draining_owned_old_dispatcher',wait_seconds=time.monotonic()-start);time.sleep(3)
    pulse('checking_existing_output_hashes');assert all(sha(R/n)==h for n,h in hashes.items()),'Existing generation bytes changed across handoff'
    shell='set -euo pipefail\ncd /data/HZX/Def\nsource night/launch.sh\nexport NOGPU=1 DEVICE=cpu\nlaunch_job /home/kemove/anaconda3/envs/HZX_GLA/bin/python -u tools/handoff_20261106/lease_priority_controller_v3.py\n'
    log=(R/'logs/lease_priority_controller_v3.log').open('ab',buffering=0);p=subprocess.Popen(['bash','-s'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);p.stdin.write(shell.encode());p.stdin.close();out={'utc':utc(),'retired_controller':OLD,'new_launcher_pid':p.pid,'unchanged_existing_files':len(hashes),'unchanged_files_manifest_sha256':sha(manifest),'day_authorization_sha256':sha(B/'gpu0_day_authorization.json'),'effects_read':False};put(S/'v3_handoff_complete.json',out);pulse('complete',**{'new_launcher_pid':p.pid})
    for n in ['PREREG_LOG.txt','OPS_LOG.txt']:
        with(R/'docs'/n).open('a')as f:f.write(f'{out["utc"]} LEASE_PRIORITY_V3_STARTED old={OLD} launcher={p.pid} unchanged_files={len(hashes)} manifest_SHA={sha(manifest)} receipt_SHA={sha(S/"v3_handoff_complete.json")} no numerical source change/no effect read.\n')
    print(json.dumps(out),flush=True)
if __name__=='__main__':main()
