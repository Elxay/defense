from pathlib import Path
import json,hashlib,datetime,subprocess,fcntl,shutil
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';G=R/'prereg_repo'
def L(p):return json.loads(p.read_text())
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
for n in ['unified300_export_calibration_grid.py','unified300_parallel_device20.py','unified300_translation_diagnostic.py']:
 p=T/n;s=p.read_text();p.write_text(s);compile(s,str(p),'exec')
p=L(U/'static_alpha0_execution_plan.json');priv=L(U/'static_alpha0_inputs.private.json');payload={};specs={}
nodepaths={'llama':'/home/dell/.cache/huggingface/hub/models--meta-llama--Meta-Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659','qwen':'/data/ray/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'}
for m,s in p['models'].items():
 cfg=s['families']['base'];selected=set(cfg['gate_selected20_IDs']);rows={str(r['id']):r for r in priv[m]['base']};groups=[]
 for batch in cfg['batches']:
  if not selected.intersection(batch):continue
  group=[]
  for k in batch:
   r=rows[k];ref=L(U/'static_alpha0'/m/'base/generation.private'/f'{int(k):04d}.json');group.append(dict(id=int(k),input_ids=r['input_ids'],position=r['position'],reference=ref['result']['text'],selected20=k in selected,prompt_sha256=r['prompt_sha256']))
  groups.append(group)
 payload[m]=groups;mp=Path(s['model_path']);files={n:H(mp/n)for n in s['asset_interface_sha256']};files.update({f.name:H(f)for f in mp.glob('*.safetensors')});assert len([n for n in files if n.endswith('.safetensors')])==4
 specs[m]=dict(model_paths={'innet_gpu0':s['model_path'],'node01_gpu1':nodepaths[m]},files_sha256=files,layer=s['layer'],batch_size=s['batch_size'])
save(U/'parallel_device20_inputs.private.json',payload);save(U/'parallel_device20_plan.json',dict(utc_frozen=datetime.datetime.now(datetime.timezone.utc).isoformat(),worker_sha256=H(T/'unified300_parallel_device20.py'),batch_core_sha256=H(T/'batched_injection300.py'),private_input_sha256=H(U/'parallel_device20_inputs.private.json'),models=specs,N_selected_each=20,sites=['innet_gpu0','node01_gpu1'],cap=2400,gate='all covered bytes equal to completed innet base alpha0; preserves frozen full batch composition; no label reads; per-family gates remain required',future_nonzero_not_admitted=True))
D=R/'results/audit/sorry296/downloads.private/sorry-bench-202503';base={r['question_id']:r for r in [json.loads(x)for x in (D/'question.jsonl').read_text().splitlines()if x]};assert len(base)==440
inputs=[]
for lang in ['zh-cn','fr','mr','ml','ta']:
 fn=D/f'question_translate-{lang}.jsonl';rs=[json.loads(x)for x in fn.read_text().splitlines()if x];assert {r['question_id']for r in rs}==set(base)
 for r in sorted(rs,key=lambda r:r['question_id']):
  assert len(r['turns'])==1 and len(base[r['question_id']]['turns'])==1
  text=r['turns'][0];english=base[r['question_id']]['turns'][0];inputs.append(dict(id=r['question_id'],language=lang,text=text,base_text=english,source_sha256=hashlib.sha256(text.encode()).hexdigest(),base_sha256=hashlib.sha256(english.encode()).hexdigest()))
save(U/'translation_diagnostic_inputs.private.json',inputs)
fixtures=[]
texts={
'zh-cn':['图书馆每天上午九点开放，晚上六点关闭。','请把蓝色的书放在窗户旁边的小桌子上。','我们将在星期六乘火车去海边看日出。','这座城市有许多公园，居民喜欢在周末散步。'],
'fr':['La bibliothèque ouvre chaque matin à neuf heures et ferme à dix-huit heures.','Veuillez poser le livre bleu sur la petite table près de la fenêtre.','Nous prendrons le train samedi pour regarder le lever du soleil au bord de la mer.','Cette ville possède de nombreux parcs où les habitants aiment se promener le week-end.'],
'mr':['ग्रंथालय रोज सकाळी नऊ वाजता उघडते आणि संध्याकाळी सहा वाजता बंद होते.','कृपया निळे पुस्तक खिडकीजवळच्या छोट्या टेबलावर ठेवा.','शनिवारी आम्ही समुद्रकिनारी सूर्योदय पाहण्यासाठी रेल्वेने जाणार आहोत.','या शहरात अनेक उद्याने आहेत आणि लोकांना आठवड्याच्या शेवटी फिरायला आवडते.'],
'ml':['ഗ്രന്ഥശാല എല്ലാ ദിവസവും രാവിലെ ഒമ്പത് മണിക്ക് തുറക്കുകയും വൈകുന്നേരം ആറിന് അടയ്ക്കുകയും ചെയ്യുന്നു.','നീല പുസ്തകം ജനലിനടുത്തുള്ള ചെറിയ മേശപ്പുറത്ത് വയ്ക്കുക.','ശനിയാഴ്ച സൂര്യോദയം കാണാൻ ഞങ്ങൾ ട്രെയിനിൽ കടൽത്തീരത്തേക്ക് പോകും.','ഈ നഗരത്തിൽ ധാരാളം പാർക്കുകളുണ്ട്, വാരാന്ത്യങ്ങളിൽ നടക്കാൻ ആളുകൾ ഇഷ്ടപ്പെടുന്നു.'],
'ta':['நூலகம் தினமும் காலை ஒன்பது மணிக்கு திறந்து மாலை ஆறு மணிக்கு மூடப்படுகிறது.','நீல நிறப் புத்தகத்தை ஜன்னலுக்கு அருகிலுள்ள சிறிய மேசையில் வைக்கவும்.','சனிக்கிழமை சூரிய உதயத்தைப் பார்க்க நாங்கள் ரயிலில் கடற்கரைக்குச் செல்வோம்.','இந்த நகரத்தில் பல பூங்காக்கள் உள்ளன, வார இறுதியில் மக்கள் நடக்க விரும்புகிறார்கள்.']}
for lang,ss in texts.items():
 for i,text in enumerate(ss):fixtures.append(dict(id=f'{lang}_{i}',language=lang,text=text))
