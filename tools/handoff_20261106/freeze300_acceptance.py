from pathlib import Path
import datetime,fcntl,hashlib,json,shutil,subprocess
import numpy as np
import torch
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';G=R/'prereg_repo'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
now=datetime.datetime.now(datetime.timezone.utc).isoformat();path=U/'acceptance_generation_plan.json'
assert not path.exists()and not (U/'acceptance').exists()
base=load(U/'throughput_plan.json');models=base['models'];C=R/'results/audit/crossmodel287'
learned={'llama':C/'U1_llama_seed3_check/v.npy','qwen':C/'qwen_vec_s3/v.npy'}
randoms={'llama':R/'results/audit/pair500/pair500_rand0.npy','qwen':U/'engineering_rand61000.npy'}
v=np.load(learned['qwen']);gen=torch.Generator(device='cpu').manual_seed(61000);direction=torch.randn(v.size,generator=gen,dtype=torch.float32);direction=direction/direction.norm()*float(np.linalg.norm(v))
assert not randoms['qwen'].exists();np.save(randoms['qwen'],direction.numpy())
for key,spec in models.items():
 complete=load(U/'throughput'/key/'throughput_complete.json')
 assert complete['no_test_effects_read']
 spec['batch_by_cap']=complete['candidate_batch_sizes']
 spec['vectors']={cond:{'path':str(p),'sha256':sha(p),'norm_float64':float(np.linalg.norm(np.load(p).astype(np.float64)))}for cond,p in [('s3',learned[key]),('random',randoms[key])]}
 assert abs(spec['vectors']['s3']['norm_float64']-spec['vectors']['random']['norm_float64'])<1e-4
plan={'utc_frozen':now,'S0_engineering_only':True,'formal_test_generation_allowed':False,
 'calibration_sha256':base['calibration_sha256'],'IDs100':base['acceptance_ids100'],'sample_seed':20261241,
 'models':models,'caps':[120,2400],'engineering_alpha':1,'conditions':['alpha0','s3','random'],
 'worker_sha256':sha(R/'tools/handoff_20261106/unified300_acceptance_generate.py'),
 'legacy_core_sha256':base['legacy_core_sha256'],'batch_core_sha256':base['batch_core_sha256'],
 'random_Qwen_engineering':'torch CPU float32 Gaussian generator seed61000, normalized to the frozen s3 norm; no test-result choice; formal binding remains S1/S2b responsibility',
 'reference_vectors':'existing fixed-U1 seed3; engineering references do not select alpha or declare new formal training complete',
 'new_acceptance_outputs_at_freeze':0,'scoring_status':'not run; generation completion does not admit batching',
 'label_gate':'each cap and each condition WG refusal and v2 paired B1-to-batch disagreement <=2/100; worst-case INVALID; no absolute refusal rates read for selection',
 'failure_order':'preserve candidate and test next smaller B from fixed grid; no resource or label failure may admit formal generation',
 'history20_is_separate':True}
save(path,plan)
doc=R/'docs/300_UNIFIED_PROTOCOL.md';text=doc.read_text()
text+='\nS0吞吐实测完成（'+now+'，固定32条校准工程提示）：2400上限Llama B1/B4/B8/B16/B32 tokens/s=38.63/92.90/161.79/204.05/204.78；B32显存余量仅0.71GiB不准入，按80%与3GiB规则候选B16。Qwen对应44.68/121.71/189.57/231.05/300.08，候选B32，余量5.44GiB。候选相对B1 token吞吐约5.28/6.72倍，只对该工程面板成立，不能统一折算全部家族成本。120上限候选同为16/32。\n'
text+='\nWG原单条human缓存20条，在B1/4/8/16下逐字节全部20/20一致，三个字段亦全相同；按同一80%及3GiB规则，候选WG B8（tokens/s=78.72；B16=98.04）。这是固定20条工程门，不外推判官准确性；人工参照accuracy结果不因批门而改写。\n'
text+='\n100×3标签验收生成在acceptance_generation_plan.json预冻后启动，120与2400两场景都做；固定alpha0、U1来源s3、第一随机参照，工程alpha1，三个条件同一100提示/顺序。只读取路径间拒答翻转，不读取绝对拒答率用来选alpha；固定参考向量不是新协议正式向量训练/alpha冻结完成声明。标签门、历史同批20复现和搜索补丁20门仍分别关闭。PAIR/TAP源码HF停止符含右花括号，搜索补丁门必须复制同一显式EOS，不能由通用B1零向量门替代。\n'
doc.write_text(text)
active=load(U/'active_protocol.json');active.update(utc=now,master_candidate_sha256=sha(doc),S1_frozen=False,new_test_generation_allowed=False);save(U/'active_protocol.json',active)
record={'utc':now,'master_candidate_sha256':sha(doc),'acceptance_plan_sha256':sha(path),'WG_batch_plan_sha256':sha(U/'WG_batch_plan.json'),'WG_batch_result_sha256':sha(U/'WG_batch/complete.json'),'target_candidates':{k:v['batch_by_cap']for k,v in models.items()},'stage':'S0; 100x3 label gate not yet run'}
save(U/'throughput_summary_and_acceptance_start.json',record)
line=now+' unified300 S0 target throughput complete: Llama B16,Qwen B32 provisional, long tokens/s204.05/300.08; WG candidateB8 strict20bytesallpass. Freeze100x3 generation before any panel nonzero outputs; alpha1 engineering only, no absolute calibration/test rates read. S1 remains closed; master='+sha(doc)+'; acceptanceplan='+sha(path)+'\n'
for n in ['OPS_LOG','PREREG_LOG.txt']:
 with (R/'docs'/n).open('a')as f:f.write(line)
files=[doc,R/'docs/OPS_LOG',R/'docs/PREREG_LOG.txt',path,U/'throughput_summary_and_acceptance_start.json',U/'active_protocol.json']
files += list((U/'WG_batch').glob('*.json'))
for key in ['llama','qwen']:
 files += list((U/'throughput'/key).glob('cap2400_B*.json'))+[U/'throughput'/key/'throughput_complete.json']
files += [R/'tools/handoff_20261106'/n for n in ['unified300_acceptance_generate.py','launch300_acceptance.sh','freeze300_acceptance.py']]
with (R/'logs/prereg_publish.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
 rels=[]
 for p in files:
  rel=p.relative_to(R);dst=G/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);rels.append(str(rel))
 subprocess.run(['git','add','--',*rels],cwd=G,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True)
 subprocess.run(['git','commit','-m','Record long batch throughput and exact WG gate; freeze fixed 100x3 engineering acceptance before generation'],cwd=G,check=True)
 subprocess.run(['git','push','origin','HEAD'],cwd=G,check=True)
print(json.dumps(record,indent=2));print('COMMIT',subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip())
