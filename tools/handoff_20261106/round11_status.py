from pathlib import Path
import json,datetime,subprocess,shlex,os,csv,time,argparse
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round11';P=B/'results/plain_arm';parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');args=parser.parse_args()
def load(p):
 try:return json.loads(p.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return None

def snapshot():
 now=datetime.datetime.now(datetime.timezone.utc);rows=[];controllers={}
 for label,p in [('original_twoarm',B/'results/audit/handoff_round9/pipeline_live.json'),('plain_five',O/'plain_pipeline_live.json'),('noise_B',O/'noise_controller_live.json')]:
  d=load(p)
  if d:controllers[label]=d;rows.append(dict(job=label,host='innet',gpu='CPU',pid=d['pid'],phase=d['phase'],progress='',seconds_per_unit='',heartbeat_age_s=round((now-datetime.datetime.fromisoformat(d['utc'])).total_seconds(),1)))
 for seed in range(3,8):
  source=(B/'results/audit/handoff_round10'if seed<=5 else O)/f'plain_s{seed}_live.json';d=load(source);meta=load(P/f'plain_s{seed}/metadata.json');card=2 if seed in[3,5,7]else 3
  if d:
   phase=d['phase'];n=d.get('step',40 if meta else 0);stamp=d['utc'];pid=d['pid'];speed=d.get('seconds_per_step','')
  else:phase='waiting_gpu_lease_or_prior_queue';n=0;stamp=None;pid='pending';speed=''
  if meta:phase='vector_complete';n=40
  rows.append(dict(job=f'plain_s{seed}_train',host='innet',gpu=str(card),pid=pid,phase=phase,progress=f'{n}/40',seconds_per_unit=speed,heartbeat_age_s=round((now-datetime.datetime.fromisoformat(stamp)).total_seconds(),1)if stamp else 'pending'))
 remote={}
 code="from pathlib import Path;import json;p=Path('/home/dell/Def/results/audit/handoff_round11');print(json.dumps({x.name:json.loads(x.read_text())for x in p.glob('*live.json')}))"
 try:remote=json.loads(subprocess.check_output(['ssh','node01','python3','-c',shlex.quote(code)],text=True,timeout=15))
 except Exception as e:remote={'read_error':str(e)}
 for host,files in [('innet',{p.name:load(p)for p in O.glob('*live.json')if p.name.startswith('generate_')or p.name=='judge_live.json'}),('node01',remote)]:
  for name,d in files.items():
   if not isinstance(d,dict)or'pid'not in d:continue
   n=d.get('n',d.get('n_harm',''));total=d.get('total','');progress=f'{n}/{total}'if total else str(n);gpu=d.get('physical_gpu',d.get('physical_gpus','CPU'))
   rows.append(dict(job=name.removesuffix('_live.json'),host=host,gpu=str(gpu),pid=d['pid'],phase=d['phase'],progress=progress,seconds_per_unit=d.get('seconds_per_item',''),heartbeat_age_s=round((now-datetime.datetime.fromisoformat(d['utc'])).total_seconds(),1)))
 # Explicitly expose unstarted grid and holdout stages rather than pretending training means evaluation.
 for seed in range(3,8):
  if not any(r['job']==f'generate_grid_s{seed}'for r in rows):rows.append(dict(job=f'plain_s{seed}_grid',host='node01'if seed<=5 else'innet',gpu=str(seed-3 if seed<=5 else seed-4),pid='pending',phase='not_started_waiting_all_vectors_and_original_window',progress='0/2820',seconds_per_unit='',heartbeat_age_s='pending'))
  if not any(r['job']==f'generate_full_s{seed}'for r in rows):rows.append(dict(job=f'plain_s{seed}_holdout',host='node01'if seed<=5 else'innet',gpu=str(seed-3 if seed<=5 else seed-4),pid='pending',phase='not_started_before_endpoint_plan_hash',progress='endpoint_count_pending',seconds_per_unit='',heartbeat_age_s='pending'))
 data=dict(utc=now.isoformat(),JST=(now+datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S'),rows=rows,controllers=controllers,source='live files plus completion metadata only; no holdout text/effects read');p=O/'STATUS_LATEST.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(data,indent=2)+'\n');q.replace(p)
 fields=['job','host','gpu','pid','phase','progress','seconds_per_unit','heartbeat_age_s'];p=O/'STATUS_LATEST.csv';q=p.with_suffix('.tmp')
 with q.open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 q.replace(p);lines=['# 281 — 实时队列状态','', '快照JST：'+data['JST']+'；每30秒刷新根工作区，Git报告是发布时快照。训练完成行的旧心跳年龄不表示作业卡死；pending为等待租约或前置步骤。','', '| 作业 | 节点/GPU | PID | 阶段 | 进度 | 秒/单位 | 心跳年龄s |','|---|---|---|---|---|---|---|']
 for r in rows:lines.append(f"| {r['job']} | {r['host']}/{r['gpu']} | {r['pid']} | {r['phase']} | {r['progress']} | {r['seconds_per_unit']} | {r['heartbeat_age_s']} |")
 lines+=['', '网格0/2820为6×(70攻击+400合法)，评估合法分母仍是388；留出端点数量在方案冻结前不假定为1。所有GPU任务原门禁>2000MiB拒绝，innetGPU0/1禁用。']
 p=B/'docs/281_LIVE_STATUS.md';q=p.with_suffix('.tmp');q.write_text('\n'.join(lines)+'\n');q.replace(p)
 return data
while True:
 d=snapshot()
 if not args.watch:print(json.dumps(d,indent=2));break
 phases=[v['phase']for v in d['controllers'].values()]
 if len(phases)==3 and all(x in['complete','failed','plain_incomparable','stopped_incomparable_seed']for x in phases):break
 if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,11,9,15,tzinfo=datetime.timezone.utc):break
 time.sleep(30)