save(U/'translation_benign20.json',fixtures)
save(U/'translation_execution_20261111_plan.json',dict(utc_frozen=datetime.datetime.now(datetime.timezone.utc).isoformat(),worker_sha256=H(T/'unified300_translation_diagnostic.py'),language_plan_sha256=H(U/'language_preprocessing_plan.json'),inputs_sha256=H(U/'translation_diagnostic_inputs.private.json'),fixtures_sha256=H(U/'translation_benign20.json'),N=2200,N_by_language={l:440 for l in texts},physical_gpu=2,node='node01',repeatability_gate='20 benign non-English sentences, two actual deterministic translations each; nonempty nontruncated bytes equal; interface only',backtranslation='force translation of every supplied language instruction, even if langdetect calls source English; not response routing or test answers',translator_runtime_unchanged=True,downstream='English all-MiniLM-L6-v2 fixed snapshot1110a243fdf4706b3f48f1d95db1a4f5529b4d41; CPU cosine against original English instruction, default max_seq_length with truncation counts; no threshold, report errors and missing; no gate on similarity, no model condition comparisons',no_reply_fidelity_claim=True,no_main_outcomes_read=True))
source=R/'docs/300_S1A_STATIC_CALIBRATION_COST_UTILITY.md';line=next(l for l in source.read_text().splitlines()if l.startswith('R0在300'))
text='# 300 追加5：不可达操作点与设备/翻译执行核对\n\n冻结UTC：'+datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n\n## 冻结原文与解释\n\n来源 docs/300_S1A_STATIC_CALIBRATION_COST_UTILITY.md 第13行，文件SHA '+H(source)+'。原文：\n\n> '+line+'\n\n有可行非零点但目标不可达时，继续在已冻结的最近可行共同alpha做主测试，逐表标注“冻结网格内目标不可达”；不重新选择、不扩网格、不删seed，不写达到校准目标。无可行非零点和INVALID排序未决仍不放行。当前WG主alpha Llama0.75、Qwen1.25不变；v2只作敏感性选择。当前S1a原文未另设“距目标超过5pp”的不可达判定，5pp在该文是良性新增拒答上限；不把旧稿措辞追溯加入当前选择。两个已选点的差均超过5pp，因此这一措辞差异不改变本次标记。\n\n本条在任何非零SORRY主生成之前冻结。继续运行仍需SORRY alpha0家族闸门及路径/位置/预处理门，不将校准完成等同于全家族放行；主测试标签读取锁保持，旧Llama alpha1数据标遗留、不混表。可行网格未达目标只描述该校准/预算下的观察，不认定机制。\n\n## 调度与检查\n\n原10个英语/P1/P2家族两模型均440完成，不重复生成。GPU0同节点、node01 GPU1跨节点各对Llama B8/Qwen B4做20条alpha0逐字节门，保持原完整批成员和2400cap，所有覆盖行都一致才放行相应路径；不据此取消逐家族门，也不外推非零条件。模型全分片/模板文件SHA核验，门失败就记录该路径不可用，不改B/EOS/后端以凑一致。执行计划SHA '+H(U/'parallel_device20_plan.json')+'。\n\nnode01 GPU2使用冻结Qwen3-8B翻译runtime。先核所有资产及20条无害文本两次重放；然后做五语言各440条指令回译。回译使用同一固定翻译模板/参数、逐条B1，不改变主回复路由。与英文原指令的MiniLM余弦只作描述，不设准入阈值，不等于回复保真度；公开ID/计数/SHA，原指令及译文不入git。失败和截断单列，不丢弃后挑样本。执行计划SHA '+H(U/'translation_execution_20261111_plan.json')+'。其2200次B1翻译的时间以实测更新，不预称“几分钟”。\n\nS1b角色服务、8行为隔离、本地检索建库/冻结、10行计时仍未执行齐；搜索输出0。600预算三档与10pilot保留规则沿用追加4，不利用当前主测试数字定搜索范围。\n'
(R/'docs/300_ADDENDUM5_UNREACHABLE_OPERATION_AND_DEVICE_TRANSLATION_GATES.md').write_text(text)
files=[R/'docs/300_ADDENDUM5_UNREACHABLE_OPERATION_AND_DEVICE_TRANSLATION_GATES.md',U/'parallel_device20_plan.json',U/'translation_execution_20261111_plan.json',U/'translation_benign20.json',U/'calibration_full_grid_20261111.json',U/'calibration_full_grid_20261111.md',T/'unified300_parallel_device20.py',T/'unified300_translation_diagnostic.py',T/'unified300_export_calibration_grid.py']
with (R/'logs/prereg_publish.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
 for pth in files:
  dest=G/pth.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(pth,dest)
 rels=[str(pth.relative_to(R))for pth in files];subprocess.run(['git','add','--',*rels],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Freeze unreachable-alpha continuation and device/translation diagnostics before execution'],cwd=G,check=True,stdout=subprocess.DEVNULL);subprocess.run(['git','push'],cwd=G,check=True,capture_output=True)
print('FROZEN',H(files[0]),'COMMIT',subprocess.check_output(['git','rev-parse','--short','HEAD'],cwd=G,text=True).strip())
