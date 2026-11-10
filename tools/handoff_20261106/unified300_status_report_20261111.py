from pathlib import Path
import json,hashlib,subprocess,datetime,shlex
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def dump(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def gpu(): return subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,memory.free,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip()
nodecode="""import pathlib,json,subprocess
u=pathlib.Path('/home/dell/Def/results/audit/unified300/static_alpha0_WG')
d={'gpus':subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,memory.free,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True).stdout.strip()}
for n in ['live.json','reference20_v2.json','failure_v2.json']:
 p=u/n; x=json.loads(p.read_text()) if p.exists() else None
 d[n]=({k:x.get(k) for k in ['utc','passed']} if n=='reference20_v2.json' and x else x)
print(json.dumps(d))"""
node=json.loads(subprocess.run(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(nodecode)],capture_output=True,text=True,check=True).stdout)
preserve=load(U/'static_generation_preservation_before_WG_IO_repair.json')
assert all(sha(R/p)==h for p,h in preserve['files_sha256'].items())
now=datetime.datetime.now(datetime.timezone.utc); s={'utc':now.isoformat(),'jst':now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'main_labels_or_effects_read':False,'models':{},'innet_gpus':gpu(),'node01':node,'preserved_generation_files_verified':len(preserve['files_sha256']),'B4_directions':load(U/'B4_disagreement_directions.json'),'B4_directions_sha256':sha(U/'B4_disagreement_directions.json'),'throughput_engineering_panel':{},'calibration_WG_complete':load(U/'calibration_WG_all_scoring_complete.json'),'alpha_decisions':{'llama':{'alpha':0.75,'target_reachable':False,'decision_utc':'2026-11-10T17:41:22.560979Z','commit':'59b9b75','ledger_sha256':'25bd2d63fda506c8599cbe36637b8f96ce55f61de55a3117769cabc83b8bfaba'},'qwen':{'alpha':1.25,'target_reachable':False,'decision_utc':'2026-11-10T17:41:29.789408Z','commit':'88f30ea','ledger_sha256':'6dcd14974571b65fa491812ffcb296c9ea898e18dded79de840d064a026057ca'}},'S1b_frozen':False,'search_outputs':0,'language_translation_execution_gate':'pending; no language outputs','prefix_position_gates':'pending queue reaches family','nonzero_main_generation_enabled':False}
for model,rel in [('llama','acceptance_v2/llama/metrics'),('qwen','acceptance_v5/qwen/metrics')]:
 files=sorted((U/rel).glob('*candidate_batch*.json')); rows=[load(p) for p in files]
 total=sum(x['rows'] for x in rows); seconds=sum(x['elapsed_seconds'] for x in rows); assert total==300
 s['throughput_engineering_panel'][model]={'N':total,'elapsed_seconds':seconds,'rows_per_hour':total/seconds*3600,'metrics_sha256':{p.name:sha(p) for p in files},'peak_reserved_GiB':max(x['peak_reserved_bytes'] for x in rows)/2**30,'minimum_headroom_GiB':min(x['headroom_bytes'] for x in rows)/2**30}
for m in ['llama','qwen']:
 d=U/'static_alpha0'/m; out={'live':load(d/'live.json'),'families':{}}
 for f in sorted(d.iterdir()):
  if not f.is_dir():continue
  item={'saved_rows':len(list((f/'generation.private').glob('*.json')))}
  for name in ['zero20_gate','position20_gate']:
   p=f/(name+'.json')
   if p.exists():
    o=load(p);item[name]={k:o.get(k) for k in ['utc','passed','exact20']};item[name]['sha256']=sha(p)
  p=f/'generation_complete.json'
  if p.exists():
   o=load(p);item['complete']={k:o.get(k) for k in ['utc','N','effective_rows_per_hour','family_wall_seconds_including_gate_overhead']};item['complete']['sha256']=sha(p)
  out['families'][f.name]=item
 s['models'][m]=out
hashfiles={'addendum4':R/'docs/300_ADDENDUM4_LANGUAGE_BATCH_REGRESSION_AND_SEARCH_TIERS.md','language_rule':U/'language_preprocessing_plan.json','translator_assets':U/'translator_Qwen3_asset_manifest.json','regression_rule':U/'postmain_path_regression_plan.json','search_tiers':U/'search_three_tier_sampling.json','WG_IO_repair':U/'static_WG_cache_IO_repair.json'}
s['hashes']={k:sha(p) for k,p in hashfiles.items()}
dump(U/'status_20261111_031x.json',s)
lines=['# 300 本轮执行记录', '', '快照 UTC：'+s['utc'],'JST：'+s['jst'],'','主测试标签和效应未读取。只读取缓存进度；校准选择单独按状态→α0→完整网格/合法上限→决定读取。','', '## B4方向','', '| 条件 | 规则 | 批比单条多拒答 | 少拒答 | 精确McNemar p |','|---|---|---:|---:|---:|']
for o in s['B4_directions']['records']:
 if o['batch_more_refusal'] or o['batch_less_refusal']:lines.append(f"| {o['condition']} | {o['rule']} | {o['batch_more_refusal']} | {o['batch_less_refusal']} | {o['McNemar_exact_two_sided']} |")
