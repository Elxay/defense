"""Owned-child 20-request/four-hour retiming supervisor; metadata only."""
from pathlib import Path
import os,sys,subprocess,signal,time,datetime,json,hashlib,statistics
R=Path(os.environ['DEF_ROOT']);U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';D=U/'AutoDAN_build_cap512_v5';lease=Path(os.environ['DEF_LEASE_DIR'])
def L(p):return json.loads(Path(p).read_text())
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'autodan_cap512_supervisor19.json');assert H(__file__)==P['worker_sha256'];assert H(U/'S1b_AutoDAN_cap512_v5.json')==P['source_plan_sha256']
assert not list((D/'requests.private').glob('*.json')),'New timing must start from empty namespace, not resume old results'
started=L(lease/'status.json')['utc'];deadline=datetime.datetime.fromisoformat(started).timestamp()+4*3600
child=subprocess.Popen([sys.executable,str(T/'unified300_autodan_worker_cap512_v5.py'),'warmup','qwen']);save(lease/'retime_child.json',dict(utc=utc(),pid=child.pid,started_utc=started,deadline_utc=datetime.datetime.fromtimestamp(deadline,datetime.timezone.utc).isoformat()))
signals=[]
try:rc=child.wait(timeout=max(0,deadline-time.time()))
except subprocess.TimeoutExpired:
 child.send_signal(signal.SIGINT);signals.append(dict(utc=utc(),signal='SIGINT',pid=child.pid))
 try:rc=child.wait(timeout=60)
 except subprocess.TimeoutExpired:
  child.terminate();signals.append(dict(utc=utc(),signal='SIGTERM',pid=child.pid))
  try:rc=child.wait(timeout=30)
  except subprocess.TimeoutExpired:child.kill();signals.append(dict(utc=utc(),signal='SIGKILL',pid=child.pid));rc=child.wait()
rows=[L(p) for p in sorted((D/'requests.private').glob('*.json'))];n=len(rows);gpu_h=(time.time()-datetime.datetime.fromisoformat(started).timestamp())*2/3600
forecast={str(N):gpu_h*N/n for N in [300,150,75]} if n else None;eligible=[N for N in [300,150,75] if forecast and forecast[str(N)]<=150]
fails=sum(not r.get('internal_score_stop_hit',False) and r.get('iterations_completed')==150 for r in rows);censored=int(n<20 and bool(signals));tried=n+censored
mixture={str(t):{str(p):150*2/3600*(p*150*t+(1-p)*14*t) for p in [.1,1/3,.5]} for t in [90,45,30]}
save(D/'retime_result.json',dict(utc=utc(),started_utc=started,N_complete=n,N_planned=20,complete_request_ids=[r['id'] for r in rows],right_censored_requests=censored,internal_full150_no_stop=fails,internal_failure_rate_bounds=None if not tried else [fails/tried,(fails+censored)/tried],observed_request_costs=[r['resident_GPUh'] for r in rows],iterations=[r.get('iterations_completed') for r in rows],reserved_GPUh=gpu_h,forecast_by_tier=forecast,selected_warmup_N=max(eligible) if eligible else None,signals=signals,worker_returncode=rc,old_data_imported=False,old_sunk8_GPUh_remains_in_global600=True,mixture_fixed_diagnostic_only=mixture,budget_feasible=bool(eligible),next_branch='continue-new-library-after-admission' if eligible else 'external-prebuilt-adaptation-pending',main_nonzero_effects_read=False))
# Complete means timing attempt ended; it is not a20/20 marker or a frozen test library.
save(lease/'retime_attempt_finished.json',dict(utc=utc(),N_complete=n,result_sha256=H(D/'retime_result.json')))
