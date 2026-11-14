from u300_schedule_prepare import *
import os,sys,signal
os.environ['GIT_SSH_COMMAND']='ssh -o Hostname=127.0.0.1 -o Port=18443 -o HostKeyAlias=github.com -o StrictHostKeyChecking=yes -o ConnectTimeout=15'
O=U/'followup38';old=T/'u300_replay38.py';s=old.read_text();s=s.replace('group=sys.argv[1]','group_name=sys.argv[1]').replace("z['group']==group)","z['group']==group_name)").replace("/'replays'/group;","/'replays'/group_name;").replace('family=group,','family=group_name,').replace("'order38_'+group)","'order38_'+group_name)").replace("U/'followup38/replay_execution.json'","U/'followup38/replay_execution_v2.json'")
w=T/'u300_replay38_v2.py';w.write_text(s);compile(s,str(w),'exec');plan=L(O/'replay_execution.json');plan.update(utc_frozen=utc(),worker_sha256=H(w),parent_plan_sha256=H(O/'replay_execution.json'),change='Use group_name for metadata; numerical loop and core unchanged');save(O/'replay_execution_v2.json',plan)
watchold=T/'u300_T2_watch38b.py';q=watchold.read_text();a="rp=any(state.get(prefix+x['group'],{}).get('state')!='done' for x in groups for prefix in ['replay38_','judge38_'])";b="rp=any(not (U/'followup38/replays'/x['group']/'complete.json').exists() or state.get('judge38_'+x['group'],{}).get('state')!='done' for x in groups)";assert a in q;q=q.replace(a,b)
a="any(state.get(tid,{}).get('state')!='done' for tid in ['Gemma_zero20_window38','replay38_TAP_llama_first88','judge38_TAP_llama_first88'])";b="(state.get('Gemma_zero20_window38',{}).get('state')!='done' or not (U/'followup38/replays/TAP_llama_first88/complete.json').exists() or state.get('judge38_TAP_llama_first88',{}).get('state')!='done')";assert a in q;q=q.replace(a,b);watch=T/'u300_T2_watch38c.py';watch.write_text(q);compile(q,str(watch),'exec')
doc=R/'docs/300_ADDENDUM38_REPLAY_PACKAGING_CONFORMITY.md';doc.write_text('''# 追加38重放收尾符合性补记

PAIR末候选220条已完整生成、零向量门和逐批指标齐全，收尾时group字符串被批列表同名变量覆盖，构造wave名发生TypeError。不是目标生成失败。原worker、plan哈希、输出文件及EXIT=1保留，不伪装EXIT=0。

已运行的旧worker不热改、不杀。独立CPU恢复器仅在确认同一收尾TypeError、全N原子记录、原plan/提示/基础指令/来源哈希、零范数/注入次数、回复SHA、完整批指标和20门后创建判分输入与完成回执。回执明确generation_worker_exit=1和postprocessing_recovered=true；不重新生成、不读标签。

尚未启动的Qwen首位78使用仅改元数据变量名的v2副本，数值核心、提示清单、B4、2400、zero20不变；原执行计划保留，新计划绑定v2哈希。预算监视以验证完成回执和判分任务为准，不把已恢复的失败状态当作永久未完成，也不改旧失败记录。
'''.rstrip()+'\n')
commit=publish([doc,w,O/'replay_execution_v2.json',watch,T/'u300_finalize_replays38.py',Path(__file__)],'Preserve replay outputs and original failure exits; recover packaging with explicit provenance and fix pending metadata variable')
with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json');tid='replay38_TAP_qwen_first78';assert L(U/'ready_queue/state.json')['tasks'].get(tid,{}).get('state','pending')=='pending';t=next(t for t in cat['tasks'] if t['id']==tid);t['argv']=[x.replace('replay_execution.json','replay_execution_v2.json').replace('u300_replay38.py','u300_replay38_v2.py') for x in t['argv']];save(U/'ready_queue_catalog.json',cat)
log=(O/'packaging_recovery.log').open('a');p=subprocess.Popen([sys.executable,str(T/'u300_finalize_replays38.py')],stdout=log,stderr=log,start_new_session=True);pid=L(U/'followup37/T2_watch/live.json')['pid'];assert b'u300_T2_watch38b.py' in (Path('/proc')/str(pid)/'cmdline').read_bytes();os.kill(pid,signal.SIGTERM);log2=(O/'T2_watch38c.log').open('a');n=subprocess.Popen([sys.executable,str(watch)],stdout=log2,stderr=log2,start_new_session=True);save(O/'packaging_repair_execution.json',dict(utc=utc(),commit=commit,CPU_finalizer_pid=p.pid,new_budget_watch_pid=n.pid,doc_sha256=H(doc),numerical_outputs_regenerated=False,original_worker_exit_retained=True));print(json.dumps(L(O/'packaging_repair_execution.json')))
