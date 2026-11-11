from pathlib import Path
import datetime,json,re,subprocess
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(T/'u300_generation_matrix_v3.py')],check=True,stdout=subprocess.DEVNULL)
# The earlier preparation inventory is immutable evidence; refresh only live GPU
# process ownership here and keep its snapshot time explicit.
subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(T/'u300_preparation_status_report.py')],check=True,stdout=subprocess.DEVNULL)
matrix=L(U/'family_condition_status_20261111_v3.json');cards=L(U/'GPU_project_status_rule16.json');prep=L(U/'Gemma_Mistral_preparation_status_20261111.json')
audit=[]
pattern=re.compile(r'(?<!\d)(?:1/10|5/10|6/10)(?!\d)|(?:each|every|all)\s+(?:(?:four|4|tested)\s+)?models?.{0,90}(?:multiple|diverse)\s+(?:jailbreak|attack)',re.I)
for p in (R/'paper').rglob('*.tex'):
 for i,line in enumerate(p.read_text().splitlines(),1):
  if pattern.search(line):audit.append(dict(file=str(p.relative_to(R)),line=i,text_sha256=__import__('hashlib').sha256(line.encode()).hexdigest()))
save(U/'paper_rule16_diagnostic_claim_audit.json',dict(utc=utc(),narrow_pattern_hits=audit,
   scope='Pilot n10 fractions and premature per-model multiple-attack claim patterns; not a full manuscript proof',
   pilot_diagnostic_publication_exclusion_sha256=H(U/'pilot10_diagnostic_publication_exclusion.json')))
vector_files=[]
for base in [R/'results/audit/crossmodel287',U]:
 for p in base.rglob('v.npy'):
  if any(k in str(p.relative_to(base)).lower() for k in ['gemma','mistral']):vector_files.append(str(p.relative_to(R)))
assert not vector_files,'Unexpected new-model trained vector; update model inventory before reporting'
lines=['# 规则16、当前家族生成表与后续模型准备', '',
 '卡快照 UTC：'+cards['utc']+'；生成快照 UTC：'+matrix['utc'], '',
 'HarmBench首窗实际12:51:24.981658→14:29:10.878709 UTC，双卡占用5865.90秒（1小时37分45.90秒）。21,120条缓存完成，未读标签汇总或INVALID总数。GPU2/3已还给生成；GPU0期间也在生成与SORRY小波次之间接续。', '',
 '## 卡与项目', '', '| 卡 | 账号 | 项目任务 | CUDA PID | 命令 |','|---|---|---|---:|---|']
for c in cards['cards']:
 task=', '.join(z['task'] for z in c['registered']) or c['project']
 proc=c['processes'];lines.append('| '+c['site']+' GPU'+str(c['card'])+' | '+','.join(str(p['account']) for p in proc)+' | '+task+' | '+','.join(str(p['pid']) for p in proc)+' | '+','.join(p['command_basename'] for p in proc)+' |')
