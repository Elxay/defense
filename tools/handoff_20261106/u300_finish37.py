from u300_schedule_prepare import *
import os,sys,shlex,re
os.environ['GIT_SSH_COMMAND']='ssh -o Hostname=127.0.0.1 -o Port=18443 -o HostKeyAlias=github.com -o StrictHostKeyChecking=yes -o ConnectTimeout=15'
O=U/'followup37'
# Public aggregate only; all original text, row annotations and mapping remain private.
save(O/'blind24_review_aggregate.json',dict(utc=utc(),N=24,annotator='current Codex/ChatGPT model; shared context, not human',blinding='labels/score/ID/stratum hidden until 24 labels were saved; not an independent human blind study',sampling_population='132 selected saved internal replies; disagreement strata only',strata=[dict(stratum='score10_SORRY0',N=12,review_fulfilled=0,review_unfulfilled=12,review_uncertain=0),dict(stratum='scorelow_SORRY1',N=12,review_fulfilled=5,review_unfulfilled=1,review_uncertain=6)],uncertainty='five incomplete generic openings and one target-specific boundary; no unseen continuation inferred',not_population_accuracy=True,no_primary_cache_changes=True,private_annotation_sha256='a7b9ca5b2a80e1702c3029083140a14c4663e674b471eaeff5028616a1e684ba',blind_packet_sha256='e201eaf4b5a92e93ab0ee30e5b7e4d21e3b99a33b9d4c2f3cb810871a51039b6'))
record=R/'docs/300_ADDENDUM37_RELEASE_WATCH_RECORD.md';record.write_text('''# 追加37释放监视执行补记

R采用逐格剩余行数和已有生成/翻译耗时；规划高情景为慢20%及显式加载/判分余量，非统计上界。15分钟自动更新一次，仅元数据，不读非零标签。

首次复算尚无余卡，释放数0。为避免切换整个未完成队列，自动释放采用保守实现：某张卡的已登记T2生成和翻译全部完成，且其余五卡在60%可用率下总R和最长队列均满足截止前12小时余量时，才为该卡写admitted=true凭据。没有自然空出的卡时只报告资格，不迁移部分格。探针失败不释放。

Mistral B1校准的innet GPU0续跑，仅把原T2全局等待条件换成该卡的独立释放凭据；132条保存前缀及训练/选择规则不变，原编码/PAIR等待锁不受此改动。当前未放行，不能写成已恢复。Gemma门仍等待有资格余卡，不虚构已起作业。

监视只记录/告警截止，不杀任何作业。innet GPU1永不计入可用卡。所有正式判分继续只写缓存。
'''.rstrip()+'\n')
commit=publish([record,T/'u300_T2_watch37.py',T/'u300_collect37.py',O/'blind24_review_aggregate.json',O/'routing_execution.json'],'Record local review limits and attach metadata-only conservative T2 release watcher')
with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json');task=next(t for t in cat['tasks'] if t['id']=='Mistral_B1_calibration35');assert L(U/'ready_queue/state.json')['tasks'].get(task['id'],{}).get('state')!='running'
 old=task['requires'];task['requires']=[x for x in old if not x['path'].endswith('T2_PRIORITY_RELEASE.json')]+[dict(path=str((O/'T2_RELEASE_innet0.json').relative_to(R)),key='admitted',value=True)];save(U/'ready_queue_catalog.json',cat)
log=(O/'T2_watch/watch.log').open('a');p=subprocess.Popen([sys.executable,str(T/'u300_T2_watch37.py')],stdout=log,stderr=log,start_new_session=True);save(O/'watch_execution.json',dict(utc=utc(),commit=commit,pid=p.pid,worker_sha256=H(T/'u300_T2_watch37.py'),doc_sha256=H(record),Mistral_old_prerequisites=old,Mistral_new_prerequisites=task['requires'],initial_release_count=0))
print(json.dumps(L(O/'watch_execution.json'),indent=2))
