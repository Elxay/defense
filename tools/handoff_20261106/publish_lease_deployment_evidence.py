"""Publish only operational counts/hashes; leave all new outcome caches private."""
from pathlib import Path
import datetime,fcntl,hashlib,json,re,shutil,subprocess

R=Path('/data/HZX/Def');B=R/'results/audit/pair500';S=B/'lease_priority';O=B/'lease_priority_followup_20261109/deployment';G=R/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def safe(x):
    if isinstance(x,dict):
        assert not({'text','response','prompt','task','generation'}&set(x))
        for v in x.values():safe(v)
    elif isinstance(x,list):
        for v in x:safe(v)
def main():
    paths=sorted(O.glob('snapshot_*.json'));assert paths
    source=paths[-1];x=load(source);safe(x);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    caught=x['first_caught_up'];windows=x['HB_windows']
    lines=['# 租约调度部署与实测状态','',f'记录UTC {x["utc"]}；JST {x["jst"]}。本报告只采集进度与生成耗时，不读取PAIR500的新有害标签或条件效应。','',
           '追加#9先冻结并push，之后发布实现哈希，最后在04:17:42.581765 UTC完成控制器交接。旧480行控制器已停；4763个交接前生成文件哈希未变。PAIR租约优先，低优先级单条生成在行边界、公开侧在原batch8边界让出。GPU0仍在18:00 JST让卡，GPU1不属于本项目。','',
           f'当前主调度PID {x["scheduler_pid"]}，phase={x["phase"]}，心跳年龄{x["heartbeat_age_seconds"]:.1f}秒。',
           '当前租约（launcher_PID为启动进程，非模型worker PID）：'+json.dumps(x['jobs'],ensure_ascii=False),
           f'PAIR搜索{x["PAIR_search"]["rows"]}/500，worker PID {x["PAIR_search"]["worker_pid"]}，历史OOM重启计数1。累计{x["PAIR_search"]["mean_seconds_per_row"]:.2f}秒/行；不计未来中断的累计速率ETA UTC {x["PAIR_search"]["eta_utc_no_future_interruptions"]}。','']
    if caught:lines +=[f'首次实测积压清空：UTC {caught["utc"]}，该时点已接纳{caught["source_rows"]}行，13条件覆盖均相同。其后搜索继续新增行，所以清空不是搜索完成，也不代表后续永无积压。',f'清空记录SHA256 {x["first_caught_up_sha256"]}。','']
    else:lines +=['截至本快照未观测到13条件同时追平；不以ETA代替实际清空时间。','']
    lines+=['| 条件 | 前缀已生成行数 | 实测完成批次数 | 行数 | 净生成秒/行 | 含启动墙钟秒/行 | 含启动行/小时 |','|---|---:|---:|---:|---:|---:|---:|']
    for n,v in x['prefix_coverage'].items():
        z=x['prefix_measured_rates'].get(n)
        if z:lines.append(f'| {n} | {v} | {z["completed_batches"]} | {z["rows"]} | {z["net_seconds_per_row"]:.3f} | {z["wall_seconds_per_row"]:.3f} | {z["wall_rows_per_hour"]:.1f} |')
    lines+=['','实测速率来源是已完成任务，不是整集合外推；alpha0含很多单行重载，不能与50行任务直接比较。加载时间中位数约8.3–8.6秒，墙钟口径还包含写盘。不同条件输出长短与批次组成不同，不将这些差异解释成硬件效应。','',
            '## 首个增量判官窗口','']
    if not windows:lines+=['截至快照尚未启动。']
    for w in windows:
        lines.append(f'窗口PID {w["pid"]}：'+json.dumps({k:v for k,v in w.items()if k!='pid'},ensure_ascii=False))
        if 'started'in w and 'ready'in w:
            elapsed=(datetime.datetime.fromisoformat(w['ready']['utc'])-datetime.datetime.fromisoformat(w['started']['utc'])).total_seconds()
            lines.append(f'本窗口完整权重校验、加载及20条门合计{elapsed:.2f}秒，另计于缓存判分耗时；不把前缀小模型的约8秒启动速度套用到13B判官。')
    lines+=['','窗口先核验模型文件，再过原20条门，之后只写判分缓存；copyright仍走CPU MinHash。读取锁不变。PAIR缓存优先，余下驻留时间用于已冻结的WJB top2与尾部top1；窗口有界、可续跑。','',
            '## 尾部补跑','']
    if not x['tail_live']:lines+=['截至快照尚无新尾部行落盘；PAIR补前缀优先。']
    else:lines+=['以下是各卡最近一次尾部观察；process_exists=false表示该段已结束/让出，不能视为仍在占卡。']
    for t in x['tail_live']:lines.append(json.dumps(t,ensure_ascii=False))
    qa=S/'first_tail_metadata_qa_addendum.json'
    if qa.exists():
        z=load(qa);lines+=['',z['clarification'],json.dumps(z['families'],ensure_ascii=False),f'元数据核对SHA256 {sha(qa)}。']
    lines+=['','各尾部条件old_s0、SYS_A、SYS_B沿原生成函数；公开侧原1979行、batch8、120token，有害侧2000行、单条、2400token。输出侧Guard按同一原模板低优先级填缓存，不聚合读取。WildGuard的WJB尾部队列先停在条件边界，PAIR WildGuard全部完成后再恢复，避免抢node01 GPU0。','',
            f'快照SHA256：{sha(source)}。',f'前缀耗时记录SHA256：{x["prefix_rate_source_sha256"]}。','']
    doc=R/'docs/254_LEASE_PRIORITY_DEPLOYMENT_STATUS.md';doc.write_text('\n'.join(lines))
    log=f'{now} LEASE_PRIORITY_DEPLOYMENT_EVIDENCE snapshot={source.relative_to(R)} SHA={sha(source)} report_SHA={sha(doc)} caught_up_utc={caught["utc"]if caught else "not_observed"}; PAIR effects remain unread; old480 retired; GPU0 release18JST unchanged.\n'
    for n in ['PREREG_LOG.txt','OPS_LOG.txt']:
        with(R/'docs'/n).open('a')as f:f.write(log)
    files=['docs/254_LEASE_PRIORITY_DEPLOYMENT_STATUS.md','docs/PREREG_LOG.txt','docs/OPS_LOG.txt','tools/handoff_20261106/export_lease_deployment_status.py','tools/handoff_20261106/publish_lease_deployment_evidence.py',str(source.relative_to(R))]
    files +=[str((S/n).relative_to(R))for n in ['first_tail_metadata_qa.json','first_tail_metadata_qa_addendum.json']if(S/n).exists()]
    if caught:
        p=S/'caught_up'/(str(caught['source_rows'])+'.json');assert sha(p)==x['first_caught_up_sha256'];files.append(str(p.relative_to(R)))
    for n in files:
        p=R/n;assert p.is_file()
        if p.suffix=='.json':safe(load(p))
        assert not re.search(r'hf_[A-Za-z0-9]{20,}',p.read_text())
    with(R/'logs/prereg_publish.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
        for n in files:p=G/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
        manifest='manifests_lease_priority_deployment_20261109.json';(G/manifest).write_text(json.dumps({'utc':now,'files':{n:sha(G/n)for n in files},'PAIR_outcomes_read':False,'no_raw_attacks_or_outputs':True},indent=2)+'\n')
        subprocess.run(['git','add',*files,manifest],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Record lease scheduler deployment, catch-up and numerical gate evidence'],cwd=G,check=True);content=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip()
        with(R/'docs/PREREG_LOG.txt').open('a')as f:f.write(f'{datetime.datetime.now(datetime.timezone.utc).isoformat()} LEASE_PRIORITY_DEPLOYMENT_CONTENT_COMMIT={content}; counts/hashes only; no PAIR outcome read.\n')
        shutil.copy2(R/'docs/PREREG_LOG.txt',G/'docs/PREREG_LOG.txt');subprocess.run(['git','add','docs/PREREG_LOG.txt'],cwd=G,check=True);subprocess.run(['git','commit','-m','Log lease deployment publication'],cwd=G,check=True);subprocess.run(['git','push','origin','main'],cwd=G,check=True)
        result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'content_commit':content,'head_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),'snapshot_sha256':sha(source),'report_sha256':sha(doc),'first_caught_up_utc':caught['utc']if caught else None};(O/'publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
