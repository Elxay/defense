from pathlib import Path
import ast,datetime,json,os,signal,subprocess,time
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
source=T/'u300_score_dispatcher.py';tree=ast.parse(source.read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='hb_window_allowed')
env={'datetime':datetime};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),env);f=env['hb_window_allowed']
t=datetime.datetime(2026,11,11,13,tzinfo=datetime.timezone.utc)
assert not f({},26399,40000,t) and f({},26400,40000,t)
assert f({},440,52800,t) and not f({},0,52800,t)
assert not f({'score_HB_old':{'started_utc':'2026-11-11T12:51:24+00:00'}},26400,50000,t)
assert f({'score_HB_old':{'started_utc':'2026-11-11T12:51:24+00:00'}},26400,50000,t+datetime.timedelta(hours=3))
commit=publish([source,Path(__file__)], 'Enforce daily backlog-gated HarmBench windows and WG-before-translation dependency')
C=U/'ready_queue_catalog.json';cat=L(C);S=L(U/'ready_queue/state.json')['tasks']
for task in cat['tasks']:
 if task['id']=='language_alpha0_reply_preprocessing_v2_CF':
  assert S.get(task['id'],{}).get('state')!='running';task['priority']=7
  task['requires'].append(dict(path='results/audit/unified300/WG_first_wave_released.json',key='released',value=True))
 if task['id'].startswith('score_WG_') and task['id']!='score_WG_0001' and S.get(task['id'],{}).get('state')!='running':
  task['requires'].append(dict(path='results/audit/unified300/language_processed_alpha0_v1/complete_CF.json'))
save(C,cat)
pid=L(U/'score_dispatch_state.json')['pid'];assert b'u300_score_dispatcher.py' in Path('/proc',str(pid),'cmdline').read_bytes()
os.kill(pid,signal.SIGTERM);time.sleep(1)
log=open(R/'logs/u300_score_dispatcher.log','a')
p=subprocess.Popen(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(source)],stdout=log,stderr=log,start_new_session=True)
save(U/'stage_window_rule_activation.json',dict(utc=utc(),commit=commit,cpu_dispatcher_pid=p.pid,
 policy_boundary_assertions_passed=6,existing_HB_window_preserved=True,no_GPU_worker_stopped=True))
print(json.dumps(dict(commit=commit,pid=p.pid,existing_HB_window='continues; counts as Nov11 window')))
