"""Restore the explicitly paused owned WJB WG CPU queue after PAIR WG completes."""
from pathlib import Path
import os,signal,time
from lease_priority_support import BASE,STATE,load,save,utc,verify

def main():
    verify();held=load(STATE/'held_wjb_WG_queue.json');pid=held['pid']
    while True:
        p=BASE/'wildguard_pair254/queue_live.json';phase=load(p).get('phase') if p.exists() else None
        save(STATE/'WJB_WG_hold_live.json',{'utc':utc(),'pid':os.getpid(),'held_worker':pid,'reason':'PAIR WG priority','PAIR_WG_phase':phase,'effects_read':False})
        if phase=='all_conditions_complete_no_effect_read':break
        time.sleep(15)
    proc=Path('/proc',str(pid))
    if proc.exists():
        assert proc.joinpath('stat').read_text().split(') ',1)[1].split()[19]==held['start_ticks'];assert 'wildguard_conditions_queue.py' in proc.joinpath('cmdline').read_bytes().decode();os.kill(pid,signal.SIGCONT)
    save(STATE/'WJB_WG_resumed_after_PAIR.json',{'utc':utc(),'original_pid':pid,'identity_verified':True,'effects_read':False})

if __name__=='__main__':main()
