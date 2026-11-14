from u300_schedule_prepare import *
import os,shlex
os.environ['GIT_SSH_COMMAND']='ssh -o Hostname=127.0.0.1 -o Port=18443 -o HostKeyAlias=github.com -o StrictHostKeyChecking=yes -o ConnectTimeout=15'
O=U/'followup37';tid='T2translate36_qwen_translate-ta_s3';s=L(U/'ready_queue/state.json')['tasks'][tid];assert s['state']=='failed' and s['exit']['returncode']==127
raw=subprocess.check_output(['ssh','node01','cat /home/dell/Def/results/audit/unified300/queue_jobs/'+s['job_dir']+'/worker.log'],text=True)
assert 'DEF_FROZEN_GIT_REV=' in raw
code="from pathlib import Path; p=Path('/home/dell/Def/results/audit/unified300/language_processed36/qwen_translate-ta_s3/processed.private');print(len(list(p.glob('*.json'))))";N=int(subprocess.check_output(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(code)],text=True));assert N==0
doc=R/'docs/300_ADDENDUM37_DISPATCH_CONFORMITY.md';doc.write_text('''# 追加37调度执行符合性补记

03:40:49Z一次Qwen ta s3新站点翻译启动，在模型加载前EXIT127。原因是执行代理重排时假定所有argv都有env前缀，覆盖了无env前缀作业的bash包装路径。不是GPU/OOM或数值门失败；无译文产生，失败租约和日志保留，不覆盖。

修复只把所有未启动翻译argv规范为env + 固定Git版本 + bash日志包装 + 相同数值plan/worker/格ID，分别选站点Python与物理卡；运行中的定义保持不变。旧失败task保留failed，另建显式supersedes的同格重试task，不重置历史状态。新卡依旧必须先过原B1参考20。原生成、译文、输入包与数值配置均不变。
'''.rstrip()+'\n')
save(O/'dispatch_failure37.json',dict(utc=utc(),failed_task=tid,failed_job=s['job_dir'],returncode=127,private_rows_produced=N,worker_log=raw,root_cause='argv prefix shape assumption in routing mutator; bash wrapper replaced by environment assignment',model_was_not_loaded=True,old_failure_retained=True))
commit=publish([doc,O/'dispatch_failure37.json',Path(__file__)],'Record and repair pre-load translation dispatch argument error without changing numerical execution')
reg={c['cell_id']:c for c in L(U/'T2_processing37_registry.json')['cells']}
with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json');state=L(U/'ready_queue/state.json')['tasks'];fixed=[];retry=None
 for t in cat['tasks']:
  if not t['id'].startswith('T2translate36_'):continue
  status=state.get(t['id'],{}).get('state','pending')
  if status in ['running','done']:continue
  if status=='failed' and t['id']!=tid:raise RuntimeError('Unexpected failed translation task; inspect first')
  key=t['id'].removeprefix('T2translate36_');c=reg[key];a=['env','DEF_FROZEN_GIT_REV='+commit,'bash','{ROOT}/tools/handoff_20261106/u300_logged_job31.sh','{ROOT}','results/audit/unified300/language_nonzero36_execution.json',str(c['gpu']),'/data/ray/env/bin/python' if c['site']=='node01' else '/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/u300_language_nonzero36.py',key]
  if status=='failed':
   retry=copy.deepcopy(t);retry.update(id='T2translate37_'+key,argv=a,supersedes_failed_task=tid);continue
  t['argv']=a;fixed.append(t['id'])
 assert retry is not None and not any(t['id']==retry['id'] for t in cat['tasks']);cat['tasks'].append(retry);save(U/'ready_queue_catalog.json',cat)
save(O/'dispatch_repair_execution.json',dict(utc=utc(),commit=commit,doc_sha256=H(doc),N_pending_argv_normalized=len(fixed),retry_task_id=retry['id'],old_failure_retained=True,numerical_worker_sha256=H(T/'u300_language_nonzero36.py')));print(json.dumps(L(O/'dispatch_repair_execution.json')))
