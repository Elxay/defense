from u300_schedule_prepare import *
import sys,time,shlex,collections,math,os
sys.path.insert(0,str(T));from u300_alpha0_cache_scope20 import load_alpha0_cache
sys.path.insert(0,str(R/'src'));from judge.refusal import new_rule
O=U/'followup35'
def compare_gate(wave,cap):
 W=U/'score_waves'/wave;S=U/'Mistral_gate_scores35'/wave
 if not (S/'complete.json').exists():return None
 rows=L(W/'inputs.private.json');by={r['id']:r for r in rows};batches=L(W/'manifest.json')['batches'];schedule=H(U/'Mistral_gate35_scoring_plan.json');cache={}
 def row(B,c,i):
  id=f'{cap}:B{B}:{c}:{i}'
  if id in cache:return cache[id]
  r=by[id];fields={k:r[k] for k in ['generation_sha256','prompt_sha256','response_sha256','behavior_sha256']};fields.update(preprocessing_sha256=r.get('preprocessing_sha256'),judge='WG',schedule_sha256=schedule);key=hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest();z=L(S/'WG/records.private'/(key+'.json'));assert z['generation_sha256']==r['generation_sha256'] and z['condition']==r['condition'];val=({'yes':1,'no':0}.get(z['labels'].get('Response refusal')),bool(new_rule(r['response'])));cache[id]=val;return val
 candidates=[];selected=1
 for B in [8,4]:
  if B not in batches:
   failures=[L(p) for p in (U/'Mistral_gate35'/f'cap{cap}'/f'B{B}').glob('*/memory_failed.json')];candidates.append(dict(B=B,available=False,memory_failure=failures));continue
  cells=[]
  for c in ['alpha0','s3','61000']:
   lo=hi=b_only=s_only=v_bonly=v_sonly=0;unknown=[]
   for i in range(100):
    sw,sv=row(1,c,i);bw,bv=row(B,c,i)
    if sw is None or bw is None:hi+=1;unknown.append(i)
    else:lo+=sw!=bw;hi+=sw!=bw;b_only+=bw==1 and sw==0;s_only+=bw==0 and sw==1
    v_bonly+=bv and not sv;v_sonly+=sv and not bv
   n=b_only+s_only;p=1. if n==0 else min(1.,2*sum(math.comb(n,k) for k in range(min(b_only,s_only)+1))/2**n);passed=hi<=2 and v_bonly+v_sonly<=2;cells.append(dict(condition=c,N=100,WG_change_bounds=[lo,hi],WG_batch_only=b_only,WG_single_only=s_only,WG_INVALID_pair_IDs=unknown,WG_McNemar_exact_p=p,v2_changes=v_bonly+v_sonly,v2_batch_only=v_bonly,v2_single_only=v_sonly,passed=passed))
  okay=all(c['passed'] for c in cells);candidates.append(dict(B=B,available=True,cells=cells,passed=okay))
  if okay:selected=B;break
 out=dict(utc=utc(),cap=cap,N_per_condition=100,conditions=['alpha0','s3','61000'],alpha=1.5,selected_B=selected,candidates=candidates,threshold=2,B1_fallback=selected==1,scope='engineering only; no alpha selection statistics',wave_manifest_sha256=H(W/'manifest.json'))
 save(O/(f'Mistral_gate{cap}_read.json' if not wave.endswith('_B4') else 'Mistral_gate2400_B4_read.json'),out);return out
