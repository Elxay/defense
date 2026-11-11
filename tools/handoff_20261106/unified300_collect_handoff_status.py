from pathlib import Path
import json,datetime,subprocess,hashlib,collections
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def collect(base):
 u=Path(base)/'results/audit/unified300'
 d={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'date_u':subprocess.check_output(['date','-u','+%Y-%m-%d %H:%M:%S UTC'],text=True).strip()}
 for k,q in [('gpu','index,uuid,memory.used,memory.total,utilization.gpu'),('apps','gpu_uuid,pid,used_gpu_memory')]:
  flag='--query-gpu=' if k=='gpu' else '--query-compute-apps='
  d[k]=subprocess.run(['nvidia-smi',flag+q,'--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.strip()
 d['counts']={};d['completed']={};d['live']={};d['gates']={}
 local_site='node01' if str(base).startswith('/home/dell')else'innet';numerical_plan=json.loads((u/'ready_generation_plan.json').read_text())
 for root in ['static_alpha0','language_alpha0','ready_generated']:
  p=u/root
  pattern='*/*/*/generation.private' if root=='ready_generated' else '*/*/generation.private'
  for folder in p.glob(pattern):
   if root=='ready_generated':
    model,family,condition=folder.parent.relative_to(p).parts
    if numerical_plan['models'][model]['families'][family]['home_site']!=local_site:continue
   key=str(folder.parent.relative_to(u));d['counts'][key]=len(list(folder.glob('*.json')))
   for fn in ['complete.json','generation_complete.json']:
    z=folder.parent/fn
    if z.exists():
     x=json.loads(z.read_text());d['completed'][key]={'sha256':H(z),**{k:x[k] for k in ['utc','N','generation_seconds','rows_per_hour'] if k in x}}
 for p in list((u/'queue_jobs').glob('*/live.json'))+list((u/'language_alpha0').glob('*/live.json')):
  x=json.loads(p.read_text());x.setdefault('model',p.parent.name) if 'language_alpha0' in str(p)else None;d['live'][str(p.relative_to(u))]={k:x[k] for k in ['utc','pid','model','family','condition','phase','N','done','saved','N_saved','heartbeat_utc'] if k in x}
 for rel in ['PAIR_execution_gate_v2/llama/target_zero20.json','PAIR_execution_gate_v2/llama/complete.json','PAIR_execution_gate_v2/complete.json','PAIR_pilot/llama/timing_complete.json']:
  p=u/rel
  if p.exists():
   x=json.loads(p.read_text());d['gates'][rel]={'sha256':H(p),**{k:v for k,v in x.items() if k not in ['pairs','histories','outputs','prompts','private_rows']}}
 d['pilot_saved']=len(list((u/'PAIR_pilot/llama').glob('rows.private/*.json')))
 return d
if __name__=='__main__':
 d={'innet':collect(R)}
 src=Path(__file__).read_text();remote=src[:src.index("if __name__=='__main__':")]+"print(json.dumps(collect('/home/dell/Def')))\n"
 p=subprocess.run(['ssh','node01','/data/ray/env/bin/python -'],input=remote,capture_output=True,text=True,check=True);d['node01']=json.loads(p.stdout)
 state=json.loads((U/'ready_queue/state.json').read_text());d['queue']={k:state[k] for k in ['utc','pid','catalog_sha256','ready','idle_seconds','gang_reservations'] if k in state};d['queue']['tasks']={k:v for k,v in state['tasks'].items() if v['state'] in ['running','failed']}
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=U/'status_snapshots'/stamp;out.mkdir(parents=True,exist_ok=False)
 j=out/'metadata.json';j.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 lines=['# 当前运行快照','',f"date -u: {d['innet']['date_u']}；node01: {d['node01']['date_u']}",'','只读PID、进度、资源及门检元数据；未读取主测试标签或效应。','', '| 节点/卡 | 显存 MiB | 利用率 | 计算PID | 项目/任务 |','|---|---:|---:|---|---|']
 for site in ['innet','node01']:
  x=d[site]; apps=collections.defaultdict(list)
  for row in x['apps'].splitlines():
   a=[s.strip() for s in row.split(',')]
   if len(a)==3:apps[a[0]].append(a[1])
  live={str(v.get('pid')):v for v in x['live'].values()}
  for row in x['gpu'].splitlines():
   a=[s.strip() for s in row.split(',')];ids=apps[a[1]];jobs=[]
   for pid in ids:
    y=live.get(pid,{});job='/'.join(str(y[k]) for k in ['model','family','condition','phase'] if k in y)
    if any(str(v.get('pid'))==pid and 'PAIR' in k for k,v in x['live'].items()):job='PAIR 正式控制器验收/计时'
    if site=='innet' and a[0]=='1':job='外部项目；排除调度'
    jobs.append(job or '未匹配已登记live，需核对')
   lines.append(f"| {site}/{a[0]} | {a[2]}/{a[3]} | {a[4]}% | {','.join(ids) or '—'} | {'; '.join(jobs) or '空闲/无compute上下文'} |")
 lines+=['','## 保存行数（按生成home节点，镜像不重复计数）','', '| 节点 | 缓存 | 已保存 | 正常完成标记 |','|---|---|---:|---|']
 for site in ['innet','node01']:
  for k,v in sorted(d[site]['counts'].items()):lines.append(f"| {site} | {k} | {v}/440 | {'有' if k in d[site]['completed'] else '无'} |")
 lines+=['','Llama translate-ml 已存440但3GiB资源断言失败，保留为阻塞，不计正常完成。node01 ta/mr在PAIR双卡高优先级窗口按批边界暂停，检查点SHA与续跑核对记录由队列保存。','',f"队列PID {state['pid']}；就绪任务 {len(state['ready'])}；外部innet GPU1不参与。",'','桌面通知被Windows脚本策略阻止；远端15分钟告警日志/控制台有效，未绕过策略。']
 m=out/'status.md';m.write_text('\n'.join(lines)+'\n');(U/'latest_status_snapshot.json').write_text(json.dumps({'utc':d['innet']['utc'],'path':str(out.relative_to(R)),'metadata_sha256':H(j),'status_sha256':H(m)},indent=2)+'\n')
 print(str(out));print(m.read_text());print('status_sha256',H(m))
