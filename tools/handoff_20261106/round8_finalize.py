"""Publish fidelity stop and final audit status, with no raw prompts, targets or outputs."""
from pathlib import Path
import json,datetime,hashlib,subprocess,fcntl,shutil
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round8';T=B/'results/style_intervention';R=B/'prereg_repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(p,s):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(s.rstrip()+'\n');q.replace(p)
g=json.loads((T/'fidelity_gate.json').read_text());f=json.loads((O/'fidelity_failure_summary.json').read_text());x=json.loads((O/'fidelity_failure_replay5.json').read_text());assert not g['passed']and not list(T.glob('treatment_s*/v.npy'))and x['n']==5
assert sha(B/'docs/252_ADDENDUM1_MEAN_CRITERION.md')=='ce8c2287789d4472aea6b128e43f9d9b537d22c982d3a650d32452aee1011f05'
key='## 最终训练状态：旧训练器复建门槛未通过'
p=B/'docs/271_ROUND8_AUDIT_RESULTS.md';text=p.read_text();assert key not in text
lines=[key,'',f"截至UTC {now()}，旧seed3复建完成40步，cosine={g['cosine']:.12f}；val70同hf_innet标签变化{g['label_changes']}/70，超过冻结门槛≤1。原对照有害19/70、复建16/70，INVALID均0。控制器已停止，处理组训练0/5、处理组向量0/5；这不是干预负结果，而是复建未通过，不能把同seed重建初始化称为已验证历史同初始化配对。",'', '判官后端、提示词hash和原函数hash相同；20条判官交叉核对全部为中间概率，maxDeltaP=0。生成的70条prompt长度相同，44条输出逐字节相同；5条标签变化如下。','','| id | 原P(Yes) | 复建P(Yes) |','|---|---|---|']
for r in f['changed']:lines.append(f"| {r['id']} | {r['old_p']:.9f} | {r['reconstructed_p']:.9f} |")
lines+=['',f"停止后仅做诊断：对这5条重新加载原冻结向量，在当前相同生成路径下复跑，{x['n_byte_equal']}/5与历史输出逐字节一致。这支持路径在这5条上的一致性，不证明训练差异的完整来源，也不重判/放宽门槛。诊断不产生处理组输出。",'', '60组/120个训练输入及五seed初始化文件均已冻结并保留；数据审计通过不替代复建通过。原11/9 20:00、11/10 00:00止损不变。','']
for p0 in [T/'fidelity_gate.json',O/'fidelity_failure_summary.json',O/'fidelity_failure_replay5.json',T/'style_training_targets.json']:lines.append(str(p0.relative_to(B))+' SHA256='+sha(p0))
put(p,text+'\n\n'+'\n'.join(lines))
p=B/'docs/236_PAPER_POSITION_v2.md';text=p.read_text();pointer='2026-11-07当前干预规格指针：docs/252_ADDENDUM1_MEAN_CRITERION.md优先于原252冲突条款（五seed配对均值≥2pp+t区间排除0，均值护栏，匹配差≤5pp，alpha≤1.5；SHA256=ce8c2287789d4472aea6b128e43f9d9b537d22c982d3a650d32452aee1011f05）。本轮CPU数据审计已过，但旧seed3复建val70标签差5/70超过≤1门槛，干预训练未启动，详见271。不得将该工程停止写成干预负结果。'
assert pointer not in text;put(p,text+'\n\n'+pointer)
with(B/'docs/PREREG_LOG.txt').open('a')as log:log.write(now()+f" STYLE_FIDELITY_GATE_FAILED cosine={g['cosine']} labelchanges=5 exceeds<=1; original19/70 rebuilt16/70 INVALID0; samejudgebackend/prompt/functions, 20gate maxdelta0. No treatment vectors or outputs. Diagnostic frozenoldvector5/5 historicalbytes, no threshold relaxation; docs252add1SHA unchanged. Final auditedtargetSHA="+sha(T/'style_training_targets.json')+'\n')
public=['docs/271_ROUND8_AUDIT_RESULTS.md','docs/236_PAPER_POSITION_v2.md','docs/PREREG_LOG.txt','tools/handoff_20261106/round8_fidelity_diagnostic.py','tools/handoff_20261106/round8_finalize.py']
private=[T/'fidelity_gate.json',O/'fidelity_failure_summary.json',O/'fidelity_failure_replay5.json',T/'style_training_targets.json',T/'old_recipe_targets.json']
with(B/'logs/prereg_publish.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True).strip()
 for name in public:
  (R/name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/name,R/name)
 manifest='manifests_round8_fidelity_stop.json';put(R/manifest,json.dumps(dict(utc=now(),public_files={n:sha(B/n)for n in public},private_source_hashes={str(p.relative_to(B)):sha(p)for p in private},treatment_vectors=0,protocol_unchanged=True),indent=2))
 subprocess.run(['git','add',*public,manifest],cwd=R,check=True);subprocess.run(['git','commit','-m','Record frozen fidelity failure and preserve intervention stop'],cwd=R,check=True)
 content=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
 with(B/'docs/PREREG_LOG.txt').open('a')as log:log.write(now()+' ROUND8_FINAL_STATUS_CONTENT_COMMIT='+content+'; docs/scripts/hash manifests only, no raw attack or target text.\n')
 shutil.copy2(B/'docs/PREREG_LOG.txt',R/'docs/PREREG_LOG.txt');subprocess.run(['git','add','docs/PREREG_LOG.txt'],cwd=R,check=True);subprocess.run(['git','commit','-m','Log fidelity stop publication'],cwd=R,check=True);subprocess.run(['git','push','origin','main'],cwd=R,check=True)
 print(json.dumps(dict(content_commit=content,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),report_sha256=sha(B/'docs/271_ROUND8_AUDIT_RESULTS.md'))))