lines+=['','WG随机变化ID wjb_train_000065024；v2 α0变化ID wjb_train_000058959。其他B4单元无变化，不将方向解释为系统偏差。','','## 实测吞吐','','工程面板：Llama B8三条件300条796.20行/小时（α0 831.88）；Qwen B4三条件300条678.30（α0 668.46）。不含冷加载和无钩子参考门耗时，不能外推所有家族。','','| 模型 | base α0条数 | 实测行/小时 | 全家族墙钟含门检(秒) |','|---|---:|---:|---:|']
for m in ['llama','qwen']:
 b=s['models'][m]['families']['base']['complete'];lines.append(f"| {m} | {b['N']} | {b['effective_rows_per_hour']:.2f} | {b['family_wall_seconds_including_gate_overhead']:.2f} |")
lines+=['','## 执行与锁','','GPU2 Llama/PID540433/B8，GPU3 Qwen/PID540429/B4。base均440完成，下一家族状态见JSON；其余五说服等按固定队列逐一执行门检，不能将排队记为已开始。P1/P2额外位置门未过前不放行，编码/语言门仍关闭。GPU1外部项目不动；GPU0本轮未使用。node01 GPU0运行WG只写缓存；GPU1/2无本项目计算作业。','','WG首次因整数ID转缓存文件名失败，0条主评分已写；已保留失败记录、发布I/O-only v2并重新过20/20门。数值模板、权重、批大小不改；生成旧文件'+str(s['preserved_generation_files_verified'])+'个SHA全部未变。新评分仅计进度，不读标签/INVALID汇总。','','## 校准读取','','44任务30800评分于2026-11-10T16:50:09.094967Z完成，本地桥齐全16:50:30.431001Z。Llama四步读取于17:41:22Z、Qwen17:41:29Z，逐步UTC/SHA见calibration_selection_reads/*/read_ledger.json。Llama α0.75、Qwen α1.25；两者均在冻结可行网格内未达到目标，按原不可达分支选择。非零主生成仍未启用。','','## 规则与预算','','语言langdetect1.0.9 seed20261267；英文透传，其余固定Qwen3-8B revision b968826d9c46dd6066d109eabc6255188de91218翻英语，thinking关闭，B1，greedy，翻译cap4096；错误保留为INVALID并给界。全体与原英语子集都报；各语言只描述。模型资产已核验，node01复制及20条接口门尚未执行，不声称翻译链已可用。','','回归固定s3/第一随机、seed20261268，每家族100（88档全88）；主结果快照后执行。22家族按244行/小时约18.03卡小时/模型，评分另计；只核对一对向量，不能替代完整配方方差。','','搜索第一轮2模型×3家族，440/220/88嵌套；10计时行均保留。按实测驻留卡时选预测≤600的最大档；88仍超则预算不可行，不启动bulk。S1b、角色服务/行为隔离/本地检索执行门尚未齐，未产生搜索输出。','','目标串映射SHA 1bca91c7a4ab634d1a205a45cd550f9d266513bd561d1c96b7b72e3cbe323d93；规则/固定文本manifest SHA 85ff7ff420a7308d73e0b3e60639240dec7c2bc13eb14a456085b094a49bc316。','','## SHA清单','']
for k,h in s['hashes'].items():lines.append(f'- {k}: `{h}`')
lines+=['- B4方向输出: `'+s['B4_directions_sha256']+'`','- 完整状态JSON: `'+sha(U/'status_20261111_031x.json')+'`']
(U/'execution_report_20261111.md').write_text('\n'.join(lines)+'\n')
dump(U/'execution_report_20261111_receipt.json',{'utc':now.isoformat(),'report_sha256':sha(U/'execution_report_20261111.md'),'snapshot_sha256':sha(U/'status_20261111_031x.json'),'main_labels_or_effects_read':False})
print(json.dumps({'utc':s['utc'],'jst':s['jst'],'models':{m:s['models'][m]['live'] for m in s['models']},'node':node,'report_sha256':sha(U/'execution_report_20261111.md'),'preserved_files':s['preserved_generation_files_verified']},ensure_ascii=False,indent=2))
