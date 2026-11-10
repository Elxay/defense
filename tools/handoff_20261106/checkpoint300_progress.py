from pathlib import Path
import datetime,fcntl,hashlib,json,shutil,subprocess
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';G=R/'prereg_repo'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
admission=load(U/'utility_cpu_admission_v2.json')
assert all(x['passed']for x in admission['ARC_native_prefix_checks'].values())
old=load(U/'utility200_manifest.json');updated=json.loads(json.dumps(old))
updated.update(utc=now,previous_manifest_sha256=sha(U/'utility200_manifest.json'),
    correction='Derive option IDs from the actual native prefix plus letter, not the standalone letter tokenizer call; no model forward or accuracy observed')
for k,v in admission['ARC_native_prefix_checks'].items():
 updated['ARC_CPU_token_checks'][k]['letters']=v['actual_letters']
 updated['ARC_CPU_token_checks'][k]['joint_native_prefix_checks']=v['n']
 updated['ARC_CPU_token_checks'][k]['joint_native_prefix_passed']=v['passed']
updated['GSM_parser_code_sha256']=admission['scoring_code_sha256']
save(U/'utility200_manifest_v2.json',updated)
progress={'utc':now,'stage':'S0','S1_frozen':False,'test_generation_allowed':False,
 'human_reference_result_sha256':sha(U/'human_agreement_results.json'),
 'utility_cpu_admission_sha256':sha(U/'utility_cpu_admission_v2.json'),
 'utility_manifest_sha256':sha(U/'utility200_manifest_v2.json'),
 'static_render_manifest_sha256':sha(U/'static_render_manifest.json'),
 'throughput':{},'GPU_snapshot':{}}
public=[]
for model in ['llama','qwen']:
 d=U/'throughput'/model;live=load(d/'live.json');gate=load(d/'single_core_gate20.json')
 progress['throughput'][model]={'live':live,'single_core_zero20':gate['passed'],'short120':[]}
 public += [d/'single_core_gate20.json',d/'runtime.json']
 for p in sorted(d.glob('cap120_B*.json')):
  v=load(p);progress['throughput'][model]['short120'].append({k:v[k]for k in ['batch_size','seconds','tokens_per_second','rows_per_hour','conservative_headroom_bytes','headroom_at_least_3GiB']});public.append(p)
 # Any 2400 results available now are timing metadata only, not scored effects.
 for p in sorted(d.glob('cap2400_B*.json')):public.append(p)
for host in ['innet','node01']:
 command=['nvidia-smi','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader']
 if host=='node01':command=['ssh','node01',*command]
 progress['GPU_snapshot'][host]=subprocess.check_output(command,text=True).strip().splitlines()
doc=R/'docs/300_UNIFIED_PROTOCOL.md';text=doc.read_text()
text=text.replace('- [ ] GSM执行解析与ARC注入前向验收。','- [x] GSM固定解析实现/200个gold格式回环与缺失/歧义边界测试；ARC四模型200题真实原生前缀联合编码均通过。\n- [ ] ARC注入前向验收。')
text += '\nS0 CPU执行核对（'+now+'）：19个静态输入格×440行×四模型的渲染/输入ID哈希已保存（搜索提示待生成，不在这19格）；四模型P2原生token前缀均保持不变。ASCII变换中，仅提示超过4096 token的行数依次为Llama1、Qwen3、Gemma3、Mistral3，最大4644/8324/8325/8351；这只是输入长度标记，不等于实际位置上限溢出，不自动记INVALID，不截断。完整输入加回复长度在评分时另记。\n'
text += '\nARC编码纠正：第一次200题CPU核对显示Mistral单独编码字母的ID不适用于原生前缀之后；保留失败记录，采用联合渲染实际后缀A/B/C/D=[29509,29528,29511,29525]，200×4全部单token且不同。其余三模型映射不变。utility200_manifest_v2.json取代旧效用执行映射；无模型前向、无准确率读取。GSM仅接受最后一个####后的完整十进制数字，无法解析计错，不回退选数。\n'
text += '\n批路径新增接口相对旧单条零向量20/20字节门：Llama和Qwen均通过。短120-token的B1/4/8/16/32吞吐已测；长2400-token仍在测，100×3 WG/v2标签门和历史同批重放尚未通过，不以短输出速度外推主评测成本，不称S1完成。\n'
doc.write_text(text);progress['master_candidate_sha256']=sha(doc)
active=load(U/'active_protocol.json');active.update(utc=now,master_candidate_sha256=sha(doc));save(U/'active_protocol.json',active)
save(U/'S0_progress_20261110.json',progress)
line=now+' unified300 S0 progress; both new-core versus legacy B1 zero20 gates passed. Short120 throughput measured; long2400 and 100x3 labels remain pending. CPU prefix/P2 render passed four models; ARC Mistral joint-prefix token correction before any forward; older receipt retained. candidate='+sha(doc)+'; no S1/test generation admission.\n'
for n in ['OPS_LOG','PREREG_LOG.txt']:
 with (R/'docs'/n).open('a')as f:f.write(line)
files=[doc,R/'docs/OPS_LOG',R/'docs/PREREG_LOG.txt']
files += [U/n for n in ['utility200_manifest_v2.json','utility_cpu_admission.json','utility_cpu_admission_v2.json',
 'static_render_manifest.json','S0_progress_20261110.json','active_protocol.json']]
files += [R/'tools/handoff_20261106'/n for n in ['utility300_scoring.py','utility300_cpu_admission.py','utility300_cpu_admission_v2.py','unified300_static_render.py','checkpoint300_progress.py']]
files+=public
with (R/'logs/prereg_publish.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
 paths=[]
 for src in files:
  rel=src.relative_to(R);dst=G/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);paths.append(str(rel))
 subprocess.run(['git','add','--',*paths],cwd=G,check=True)
 subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True)
 subprocess.run(['git','commit','-m','Record fixed static renders, utility token correction and short batch throughput; retain S1 lock'],cwd=G,check=True)
 subprocess.run(['git','push','origin','HEAD'],cwd=G,check=True)
print('MASTER_SHA',sha(doc));print('COMMIT',subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip())
