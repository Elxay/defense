from pathlib import Path
import json,hashlib,subprocess,datetime,shlex
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def L(p):return json.loads(p.read_text())
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
nodecode="""from pathlib import Path
import json,subprocess
R=Path('/home/dell/Def');U=R/'results/audit/unified300';o={}
for name in ['translation_execution_20261111/live.json','translation_execution_20261111/benign20_gate.json','translation_execution_20261111/all_generation_complete.json']:
 p=U/name
 if p.exists():
  z=json.loads(p.read_text());o[name]={k:v for k,v in z.items()if k!='checks'}
o['device_gates']={}
for p in (U/'parallel_device20').glob('*/*/complete.json'):
 z=json.loads(p.read_text());o['device_gates'][z['model']]=z
o['gpus']=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,memory.free,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True).stdout.strip()
o['compute']=subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'],capture_output=True,text=True).stdout.strip()
print(json.dumps(o))"""
node=json.loads(subprocess.run(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(nodecode)],capture_output=True,text=True,check=True).stdout)
now=datetime.datetime.now(datetime.timezone.utc);o={'utc':now.isoformat(),'jst':now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'main_labels_or_effects_read':False,'nonzero_main_outputs':0,'innet_gpus':subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.free,utilization.gpu','--format=csv,noheader'],text=True).strip(),'innet_compute':subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'],text=True).strip(),'node01':node,'models':{},'device_gates_innet':{},'prefix_position_gates':{},'hashes':{}}
for m in ['llama','qwen']:
 byfamily={}
 for root in ['static_alpha0','language_alpha0']:
  d=U/root/m
  for f in d.glob('*'):
   if not f.is_dir():continue
   q={'saved_rows':len(list((f/'generation.private').glob('*.json'))),'complete':(f/'generation_complete.json').exists()}
   for n in ['zero20_gate','position20_gate','generation_complete','execution_blocked']:
    p=f/(n+'.json')
    if p.exists():
     z=L(p);q[n]={k:z.get(k)for k in ['utc','passed','selected20_exact','selected20_passed','N','effective_rows_per_hour','error_type','reason']if k in z};q[n]['sha256']=H(p)
   byfamily[f.name]=q
  lp=d/'live.json'
  if lp.exists():o['models'].setdefault(m,{})[root+'_live']=L(lp)
 o['models'].setdefault(m,{})['families']=byfamily
 for fam in ['prefix_P1','prefix_P2']:
  p=U/'static_alpha0'/m/fam/'position20_gate.json';z=L(p);o['prefix_position_gates'][m+'_'+fam]={k:z[k]for k in ['utc','passed','selected20_passed']};o['prefix_position_gates'][m+'_'+fam]['sha256']=H(p)
 p=U/'parallel_device20/innet_gpu0'/m/'complete.json';o['device_gates_innet'][m]=L(p)
for name in ['role_backend_benign/prototype_complete.json','translation_backtranslation_cosine/live.json']:
 p=U/name
 if p.exists():o[name]=L(p)
