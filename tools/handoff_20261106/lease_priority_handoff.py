"""Drain the owned dispatcher and launch the pinned priority state machine."""
from pathlib import Path
import os,signal,subprocess,time
from lease_priority_support import ROOT,BASE,STATE,load,save,sha,utc,verify

def start(program):
    shell=f'''set -euo pipefail
cd {ROOT}
source night/launch.sh
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN
NOGPU=1 launch_job /home/kemove/anaconda3/envs/HZX_GLA/bin/python -u tools/handoff_20261106/{program}
'''
    with(ROOT/'logs'/('lease_launch_'+program+'.log')).open('ab',buffering=0)as log:
        p=subprocess.Popen(['bash','-s'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);p.stdin.write(shell.encode());p.stdin.close();return p.pid

def registered_identity(pid,script):
    p=Path('/proc',str(pid));assert p.exists();cmd=p.joinpath('cmdline').read_bytes().replace(b'\0',b' ').decode();assert script in cmd
    reg=(ROOT/'logs/pid_registry.txt').read_text();assert any(x.startswith(str(pid)+'|')for x in reg.splitlines()),'process must have registry evidence';return p

def main():
    verify();oldpid=1466633;before=STATE/'handoff_before.json'
    if not before.exists():
        p=registered_identity(oldpid,'prefix_controller_borrowed.py');files={str(p.relative_to(ROOT)):sha(p)for p in (BASE/'prefix254/generation.private').glob('*/*.json')};save(before,{'utc':utc(),'files':files,'old_master_pid':oldpid})
        subprocess.run(['bash','night/safe_kill.sh',str(oldpid)],cwd=ROOT,check=True)
    while Path('/proc',str(oldpid)).exists():save(STATE/'handoff_live.json',{'utc':utc(),'pid':os.getpid(),'phase':'waiting_owned_prefix_batches_to_drain','old_master_pid':oldpid});time.sleep(5)
    original=load(before)['files'];assert all(sha(ROOT/p)==value for p,value in original.items())
    retired=[];old480=BASE/'pair_priority480_live.json'
    if old480.exists():
        pid=load(old480)['pid']
        if Path('/proc',str(pid)).exists():registered_identity(pid,'pair500_priority480.py');subprocess.run(['bash','night/safe_kill.sh',str(pid)],cwd=ROOT,check=True);retired.append(pid)
    state=load(BASE/'wildguard/conditions_queue_live.json');wgpid=state['pid'];p=registered_identity(wgpid,'wildguard_conditions_queue.py');assert state['phase']=='waiting_complete_target_outputs','do not suspend a dispatched classifier batch'
    held={'utc':utc(),'pid':wgpid,'start_ticks':p.joinpath('stat').read_text().split(') ',1)[1].split()[19],'phase_before':state['phase'],'reason':'PAIR WildGuard priority; not an external process'};save(STATE/'held_wjb_WG_queue.json',held);os.kill(wgpid,signal.SIGSTOP)
    launches={name:start(name)for name in ['lease_priority_controller.py','lease_auxiliary_finish_queue.py','resume_wjb_wg_after_pair.py']}
    receipt={'utc':utc(),'retired_old_master':oldpid,'retired480_pids':retired,'unchanged_prefix_rows_verified':len(original),'held_owned_WJB_WG_pid':wgpid,'launchers':launches,'implementation_sha256':sha(BASE/'lease_priority_implementation.json'),'effects_read':False};save(STATE/'handoff_complete.json',receipt)
    with(ROOT/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{utc()} LEASE_PRIORITY_HANDOFF_COMPLETE SHA={sha(STATE/"handoff_complete.json")} old prefix files unchanged{len(original)}; old480 retired; WJB WG auxiliary CPU intentionally held until PAIR WG completion; no external process signals.\n')
    print(__import__('json').dumps(receipt))

if __name__=='__main__':main()
