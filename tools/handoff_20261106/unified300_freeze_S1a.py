from pathlib import Path
import json,hashlib,datetime,shutil,fcntl,subprocess,numpy as np,torch
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';C=R/'results/audit/crossmodel287';G=R/'prereg_repo'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
exe=load(U/'S1a_freeze_execution_plan.json');assert sha(__file__)==exe['freeze_worker_sha256'];assert not (U/'S1a_manifest.json').exists()
for name,h in exe['code_sha256'].items():assert sha(R/name)==h,name
assert sha(R/'docs/300_S1A_SCOPE_SPEC.md')==exe['scope_sha256']
q4=load(U/'acceptance_cap2400_labels_v5/result.json');qB=4 if q4['models']['qwen']['cap2400_passed'] else 1
assert load(U/'acceptance_cap2400_labels/result.json')['models']['llama']['cap2400_passed']
for key in ['llama','qwen']:
 assert load(U/'acceptance_cap120_labels/result.json')['models'][key]['cap120_passed'];assert load(U/'ARC_forward_gate'/key/'result.json')['passed'];assert load(U/'history_search_gates'/key/'history20.json')['passed']
assert load(U/'formal_llama_training_assets_complete.json')['plan_sha256']==sha(U/'formal_training_assets_plan.json')
la=load(R/'results/style_intervention/old_recipe_targets.json');qw=load(C/'qwen_train_targets.json');u1=load(C/'qwen_U1_targets.private.json')
assert sha(C/'qwen_U1_targets.private.json')=='1442d90d5ae22decd8b932b1e4265df443aec94e3f427f8fdad72df26262f1c2'
assert la['ref_targets']==qw['ref_targets']==[x['target']for x in u1['fit']];assert qw['keep_targets']==[x['target']for x in u1['keep']]
assert [x['text']for x in qw['fit']]==[x['prompt']for x in u1['fit']];assert [x['text']for x in qw['keep']]==[x['prompt']for x in u1['keep']]
base=load(U/'S1a_calibration_CPU_binding.json');models=base['models'];frozen=U/'frozen_vectors_S1a';assert not frozen.exists();frozen.mkdir()
for key in ['llama','qwen']:
 spec=models[key];spec['long_generation_batch_size']=8 if key=='llama' else qB;spec['long_generation_core']='batched_injection300'if spec['long_generation_batch_size']>1 else'legacy gen.common.generate_with_injection';spec['learned_vectors']={}
 for seed in [3,4,5]:
  if key=='llama':original=C/'generic_equiv_llama_s3'if seed==3 else U/f'formal_vectors/llama/s{seed}'
  else:original=C/f'qwen_vec_s{seed}'
  log=load(original/'train_log.json');cfg=log['config'];assert (cfg['seed'],cfg['steps'],cfg['lr'],cfg['wpt'],cfg['layer'])==(seed,40,.005,.075,spec['layer'])
  target=Path(cfg['targets_file']);assert target==(R/'results/style_intervention/old_recipe_targets.json'if key=='llama' else C/'qwen_train_targets.json')
  v=np.load(original/'v.npy');assert hashlib.sha256(v.tobytes()).hexdigest()==log['v_sha256'];assert abs(float(np.linalg.norm(v))-(5.21 if key=='llama' else 32.352))<1e-3
  dst=frozen/f'{key}_s{seed}.npy';shutil.copy2(original/'v.npy',dst);spec['learned_vectors'][f's{seed}']=dict(path=str(dst),file_sha256=sha(dst),norm_float64=float(np.linalg.norm(v.astype('float64'))),dim=len(v),training_log_sha256=sha(original/'train_log.json'),training_config_sha256=log['config_sha256'],target_file_sha256=sha(target))
 spec['random_vectors']={}
 if key=='llama':sources=[R/f'results/audit/pair500/pair500_rand{i}.npy'for i in [0,1]];names=['rand0','rand1']
 else:
  sources=[Path(load(U/'acceptance_generation_plan.json')['models']['qwen']['vectors']['random']['path'])];generator=torch.Generator(device='cpu').manual_seed(61001);v=torch.randn(3584,generator=generator,dtype=torch.float32);v=v/v.norm()*float(np.linalg.norm(np.load(spec['learned_vectors']['s3']['path'])));new=U/'fixed_rand61001.npy';assert not new.exists();np.save(new,v.numpy());sources.append(new);names=['61000','61001']
 for src,name in zip(sources,names):
  dst=frozen/f'{key}_{name}.npy';shutil.copy2(src,dst);v=np.load(dst);assert abs(float(np.linalg.norm(v))-(5.21 if key=='llama' else 32.352))<1e-3;spec['random_vectors'][name]=dict(path=str(dst),file_sha256=sha(dst),norm_float64=float(np.linalg.norm(v.astype('float64'))),dim=len(v))
