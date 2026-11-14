from u300_schedule_prepare import *
import os,sys,signal,collections,importlib.metadata,datetime,shlex
os.environ['GIT_SSH_COMMAND']='ssh -o Hostname=127.0.0.1 -o Port=18443 -o HostKeyAlias=github.com -o StrictHostKeyChecking=yes -o ConnectTimeout=15'
O=U/'followup38';results=L(U/'followup36/rating264_results.json')['rows'];pool={}
for kind in ['selected','last']:
 rs=[r for r in results if r['kind']==kind];pool[kind]=dict(high_SORRY0=sum(r['score']>=10 and r['SORRY_same_internal']==0 for r in rs),low_SORRY1=sum(r['score']<10 and r['SORRY_same_internal']==1 for r in rs),score_exact1_SORRY1=sum(r['score']==1 and r['SORRY_same_internal']==1 for r in rs))
save(O/'sampling_pool_correction.json',dict(utc=utc(),actual_sampling='selected132 only; no resampling for replay review',pool=pool,seeds=dict(high=2026111407,low=2026111408,mix=2026111409),low_combined_correct=pool['selected']['low_SORRY1']+pool['last']['low_SORRY1'],requested_122_uses_inconsistent_predicates=True))
save(O/'replay_review_aggregate.json',dict(utc=utc(),N=24,source='same24 selected prompt HF2400 independent replay, full saved responses',annotator='current model; shared prior context; not human',strata=[dict(old_pool='selected score10/SORRY0 internal',N=12,fulfilled=0,unfulfilled=12,uncertain=0),dict(old_pool='selected score<10/SORRY1 internal',N=12,fulfilled=8,unfulfilled=3,uncertain=1)],original_six_uncertain_after_full_replay=dict(fulfilled=3,unfulfilled=2,semantic_boundary=1),private_annotations_sha256='316f1eb32e8c13f37dcc1d52dbaee0de882724fb60eaf53d6b7d8ebf1a875252',ID312='selected replay changes target; corresponding last replay checked separately and retains original target; do not call this a last-family drift example',human_annotation_complete=False,no_primary_judge_changes=True))
HUM=R/'results/audit/human_review_20261210/search38';HUM.mkdir(parents=True,exist_ok=True);src=O/'private_review/human20.private.json';shutil.copy2(src,HUM/'inputs.private.json');save(HUM/'manifest.json',dict(utc=utc(),N=20,input_sha256=H(src),seed=2026111430,source='same24 selected replay source; no model labels included',human_labels_completed=False));save(O/'human_package_receipt.json',dict(utc=utc(),N=20,package_relative=str(HUM.relative_to(R)),input_sha256=H(HUM/'inputs.private.json'),human_labels_completed=False))
batch=[]
for B in [8,4]:
 D=U/'translation_batch_engineering20'/f'B{B}';ms=[L(p) for p in (D/'metrics').glob('*.json')];batch.append(dict(B=B,failure=L(D/'failed.json'),saved_rows=len(list((D/'processed.private').glob('*.json'))),measured_rows=sum(x['rows'] for x in ms),minimum_headroom_GiB=min((x['headroom_GiB'] for x in ms),default=None),complete_100_label_gate=False))
save(O/'batch_translation_audit.json',dict(utc=utc(),trials=batch,B4_MemoryError='explicit worker raise MemoryError(peak headroom below3GiB); not proven host RAM exhaustion',worker_sha256=H(T/'u300_translation_batch_worker20.py'),selected_B=1,no_formal_batch_admission=True))
receipts=L(O/'judge_batch_receipts.json')
for r in receipts['receipts']:
 rs=L(U/'score_waves'/r['wave']/'inputs.private.json');ids=[str(x['id']) for x in rs];r['stable_sorted_IDs_sha256']=hashlib.sha256(json.dumps(sorted(ids,key=lambda x:(int(x.split(':')[0]),x)),separators=(',',':')).encode()).hexdigest()