def cycle():
 # Make encoding source acceptance deterministic and atomic, without reading scores.
 result=O/'encoding_probe/result.json';accepted=O/'encoding_v1_acceptance.json'
 if result.exists() and not accepted.exists():
  z=L(result)
  if z['passed']:
   assert z['N_selected']==20 and z['N_covered']==32;registry=L(U/'followup34/encoding_registry34.json')
   for cell in registry['cells']:
    if cell['model']=='qwen':cell.update(source='single_record_directory',record_dir='results/audit/unified300/encoding_alpha0_generated/qwen/'+cell['family']+'/alpha0/generation.private',legacy_v1_status='accepted_main_after35',acceptance_probe_sha256=H(result))
   registry.update(utc=utc(),supersedes_registry_sha256=H(U/'followup34/encoding_registry34.json'));save(O/'encoding_registry35.json',registry);save(accepted,dict(utc=utc(),admitted=True,model='qwen',N_cells=4,N_rows=1760,probe_sha256=H(result),selected20_exact=True,covered32_exact=True,all_current_overlaps_exact=True,registry_sha256=H(O/'encoding_registry35.json'),source_v1_preserved=True,v2_kept_as_engineering_replica=True,no_judge_labels_read=True))
  else:save(O/'QWEN_V2_CONTINUE.json',dict(utc=utc(),admitted=True,reason='frozen cross-node byte reference failed; no v1 acceptance'));save(accepted,dict(utc=utc(),admitted=False,probe_sha256=H(result)))
 # Stage the short gate wave while the target GPU continues long generation.
 for wave in ['Mistral_gate35_short']:
  W=U/'score_waves'/wave;receipt=O/(wave+'_node_staged.json')
  if (W/'manifest.json').exists() and not receipt.exists():
   for n in ['inputs.private.json','manifest.json']:
    dest='/home/dell/Def/results/audit/unified300/score_waves/'+wave+'/'+n;subprocess.run(['ssh','node01','mkdir -p '+shlex.quote(str(Path(dest).parent))],check=True,capture_output=True);subprocess.run(['scp',str(W/n),'node01:'+dest],check=True,capture_output=True)
   save(receipt,dict(utc=utc(),staged=True,manifest_sha256=H(W/'manifest.json'),inputs_sha256=H(W/'inputs.private.json')))
 for wave,cap in [('Mistral_gate35_short',120),('Mistral_gate35_long',2400),('Mistral_gate35_long_B4',2400)]:
  out=O/(f'Mistral_gate{cap}_read.json' if wave!='Mistral_gate35_long_B4' else 'Mistral_gate2400_B4_read.json')
  if (U/'Mistral_gate_scores35'/wave/'complete.json').exists() and not out.exists():
   z=compare_gate(wave,cap)
   if wave=='Mistral_gate35_long_B4' and z:save(out,z)
   if z and cap==2400 and z['selected_B']==1 and 4 not in L(U/'score_waves'/wave/'manifest.json')['batches'] and 8 in L(U/'score_waves'/wave/'manifest.json')['batches']:save(O/'Mistral_long_B4_required.json',dict(utc=utc(),required=True,source_read_sha256=H(O/'Mistral_gate2400_read.json')))
 # Existing translated alpha0 is enough for its own main generation gate.
 p=U/'language_gate33/llama_translate-mr_alpha0.json';plan=U/'Indian_main30_llama_translate-mr.json'
 if p.exists():
  g=L(p);cfg=L(plan)['models']['llama']['families']['translate-mr'];dest=R/cfg['external_SORRY_gate_relative']
  if not dest.exists() or L(dest).get('source_gate_sha256')!=H(p):save(dest,dict(**g,admitted=g['gate'] in ['active','INVALID_crossing_continue'],source_gate_sha256=H(p),numerical_plan_sha256=H(plan),utc_compatibility_binding=utc()))
 # Exploratory labels are direct-addressed only after each complete group.
 for spec in L(O/'exploratory_specs.json')['groups']:
  key=spec['key'];W=U/'score_waves'/('exploratory_last35_'+key);out=O/('exploratory_result_'+key+'.json')
  if (W/'SORRY_complete.json').exists() and not out.exists():
   rows=L(W/'inputs.private.json');labels=[load_alpha0_cache(R,r,H(U/'scoring_schedule_v1.json'))['label'] for r in rows];save(out,dict(utc=utc(),group=key,N=len(rows),fulfilled=sum(v==1 for v in labels),INVALID_IDs=[r['id'] for r,v in zip(rows,labels) if v not in [0,1]],exploratory=True,main_gate_unchanged=True,manifest_sha256=H(W/'manifest.json')))
 save(O/'coordinator_live.json',dict(utc=utc(),PID=os.getpid(),scope='only engineering and authorized exploratory alpha0; no protected effects'))
if __name__=='__main__':
 while True:
  try:cycle()
  except Exception as e:save(O/'coordinator_error.json',dict(utc=utc(),type=type(e).__name__,reason=str(e)[:500]))
  time.sleep(15)
