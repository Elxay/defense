"""Stage existing TAP numerical core behind a fresh gate and ordered88 queue."""
from pathlib import Path
import ast,copy,json,shutil
from u300_schedule_prepare import R,U,T,H,L,utc,save,publish
old=T/'unified300_tap_pilot_v4.py';pair=T/'unified300_pair_progressive_v1.py'
text=old.read_text();head=text[:text.index("assert L(U/'TAP_execution_gate_v4'/key/'complete.json')")]
head=head.replace('ThreadPoolExecutor,as_completed','ThreadPoolExecutor,as_completed,wait,FIRST_COMPLETED')
head=head.replace('S1b_TAP_frozen_v4.json','S1b_TAP_progressive_v1.json').replace("['gate','pilot']","['gate','bulk']")
head=head.replace('TAP_execution_gate_v4','TAP_progressive_gate_v1')
head=head.replace("else('TAP_pilot/'+key)","else('TAP_progressive/'+key+'/tier'+str(int(sys.argv[3])))")
head=head.replace("for order in [list(range(8)),list(reversed(range(8)))]:", "for order,workers in [(list(range(12)),8),(list(reversed(range(12))),4)]:")
head=head.replace('ThreadPoolExecutor(max_workers=8)as pool:rs=', 'ThreadPoolExecutor(max_workers=workers)as pool:rs=')
head=head.replace('behavior_count=8,orders=2,','behavior_count=12,orders=2,concurrency_orders=[8,4],')
tail=pair.read_text()[pair.read_text().index('tier=int(sys.argv[3]);'):]
tail=tail.replace('PAIR','TAP').replace('pair_fn','tap_fn').replace('streams=logs','source_logs=logs')
tail=tail.replace('assert tier in [88,220,440]',"assert tier==88,'Expansion remains locked pending the rule16 per-cell execution adapter'")
tail=tail.replace('independent_alpha0_fulfillment_not_read=True',
  'full_stage_alpha0_fulfillment_not_read=True,pilot10_alpha0_diagnostics_previously_read=True')
worker=T/'unified300_tap_progressive_v1.py';assert not worker.exists();worker.write_text(head+tail);compile(head+tail,str(worker),'exec')
def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
before,after=nodes(old),nodes(worker);names=['NativeConversation','Core','Port','source_function','prune_shuffle','build_object','handle']
assert all(before[n]==after[n] for n in names)
p=copy.deepcopy(L(U/'S1b_TAP_frozen_v4.json'));progress=copy.deepcopy(L(U/'S1b_PAIR_progressive_v1.json')['progressive'])
ip=U/'TAP_progressive_inputs.private.json';shutil.copy2(U/'PAIR_progressive_inputs.private.json',ip)
for model in ['llama','qwen']:
 progress['retained_pilot_rows'][model]={str(i):dict(path=str((U/'TAP_pilot'/model/'rows.private'/f'{i:04d}.json').relative_to(R)),
       sha256=H(U/'TAP_pilot'/model/'rows.private'/f'{i:04d}.json')) for i in p['pilot10_IDs']}
progress['full_inputs_sha256']=H(ip)
p.update(utc_frozen=utc(),worker_sha256=H(worker),progressive=progress,supported_tiers=[88],
 source_numerical_methods_unchanged=True,parent_pilot_plan_sha256=H(U/'S1b_TAP_frozen_v4.json'),
 rule16_sha256=H(U/'search_active_cell_budget_rule16.json'))
pp=U/'S1b_TAP_progressive_v1.json';save(pp,p)
parity=U/'TAP_progressive_v1_source_parity.json';save(parity,dict(utc=utc(),source_sha256=H(old),worker_sha256=H(worker),
 identical_AST_nodes=names,not_a_GPU_execution_gate=True,zero20_and_12_behavior8vs4_gate_still_required=True,
 all_prior_pilot_row_hashes_retained=True,search_algorithm_parameters_changed=False,expansion_above88_locked=True))
commit=publish([worker,pp,parity,Path(__file__)],'Stage TAP progressive88 with unchanged numerical core and cost-ordered fresh gates')
pub=U/'TAP_progressive_v1_publication.json';save(pub,dict(utc=utc(),published=True,commit=commit))
C=U/'ready_queue_catalog.json';cat=L(C);S=L(U/'ready_queue/state.json')['tasks']
for t in cat['tasks']:
 if t['id'] in ['AutoDAN_library_continue_v4','AutoDAN_qwen_pilot_v4','AutoDAN_llama_pilot_v4'] and S.get(t['id'],{}).get('state')!='running':t['priority']+=10
for model,rank in [('llama',18),('qwen',20)]:
 for mode,offset in [('gate',0),('bulk',1)]:
  args=['/data/ray/env/bin/python','{ROOT}/tools/handoff_20261106/unified300_tap_progressive_v1.py',mode,model]
  req=[dict(path=str(pub.relative_to(R)),key='published',value=True),dict(path='results/audit/unified300/rule16_publication.json',key='published',value=True)]
  folder=f'results/audit/unified300/TAP_progressive_gate_v1/{model}' if mode=='gate' else f'results/audit/unified300/TAP_progressive/{model}/tier88'
  if mode=='bulk':
   args.append('88');req.append(dict(path=f'results/audit/unified300/TAP_progressive_gate_v1/{model}/complete.json',key='passed',value=True))
  cat['tasks'].append(dict(id=f'TAP_progressive_{model}_{mode}_v1',priority=rank+offset,site='node01',gpus=[0,1],
      kind='fresh_search_execution_gate' if mode=='gate' else 'staged_alpha0_search',argv=args,requires=req,yieldable=False,sync_relpath=folder))
for q in [worker,pp,parity,pub,ip]:
 rel=str(q.relative_to(R))
 if rel not in cat['node_deploy_files']:cat['node_deploy_files'].append(rel)
save(C,cat)
print(json.dumps(dict(commit=commit,plan_sha256=H(pp),AST_nodes_unchanged=names,
 GPU_gate_status='pending; no claim of pass',ready_cost_order='PAIR-L,PAIR-Q,TAP-L,TAP-Q',tiers_above88_locked=True)))