lines += ['', 'GPU1外部任务不动；同账号不代表同项目。', '',
 '## 88预算规则', '',
 '上界<25%失败格未来扩档成本剔除；所有已耗搜索算力仍计600总账。INVALID跨线暂计并标未决。最大档选择只用alpha0门与剩余预算，不读非零效应；未知成本不按0。代码边界/账本固定样例已通过，未据样例发放执行许可。',
 '含一次冷启动顺序：PAIR-L 3.41、PAIR-Q 5.38、TAP-L 21.05、TAP-Q 35.91卡小时。新88行冻结时0；TAP88已接入同顺序，但新固定20和12行为8/4并发结构门未过前不运行正式行。220/440仍需新逐格执行准入，不写旧outcomes_used=False绕过alpha0门。',
 'n10诊断汇总只留审计日志，不进论文结果表；原计时行为仍进入正式88。当前不能把预期无动态范围写成已证实；每格等88门。',
 '追加16 SHA256 `'+H(R/'docs/300_ADDENDUM16_ACTIVE_CELL_SEARCH_BUDGET_AND_PREPARATION_SCHEDULE.md')+'`', '',
 '## 模型准备', '', '| 项 | Gemma-2-9B-it | Mistral-7B-Instruct-v0.3 |', '|---|---|---|',
 '| 范数 | 完成：layers[12] M=141.9122, rho=127.7210 | 完成：layers[9] M=2.5897, rho=2.3308 |',
 '| 原生基线 | 旧合法400+val70=470完成；新700未开始 | 旧470未开始；新700未开始；原生预审基线任务已排队 |',
 '| 渲染 | 完成；eager禁编译；A/B用户轮前置 | 完成；sdpa；system合并INST |',
 '| 拒答检查 | WG470完成，固定30+30盲读尚未标注 | 未开始，依赖原生基线 |',
 '| 学出向量 | 0/3，未训练 | 0/3，未训练 |',
 '| 统一700校准及alpha | 未开始 | 未开始 |', '',
 '开始目标：Gemma固定样本复核是CPU读数，不应继续当作等GPU。Mistral预审基线已注册为低优先、可让位任务：Llama英语prefix_P2 s5完成后，GPU2空闲经wait_gpu即启动，不等搜索或整轮结束。按当前英语ETA，预计11/12午后具备接卡机会；若更高优先任务介入则11/13–14。两模型训练目标11/13、统一700校准目标11/13–14，均以自己的keep60目标包、拒答和执行门通过为前提；旧470不是新700校准。', '',
 '## 翻译与泰米尔语', '',
 'WG首波退出14:05:29.268136 UTC，缓存同步后释放收据14:08:13.587299。先前已经启动的ASCII工程门完成后，CF翻译已占node01 GPU2；两模型从未同卡同时驻留。其余编码任务已加CF完成前置。Llama泰米尔alpha0已有76行；已提高补齐优先级，CF已有四单元不等它，其余印度语言保持后置。9个已有完整alpha0单元仍需各自回复预处理，并非其余语言已经全部翻译。', '',
 '## HiddenDetect资产', '',
 'ModelScope全精度权重已于13:41:32.792454 UTC完成10个所需文件下载，三片权重逐片实测SHA与原HF LFS清单一致。manifest SHA256 `'+L(U/'HiddenDetect_ModelScope_download_complete.json')['manifest_sha256']+'`。这不是接口或检测复现通过。',
 '作者load_FigTxt函数没有类别筛选；当前上游CSV500行/10类。依用户指令使用完整500并标非原设置，不猜350/7类子集、不套原350行复现通过线。', '',
 '## 家族×条件表', '',
 (U/'family_condition_status_20261111_v3.md').read_text()]
report=U/'RULE16_MATRIX_MODEL_PREPARATION_20261111.md';report.write_text('\n'.join(lines).rstrip()+'\n')
log=utc()+' Rule16 active-cell future-cost change frozen at zero new88 rows; sunk main-search costs retained in600 cap. No new nonzero effects read. HB ended14:29:10UTC, actual1h37m46s; resource-aware matrix v3 refreshed, not uniform2.2h shift. Gemma/Mistral old readiness separated from unified700; trained0/3 each. Mistral prereview baseline registered after first English release; calibration gates unchanged. FigTxt loader no filter ->500 non-original; ModelScope3shards verified. reportSHA='+H(report)+'\n'
files=[report,U/'family_condition_status_20261111_v3.json',U/'family_condition_status_20261111_v3.md',
 U/'Gemma_Mistral_preparation_status_20261111.json',U/'GPU_project_status_rule16.json',U/'paper_rule16_diagnostic_claim_audit.json',
 U/'HiddenDetect_ModelScope_download_complete.json',R/'models/HiddenDetect_llava_v16_vicuna7b_modelscope/DOWNLOAD_SHA256.json',Path(__file__)]
# Manifest contains file hashes only, never model weights or prompt text.
for name in ['OPS_LOG','OPS_LOG.txt','PREREG_LOG.txt']:
 p=R/'docs'/name
 if p.exists():
  with p.open('a') as f:f.write(log)
  files.append(p)
commit=publish(files,'Publish current resource-aware matrix, active-cell budget rule and cross-model preparation evidence')
save(U/'rule16_final_publication.json',dict(utc=utc(),commit=commit,report_sha256=H(report)))
print(json.dumps(dict(commit=commit,report_sha256=H(report),matrix_utc=matrix['utc'],cards_utc=cards['utc'],paper_pattern_hits=audit)))
