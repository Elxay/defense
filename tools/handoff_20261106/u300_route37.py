from u300_schedule_prepare import *
import os,signal,shlex,sys,time
os.environ['GIT_SSH_COMMAND']='ssh -o Hostname=127.0.0.1 -o Port=18443 -o HostKeyAlias=github.com -o StrictHostKeyChecking=yes -o ConnectTimeout=15'
O=U/'followup37';b=L(O/'T2_budget_release37.json');old=U/'T2_processing36_registry.json';r=L(old);state=L(U/'ready_queue/state.json')['tasks']
changes=[]
for c in r['cells']:
 lane=b['proposed_routes'][c['cell_id']];site,gpu=lane.split(':');tid='T2translate36_'+c['cell_id'];active=state.get(tid,{}).get('state')=='running'
 if active:assert (site,int(gpu))==(c['site'],c['gpu']), 'Never move an active whole-cell lease'
 if (site,int(gpu))!=(c['site'],c['gpu']):changes.append(dict(cell_id=c['cell_id'],old_site=c['site'],old_gpu=c['gpu'],site=site,gpu=int(gpu)))
 c.update(site=site,gpu=int(gpu))
r.update(utc_frozen=utc(),supersedes_scheduling_only_sha256=H(old),numeric_execution_plan_unchanged_sha256=H(U/'language_nonzero36_execution.json'),routing_changes=changes,partially_processed_cells_pinned=True)
rp=U/'T2_processing37_registry.json';save(rp,r)
s=(T/'u300_T2_packetizer36_v2.py').read_text().replace("O=U/'followup36';P=L(U/'T2_processing36_registry.json');done=set()","O=U/'followup36';O37=U/'followup37';P=L(U/'T2_processing37_registry.json');done=set()")
needle="  comp=U/'language_processed36'/key/'complete.json';wr=O/'T2_score_ready'/f'{key}.json'"
insert="""  sr=O37/'T2_site_ready'/f'{key}.json'
  if ready.exists() and not sr.exists():
   ip=U/'language_nonzero36_inputs'/f'{key}.private.json';bp=U/'language_nonzero36_bindings'/f'{key}.json';assert H(ip)==L(bp)['inputs_sha256']
   if c['site']=='node01':
    for path in [ip,bp]:
     dest='/home/dell/Def/'+str(path.relative_to(R));subprocess.run(['ssh','node01','mkdir -p '+shlex.quote(str(Path(dest).parent))],check=True,capture_output=True);subprocess.run(['scp',str(path),'node01:'+dest],check=True,capture_output=True)
   save(sr,dict(utc=utc(),ready=True,site=c['site'],gpu=c['gpu'],inputs_sha256=H(ip),numeric_execution_sha256=H(U/'language_nonzero36_execution.json'),scheduling_registry_sha256=H(U/'T2_processing37_registry.json')))
"""+needle
assert needle in s;s=s.replace(needle,insert);s=s.replace("O/'T2_packetizer_live.json'","O37/'T2_packetizer_live.json'");worker=T/'u300_T2_packetizer37.py';worker.write_text(s);compile(s,str(worker),'exec')
doc=R/'docs/300_ADDENDUM37_EXECUTION_RECORD.md';doc.write_text('''# 追加37执行记录：边界读核、自重复、六条件与T2分流

本文件是追加37的执行补记；原37及原36不覆写。仅发布中性聚合、代码和哈希；24条全文、映射、逐条标注保持私有，不入git。

- 24条已在解盲前保存模型标注：5履行、13未履行、6边界/截断不足。解盲后高分/SORRY未履行层12/12明确未履行；低分/SORRY履行层5履行、1目标漂移未履行、6不确定。该分歧抽样不是总体准确率，也不是人工校准；不改任何主判官、选择或闸门。
- 同132条末候选内部回复的两个新进程重复均104/132、INVALID0；逐条标签和原始判文完全一致。与此前264混合批比较均只有ID108不同。两次相同条件重复没有翻转；历史混合批的1行差不能据此称随机噪声，批组成/调用环境仍可能有影响，尚无因果归因。
- 原始指令槽位逐条查验10个波次、1134条：全部为基础英文原指令，非改写对抗提示。没有目标漂移到判官指令槽。
- docs/300和已冻结S1a均明文六条件，当前Mistral沿用六条件；旧#16五条件起步被统一SORRY方案替换。49720=19*6*440-440；若改五条件才是41360，当前没有作此范围修改。
- T2快照03:34–03:37Z的剩余估计：生成49.99、翻译93.85、加载/参考2.00、SORRY及加载2.00，共147.84卡时；另按行速慢20%给规划高情景176.61卡时。这不是统计上界。距截止59.39小时，扣12小时留47.39；按60%可用率，六卡高情景需49.06小时，尚不满足释放线，五卡需58.87小时。不用乐观点强行释放。Mistral B1、Gemma门仍待满足条件的余卡；不误写为已恢复。
- 当前原队列把全部Llama翻译压在node01 GPU0，必须分流。仅重排尚未开始、无部分译文的整格；已有Llama ml s3译文保留node01 GPU0。新调度登记逐格固定站点/卡；每张新卡自动过原B1参考20再处理，数值worker、权重、模板、解码和上限不变。参考失败则停，不换链。输入包必须在新站点就绪后才放行。原36登记保留，37只取代调度映射。
- 平衡后的点估计各卡剩余负载23.48–24.84卡时（不含均摊加载/评分），不是ETA保证。原节点/卡的生成路径不搬移；只分流未开始翻译。R与每卡队列在执行后重新核对，不读取非零标签。
'''.rstrip()+'\n')
commit=publish([doc,rp,worker,O/'T2_budget_release37.json',O/'T2_metadata_snapshot.json',O/'judge_selfrepeat_results.json',T/'u300_extract_last37.py'],'Record blinded review aggregates and isolated judge repeats; freeze whole-cell T2 translation balancing')
# Stop only the superseded CPU packetizer, never a GPU worker or queue controller.
live=L(U/'followup36/T2_packetizer_live.json');pid=live['PID'];cmd=(Path('/proc')/str(pid)/'cmdline').read_bytes();assert b'u300_T2_packetizer36_v2.py' in cmd;os.kill(pid,signal.SIGTERM)
for _ in range(30):
 if not (Path('/proc')/str(pid)).exists():break
 time.sleep(.1)