o['backtranslation_summaries']={p.name:L(p)for p in (U/'translation_backtranslation_cosine').glob('summary_*.json')}
for name,p in [('addendum5',R/'docs/300_ADDENDUM5_UNREACHABLE_OPERATION_AND_DEVICE_TRANSLATION_GATES.md'),('full_grid',U/'calibration_full_grid_20261111.md'),('device_plan',U/'parallel_device20_plan.json'),('translation_plan',U/'translation_execution_20261111_plan.json')]:o['hashes'][name]=H(p)
status=[dict(item='role service',status='in progress: benign shared-weight/nonthinking/seed/count prototype passed; actual source parsers/controllers not integrated',ETA='not yet measurable; implementation remains, no production completion timestamp'),dict(item='eight-behavior isolation',status='in progress: 8 benign sessions x2 orders, structure/count passed; actual search-controller integration gate not passed',ETA='after role parser integration; cannot infer from benign prototype runtime'),dict(item='AutoDAN local retrieval/library',status='runtime not started; MiniLM source deviation and calibration warmup source specified, no built/frozen strategy library',ETA='unknown W before measured build; do not infer from PAIR'),dict(item='10pilot timing and tier forecast',status='not started; 0/60 across2models x3families; 440/220/88 rule and nested IDs frozen',ETA='after S1b; actual cost table pending measurements')]
o['S1b_status']=status
save(U/'status_20261111_current_checks.json',o)
sampling=L(U/'search_three_tier_sampling.json');forecast={'utc':o['utc'],'budget_GPUh':600,'tiers':[440,220,88],'formula':'C_n=sum_cell(cold_GPUh+n*mean_resident_GPUh)+shared_service_GPUh_once; W/replay/adaptive/regression separate','cells':[dict(model=m,family=f,pilot_completed=0,pilot_N=10,mean_resident_GPUh=None,cold_GPUh=None,forecast_by_tier={str(n):None for n in [440,220,88]})for m in ['llama','qwen']for f in ['PAIR','TAP','AutoDAN_Turbo']],'selected_tier':None,'reason':'formal searches forbidden until S1b gates; no cost measurements available','sampling_manifest_sha256':H(U/'search_three_tier_sampling.json')};save(U/'search_cost_forecast_pending.json',forecast)
lines=['# 11/11 当前状态、校准网格与执行门','',f"UTC：{o['utc']}；JST：{o['jst']}",'','主SORRY标签/效应未读；非零主输出0。','', '## 校准读法与结果','', 'S1a第13行原文：','', '> '+next(l for l in (R/'docs/300_S1A_STATIC_CALIBRATION_COST_UTILITY.md').read_text().splitlines()if l.startswith('R0在300')),'','追加5明确：有可行点但目标不可达，保持已选最近可行共同α继续，逐表标记目标不可达；仍需家族SORRY α0闸门、执行门。不改网格/seed/目标。当前S1a没有另外的“差>5pp”判据，5pp是良性新增预算；不追溯更改。','', '完整42行、WG/v2双口径、两个良性层和INVALID界见calibration_full_grid_20261111.md/json。Llama WG目标66.50%，选中48.11–48.22%，差18.28–18.39pp；Qwen WG目标59.83%，选中38.33%，差21.50pp。两口径选择同α：Llama0.75、Qwen1.25。','', '重要限定：Llama高α被良性预算排除；Qwen全部7α可行，因此Qwen不可达不应归因为5pp预算限制。Qwen所选点seed间WG SD8.17pp，Llama0.69–0.84pp。','', '## 各家族落盘数','', '| 家族 | Llama | Qwen |','|---|---:|---:|']
families=['base','deepinception','refusal_suppression','logical_appeal','authority_endorsement','misrepresentation','evidence-based_persuasion','expert_endorsement','prefix_P1','prefix_P2','translate-ml','translate-ta','translate-mr','translate-zh-cn','translate-fr']
for f in families:lines.append('| '+f+' | '+' | '.join(str(o['models'][m]['families'].get(f,{}).get('saved_rows',0))+'/440'for m in ['llama','qwen'])+' |')
lines+=['','4种编码均未执行，解码运行门尚未放行；搜索输出0。英语/P1/P2的α0共8800生成、WG8800缓存已齐；无主标签汇总。语言α0各家族先20门、固定B8/B4、缓存只写。','', '## 设备与翻译门','', '| 模型 | innet GPU0 | node01 GPU1 |','|---|---:|---:|']
for m in ['llama','qwen']:lines.append(f"| {m} | {o['device_gates_innet'][m]['exact_selected']}/20 | {node['device_gates'][m]['exact_selected']}/20 |")
lines+=['','两站全覆盖批成员也字节一致（Llama覆盖24，Qwen覆盖20）；仅验证此次base α0，不外推非零/所有提示，每家族门保留。P1/P2两模型位置门均selected20=20。','', '翻译无害20条两次重放20/20，全资产SHA核对通过；node01依赖langdetect1.0.9和six1.17.0已补齐，均在实际翻译推理之前失败，记录见translation_runtime_dependency_receipt.json。','', '2200条指令回译正在node01 GPU2按冻结B1执行；当前进度见JSON，完整余弦分布未完成时不提前填结果。固定MiniLM CPU汇总器只在各语言440齐全后报告，不设阈值，不据此改变范围。指令保真度不等于回复保真度。','', '## S1b状态','']
for s in status:lines+=['- '+s['item']+'：'+s['status']+'；ETA：'+s['ETA']+'。']
lines+=['','原型不是正式服务或搜索控制器验收，不把两顺序无害会话测试冒充已过真实搜索隔离。10计时属于正式搜索，仍锁；成本表没有实测数，三档未选。','', '## SHA','']
for k,v in o['hashes'].items():lines.append('- '+k+': `'+v+'`')
lines+=['- 当前状态JSON: `'+H(U/'status_20261111_current_checks.json')+'`']
(U/'current_checks_report_20261111.md').write_text('\n'.join(lines).rstrip()+'\n');save(U/'current_checks_report_20261111_receipt.json',dict(utc=o['utc'],report_sha256=H(U/'current_checks_report_20261111.md'),snapshot_sha256=H(U/'status_20261111_current_checks.json'),main_labels_read=False))
print(json.dumps({'utc':o['utc'],'jst':o['jst'],'translation':node.get('translation_execution_20261111/live.json'),'innet_gpu':o['innet_gpus'],'innet_compute':o['innet_compute'],'node_gpu':node['gpus'],'node_compute':node['compute'],'language_live':{m:o['models'][m].get('language_alpha0_live')for m in ['llama','qwen']},'hashes':o['hashes'],'report_sha256':H(U/'current_checks_report_20261111.md')},ensure_ascii=False,indent=2))
