from u300_schedule_prepare import *
import numpy as np,csv,statistics,datetime,shlex,importlib.metadata,tempfile
O=U/'takeover30'
def stats(a):return dict(N=len(a),median=float(np.median(a)) if a else None,p90=float(np.percentile(a,90)) if a else None,mean=float(np.mean(a)) if a else None,SD=float(np.std(a,ddof=1)) if len(a)>1 else None,min=min(a) if a else None,max=max(a) if a else None)
z=L(O/'first_divergence.json');pooled=[]
for m in ['llama','qwen']:
 for f in ['translate-fr','translate-zh-cn']:
  groups={}
  for group in ['learned','random']:
   rows=[r for x in z['language'] if x['model']==m and x['family']==f and x['group']==group for r in x['rows']];changed=[r['first_divergence_1based'] for r in rows if r['first_divergence_1based'] is not None];exact=[r['first_divergence_1based'] for r in rows if r['hash_verified_original_tokenization'] and r['first_divergence_1based'] is not None]
   groups[group]=dict(N_pairs=len(rows),changed=len(changed),retokenized_first_divergence=stats(changed),hash_verified_original_tokens_changed=stats(exact))
  pooled.append(dict(model=m,family=f,groups=groups))
save(O/'first_divergence_summary.json',dict(utc=utc(),groups=pooled,batch_noise={k:v for k,v in z['batch_noise'].items() if k!='rows'},limitation='Main all-row positions are text-retokenization diagnostics, not guaranteed original generation token positions. SHA-verified subset separately reported; noise and language panels differ.'))
q=L(O/'PAIR_completion_sources30.json');rows=list(csv.DictReader((O/'PAIR_per_row30.csv').open()));all88=L(U/'search88_alpha0_v19/PAIR/qwen/inputs.private.json');replay_root=U/'search88_alpha0_v19/PAIR/qwen/generation.private';replay=[]
for r in all88:
 p=replay_root/f"{r['id']:04d}.json";g=L(p);replay.append(g['result']['new_tokens'])
q['tier88']['actual_judged_completion_source']='Independent selected_prompt replay on main HF B4 zero-injection path, max_new_tokens=2400; search88_sorry_recompute reads this generation.private result.text.'
q['tier88']['independent_replay_N']=len(replay);q['tier88']['independent_replay_actual_new_tokens']=stats(replay);q['tier88']['independent_replay_at2400']=sum(n==2400 for n in replay)
q['tier220_new132']['actual_judged_completion_source']='pair220_sorry_gate.py reads /tmp/pair220/rows streams[-1][-1].completion, INTERNAL max150, not selected_prompt independent replay.'
tmp=Path('/tmp/pair220/rows');actual={L(p)['id'] for p in tmp.glob('*.json')};new={int(r['id']) for r in rows if r['group']=='tier220_new132'};q['temporary_gate_source_on_innet']=dict(path=str(tmp),exists=tmp.exists(),N=len(actual),matches_new132=actual==new);q.pop('temporary_gate_source_matches_new132',None)
q['SORRY_judge_backend']=dict(backend='vLLM',version=importlib.metadata.version('vllm'),dtype='bf16',enforce_eager=True,source_scripts={n:H(T/n) for n in ['pair220_sorry_gate.py','search88_sorry_recompute.py']});q['target_backend']='Hugging Face transformers, native template, zero-injection wrapper; search cap150 vs replay2400'
for p in sorted(U.glob('S1b_PAIR*.json')):
 h=H(p)
 if h in {r['plan_sha256'] for r in rows}:q.setdefault('plan_sources',[]).append(dict(plan=p.name,sha256=h,worker_sha256=L(p).get('worker_sha256')))
# Git HEAD-at-time is a historical repository reference, not proof of an unmodified working tree.
git=[]
code="""from pathlib import Path
import json
U=Path('/home/dell/Def/results/audit/unified300');out=[]
for p in (U/'queue_jobs').glob('*/descriptor.json'):
 z=json.loads(p.read_text());a=z.get('argv',[])
 if any('unified300_pair_progressive_v1.py' in v for v in a) and 'bulk' in a and 'qwen' in a:
  s=p.parent/'status.json';v=json.loads(s.read_text()) if s.exists() else {};out.append(dict(job=p.parent.name,descriptor_mtime_UTC=__import__('datetime').datetime.fromtimestamp(p.stat().st_mtime,__import__('datetime').timezone.utc).isoformat(),status={k:x for k,x in v.items() if k not in ['argv']},tier=a[-1]))
print(json.dumps(out))"""
jobs=json.loads(subprocess.check_output(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(code)],text=True))
for j in jobs:
 stamp=j['descriptor_mtime_UTC'];head=subprocess.check_output(['git','log','-1','--until='+stamp,'--format=%H %cI %s'],cwd=G,text=True).strip();j['repository_HEAD_at_launch_time']=head
 commits=subprocess.check_output(['git','log','--until='+stamp,'-1','--format=%H %cI %s','--','tools/handoff_20261106/unified300_pair_progressive_v1.py'],cwd=G,text=True).strip();j['last_controller_path_commit_at_launch_time']=commits
 if commits:
  blob=subprocess.check_output(['git','show',commits.split()[0]+':tools/handoff_20261106/unified300_pair_progressive_v1.py'],cwd=G);j['committed_controller_blob_sha256']=hashlib.sha256(blob).hexdigest()
git=jobs;q['controller_commit_comparison']=git;q['controller_version_limit']='Rows bind a frozen plan (including worker SHA); no independent runtime git/controller-version receipt. HEAD-at-time alone does not prove worktree state.';q['correction']='Previous two-tier same-plan statement omitted retained ten pilot rows with their original pilot plan SHA.'
q['utc']=utc();save(O/'PAIR_completion_sources30.json',q)
# Validate status failure behaviour against deliberately missing roots and malformed JSON.
with tempfile.TemporaryDirectory(prefix='cell_registry_test30_',dir=O) as td:
 r=Path(td);(r/'exists/cell/generation.private').mkdir(parents=True);p=r/'plan.json';save(p,dict(test=True));(r/'exists/cell/generation.private/1.json').write_text('{not json')
 reg=r/'registry.json';save(reg,dict(cells=[dict(cell_id='malformed',model='test',language='test',condition='alpha0',home_site='innet',output_root='exists/cell',record_dir='exists/cell/generation.private',declared_root='exists',expected_rows=1,plan_relative='plan.json',plan_sha256=H(p)),dict(cell_id='missing',model='test',language='test',condition='alpha0',home_site='innet',output_root='absent/cell',record_dir='absent/cell/generation.private',declared_root='absent',expected_rows=1,plan_relative='plan.json',plan_sha256=H(p))]));out=r/'out.json'
 run=subprocess.run(['/home/kemove/anaconda3/envs/HZX_GLA/bin/python',str(T/'u300_language_status30.py'),str(r),str(reg),str(out)],capture_output=True,text=True);v=L(out);assert run.returncode==2 and v['cells'][0]['disk_rows']==1 and v['cells'][0]['parseable_rows']==0 and v['cells'][1]['status']=='MISSING';save(O/'registry_status_selftest.json',dict(utc=utc(),passed=True,missing_root_exit=run.returncode,malformed_record_detected=True,no_judge_labels_accessed=True))
print('FIRST_DIVERGENCE_SUMMARY',json.dumps(pooled))
print('PAIR_SOURCE_SUMMARY',json.dumps(q,indent=2))
print('STATUS_SELFTEST_PASSED')