conditions=[dict(id='alpha0',seed=None,alpha=0)]+[dict(id=f's{s}_a'+str(a).replace('.','p'),seed=f's{s}',alpha=a)for s in [3,4,5]for a in [.10,.25,.5,.75,1.,1.25,1.5]];assert len(conditions)==22
refs=['calibration700_manifest.json','static_render_manifest.json','utility200_manifest_v2.json','overlap_flags.json','fixed_texts_manifest.json','human_language_audit.json','human_language_raw_source_binding.json','preread_eligibility_direction_language_plan.json']
gates=['acceptance_cap120_labels/result.json','acceptance_cap2400_labels/result.json','acceptance_cap2400_labels_v3/result.json','acceptance_cap2400_labels_v4/result.json','acceptance_cap2400_labels_v5/result.json','ARC_forward_gate/llama/result.json','ARC_forward_gate/qwen/result.json','history_search_gates/llama/history20.json','history_search_gates/qwen/history20.json']
t=utc();manifest=dict(utc_frozen=t,scope='S1a static/calibration/cost/utility rules; initial execution S2b only',S1b_frozen=False,search_outputs_allowed=False,code_sha256=exe['code_sha256'],scope_sha256=exe['scope_sha256'],calibration_sha256=sha(U/'calibration700.private.json'),calibration_IDs=base['IDs'],calibration_conditions=conditions,calibration_kind_counts=base['kind_counts'],models=models,WG_batch_plan_sha256=sha(U/'WG_batch_plan.json'),reference_sha256={n:sha(U/n)for n in refs},gate_sha256={n:sha(U/n)for n in gates},Qwen_B4_passed=qB==4,Qwen_long_path='B4 operational admission'if qB==4 else'fallback original B1; no independent batch-equivalence or self-cache-comparison claim',fixed_fallback_chain=[32,16,8,4,1],static_family_execution_locked_until_alpha_and_family_manifests=True,encoding_language_execution_locked=True,read_rule='Each model all22 WG caches before selection; main effect reads remain locked',new_main_outputs=0)
save(U/'S1a_manifest.json',manifest)
policy=(R/'docs/300_S1A_SCOPE_SPEC.md').read_text().replace('当前是待最终门完成的规格，不冒充S1a已冻结。正式冻结文件另记UTC、manifest SHA、push。','S1a正式冻结UTC：'+t+'。manifest SHA `'+sha(U/'S1a_manifest.json')+'`；S1b未冻结，搜索输出不允许。')
policy+='\n实际长路径：Llama B8，Qwen '+('B4通过操作门。'if qB==4 else'回原B1，B32/B16/B8/B4失败均保留；不以缓存自比伪称新独立门。')+'短120校准仍为Llama B16/Qwen B32，已有各100×3短门；ARC两模型B1，20×3门通过。所有语言/编码执行锁保留。\n'
doc=R/'docs/300_S1A_STATIC_CALIBRATION_COST_UTILITY.md';assert not doc.exists();doc.write_text(policy)
master=R/'docs/300_UNIFIED_PROTOCOL.md';lines=master.read_text().splitlines();lines[2]='状态：S1a已冻结，搜索S1b未冻结。当前依赖与措辞以追加3及300_S1A_STATIC_CALIBRATION_COST_UTILITY.md为准；末尾保留带UTC历史S0记录。搜索准备不阻塞独立准入的S2b；S1b前正式搜索输出（包括10行pilot）为0。';text='\n'.join(lines)+'\n'
text=text.replace('三者全负才写超出随机；否则依赖判官、三个数全列。不设pp阈值，不事后选择两判官。编码/非英语只描述，无升级。','人工风格覆盖时按追加3：至少两个合格主维度（有效配对点κ>=.60且两人工类别存在），所有合格维度负才升级，否则仅描述；所有数全报，WG有害不作第四判官。无匹配人工覆盖的DeepInception/前缀/拒答抑制/搜索沿原三者全负例外，并标该分布判官未验证。发布语言回复主要英语，新翻译链未验，语言/编码当前描述。')
text=text.replace('| S1 | 所有固定文本/目标串/搜索展开配置/角色模型/具体批次/样本ID/代码hash齐全；最终本文+manifest哈希push写日志 | 未齐不称完成冻结；只允许S0工程/人工参照工作 |','| S1a | 静态/校准/代价/效用规则及当前执行manifest冻结 | 逐家族门仍锁；只放行独立满足依赖 |\n| S1b | 搜索配置/目标串/角色/隔离计数/AutoDAN库执行manifest冻结 | 前置未齐不产任何搜索输出（含pilot） |').replace('| S2a | S1后，','| S2a | S1b后，').replace('| S2b | S1后，','| S2b | S1a后，').replace('| S3 | S1+S2b，','| S3 | S1a+S2b+家族执行门，')
text+='\nS1a冻结：'+t+'；文档SHA '+sha(doc)+'；manifest SHA '+sha(U/'S1a_manifest.json')+'。搜索S1b未冻结，任何搜索输出0。只启动新英语700校准；静态主效应不读。\n';master.write_text(text)
active=load(U/'active_protocol.json');active.update(updated_utc=t,stage='S1a',S1_frozen=False,S1a_frozen=True,S1b_frozen=False,S1a_sha256=sha(doc),S1a_manifest_sha256=sha(U/'S1a_manifest.json'),master_candidate_sha256=sha(master),new_test_generation_allowed=False,new_calibration_generation_allowed=True,search_outputs_allowed=False,Qwen_long_batch_candidate=qB,long_path_admitted=True,pending=['S1b search execution prerequisites','model all22 caches before alpha selection','per-family static/prefill/decoder/translation/judge execution gates'],allowed_work=['S0 preparation','S2b700 calibration and WG cache scoring','family-specific preread execution preparation']);save(U/'active_protocol.json',active)
receipt=dict(utc=t,S1a_frozen=True,S1b_frozen=False,S1a_doc_sha256=sha(doc),manifest_sha256=sha(U/'S1a_manifest.json'),master_sha256=sha(master),freeze_execution_plan_sha256=sha(U/'S1a_freeze_execution_plan.json'),long_batches={'llama':8,'qwen':qB},short_calibration_batches={'llama':16,'qwen':32},search_outputs=0,main_test_outputs=0,per_family_gates_remain=True);save(U/'S1a_freeze_receipt.json',receipt)
public=[doc,master,U/'S1a_manifest.json',U/'S1a_freeze_receipt.json',U/'active_protocol.json',U/'formal_llama_training_assets_complete.json',U/'ARC_forward_gate/llama/result.json',U/'ARC_forward_gate/qwen/result.json',U/'human_language_audit.json',U/'batch_disagreement_directions.json',U/'acceptance_cap2400_labels_v5/result.json']
for n in ['OPS_LOG','PREREG_LOG.txt']:
 with (R/'docs'/n).open('a')as f:f.write(t+' S1a frozen per user dependency split; S1b closed, search0. Qwen longB'+str(qB)+'; ARC20x3 both pass. Language human replies primarilyEnglish; no translation-chain validity claimed. New700 calibration may start only, effects unread. docSHA='+sha(doc)+' manifestSHA='+sha(U/'S1a_manifest.json')+'\n')
 public.append(R/'docs'/n)
with (R/'logs/prereg_publish.lock').open('a')as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip();rels=[]
 for f in public:
  rel=f.relative_to(R);dest=G/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);rels.append(str(rel))
 subprocess.run(['git','add','--',*rels],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True);subprocess.run(['git','commit','-m','Freeze S1a separately from locked search S1b and admit English700 calibration'],cwd=G,check=True);subprocess.run(['git','push','origin','HEAD'],cwd=G,check=True)
print(json.dumps(receipt,indent=2))