receipts['sort_definition']='numeric base ID, then full ID string; actual execution order and batches separately retained';receipts['actual_vllm_version']=importlib.metadata.version('vllm');save(O/'judge_batch_receipts.json',receipts)
old=(T/'u300_T2_watch37.py').read_text();needle="Rpoint=g+p+reserve+judge;Rhigh=(g+p)*1.2+reserve+judge;Hleft="
replace="groups=L(O.parent/'followup38/replay_execution.json')['groups'];rp=any(state.get(prefix+x['group'],{}).get('state')!='done' for x in groups for prefix in ['replay38_','judge38_']);small={'innet:2':1.5 if rp else 0.,'innet:3':2. if state.get('Gemma_zero20_window38',{}).get('state')!='done' else 0.};extra=sum(small.values());Rpoint=g+p+reserve+judge+extra;Rhigh=(g+p)*1.2+reserve+judge+extra;Hleft="
assert needle in old;s=old.replace(needle,replace).replace("v*1.2+reserve/6+(judge if k=='innet:2' else 0)","v*1.2+reserve/6+(judge if k=='innet:2' else 0)+small.get(k,0)").replace("R_point_GPUh=Rpoint,R_high_planning_GPUh=Rhigh,","R_point_GPUh=Rpoint,R_high_planning_GPUh=Rhigh,engineering_window_reserve_GPUh=extra,");w=T/'u300_T2_watch38.py';w.write_text(s);compile(s,str(w),'exec')
doc=R/'docs/300_ADDENDUM38_OCCUPANCY_SMALL_WINDOWS_AND_BATCH_FAILURE.md';doc.write_text('''# 追加38执行补记：占卡证据、工程小窗和批翻译失败

过去24小时恢复的是已登记队列及明确闭合START/EXIT包装日志的占卡区间并集，含加载/等待，不是逐秒GPU利用率。没有全程硬件采样，不能报告完整GPU忙碌率；尚无证据将60%称作外部占用风险概率，它只是规划假设，90%也不能从一张全满快照推出。

独立持久化硬件采样从本次实际启动开始，每60秒记录UTC/UUID/利用率/显存/PID，不倒填历史。占卡低覆盖的未解释间隔不能声称被外部作业占满。

本次Gemma最多2卡时和已明确请求的alpha0搜索诊断规划1.5卡时纳入T2剩余R与对应卡负载，未完成前保留全额余量，完成后实际驻留入账。这两个小窗口获准先行，不等T2结束；长期释放仍另判。2卡时Gemma只是零向量20条工程门，不冒称100行标签门或向量训练通过。

批翻译B8实际CUDA OOM；B4的MemoryError来自代码主动抛出的“峰值显存余量不足3GiB”，不是已证实的主机RAM耗尽。二者均未完成100条SORRY标签比较，不能说标签变化超2%。保留原冻结B8→B4→B1回退；未通过完整工程准入，不将批译用于非零正式数据。
'''.rstrip()+'\n')
pub=[doc,w,T/'u300_GPU_sampler38.py',O/'sampling_pool_correction.json',O/'replay_review_aggregate.json',O/'human_package_receipt.json',O/'batch_translation_audit.json',O/'judge_batch_receipts.json',O/'GPU_24h_occupancy.json',O/'GPU_24h_lease_intervals.json',Path(__file__)];commit=publish(pub,'Publish replay-review scope corrections and measured lease coverage; meter bounded engineering windows into T2')
prior=L(U/'followup37/T2_watch/live.json')['pid'];assert b'u300_T2_watch37.py' in (Path('/proc')/str(prior)/'cmdline').read_bytes();os.kill(prior,signal.SIGTERM)
log=(O/'T2_watch38.log').open('a');p=subprocess.Popen([sys.executable,str(w)],stdout=log,stderr=log,start_new_session=True);glog=(O/'GPU_sampler38.log').open('a');q=subprocess.Popen([sys.executable,str(T/'u300_GPU_sampler38.py')],stdout=glog,stderr=glog,start_new_session=True);save(O/'CPU_execution.json',dict(utc=utc(),commit=commit,T2_watch_old_pid=prior,T2_watch_new_pid=p.pid,GPU_sampler_pid=q.pid,only_own_CPU_watcher_replaced=True,document_sha256=H(doc)));print(json.dumps(L(O/'CPU_execution.json')));print('BATCH',json.dumps(batch))
