from pathlib import Path
import json,hashlib,subprocess,datetime,os,numpy as np
R=Path('/data/HZX/Def');U=R/'results/audit/unified300'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
plan=load(U/'formal_training_assets_plan.json');assert sha(__file__)==plan['completion_worker_sha256'];assert sha(R/'tools/handoff_20261106/crossmodel287_train_generic.py')==plan['training_source_sha256']
for name,value in plan['target_files'].items():assert sha(R/name)==value
records=[]
for seed in [4,5]:
 p=U/f'formal_llama_s{seed}_config.json';assert sha(p)==plan['config_sha256'][str(seed)]
 c=load(p);assert sha(c['init_file'])==plan['initial_sha256'][str(seed)]
 subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(R/'tools/handoff_20261106/crossmodel287_train_generic.py'),'--config',str(p),'--device','cuda:0'],check=True)
 log=load(Path(c['out_dir'])/'train_log.json');v=np.load(Path(c['out_dir'])/'v.npy');assert len(log['losses'])==40;assert abs(float(np.linalg.norm(v))-5.21)<1e-4;records.append(dict(seed=seed,vector_file_sha256=sha(Path(c['out_dir'])/'v.npy'),log_sha256=sha(Path(c['out_dir'])/'train_log.json'),target_file_sha256=sha(c['targets_file']),norm=float(np.linalg.norm(v))))
p=U/'formal_llama_training_assets_complete.json';p.write_text(json.dumps(dict(utc=utc(),records=records,plan_sha256=sha(U/'formal_training_assets_plan.json'),new_calibration_outputs=0,new_test_outputs=0),indent=2)+'\n');print('ASSETS_COMPLETE',sha(p))