with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json');current=L(U/'ready_queue/state.json')['tasks'];by={c['cell_id']:c for c in r['cells']};modified=[]
 for t in cat['tasks']:
  if not t['id'].startswith('T2translate36_'):continue
  key=t['id'].removeprefix('T2translate36_');c=by[key]
  if current.get(t['id'],{}).get('state')=='running':
   assert t['site']==c['site'] and t['gpus']==[c['gpu']];continue
  assert current.get(t['id'],{}).get('state') not in ['done','failed']
  t['site']=c['site'];t['gpus']=[c['gpu']];a=t['argv'];ix=a.index('results/audit/unified300/language_nonzero36_execution.json');a[ix+1]=str(c['gpu']);a[ix+2]='/data/ray/env/bin/python' if c['site']=='node01' else '/home/kemove/anaconda3/envs/HZX_GLA/bin/python';a[1]='DEF_FROZEN_GIT_REV='+commit
  t['requires']=[dict(path=str((O/'T2_site_ready'/f'{key}.json').relative_to(R)),key='ready',value=True),dict(path=str((O/'T2_site_ready'/f'{key}.json').relative_to(R)),key='site',value=c['site'])];modified.append(t['id'])
 save(U/'ready_queue_catalog.json',cat)
log=(O/'T2_packetizer37.log').open('a');p=subprocess.Popen([sys.executable,str(worker)],stdout=log,stderr=log,start_new_session=True)
save(O/'routing_execution.json',dict(utc=utc(),commit=commit,execution_doc_sha256=H(doc),registry_sha256=H(rp),packetizer_sha256=H(worker),stopped_CPU_packetizer_pid=pid,new_CPU_packetizer_pid=p.pid,N_changed_routes=len(changes),N_updated_pending_task_definitions=len(modified),GPU_workers_stopped=False,active_partial_translation_cell_unmoved=True,spare_cards_released=0,reason='Conservative high scenario does not meet twelve-hour reserve rule'))
print(json.dumps(L(O/'routing_execution.json'),indent=2))
