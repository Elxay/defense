from u300_schedule_prepare import *
import collections,importlib.metadata,shlex
O=U/'followup31';out=dict(utc=utc())
for method in ['PAIR','TAP']:
 d=U/'search88_alpha0_v19'/method/'qwen';comp=L(d/'complete.json');mets=[L(p) for p in (d/'metrics').glob('*.json')];out[method+'_replay_timing']=dict(elapsed_seconds=comp['elapsed_seconds'],measured_generation_seconds=sum(z['seconds'] for z in mets),N=comp['N'],zero20=L(d/'zero20.json') if (d/'zero20.json').exists() else None,gate=L(d/'gate_read.json') if (d/'gate_read.json').exists() else None)
 p=U/'search88_sorry_recompute'/(method+'_qwen.json')
 if p.exists():
  x=L(p);full=x['result']['full'];cut=x['result']['150'];a=dict(zip(full['ids'],full['labels']));b=dict(zip(cut['ids'],cut['labels']));assert set(a)==set(b)
  out[method+'_truncation']=dict(source_sha256=H(p),original_UTC=x['utc'],N=len(a),full_fulfilled=full['fulfilled'],cut150_fulfilled=cut['fulfilled'],full0_to_cut1_IDs=[i for i in a if a[i]==0 and b[i]==1],full1_to_cut0_IDs=[i for i in a if a[i]==1 and b[i]==0],full_invalid=full['invalid'],cut_invalid=cut['invalid'],judge_plan_sha256=x['judge_plan_sha256'])
encoding=[]
for m in ['llama','qwen']:
 for f in ['ascii','caesar','morse','atbash']:
  a=U/'encoding_alpha0_generated'/m/f/'alpha0/generation.private';b=U/'encoding_alpha0_generated_v2'/m/f/'alpha0/generation.private';A={p.name:p for p in a.glob('*.json')};B={p.name:p for p in b.glob('*.json')};keys=sorted(set(A)&set(B));same=0;prompts=0;sitesA=collections.Counter();sitesB=collections.Counter();sizesA=collections.Counter();sizesB=collections.Counter()
  for n in keys:
   x=L(A[n]);y=L(B[n]);same+=int(x['result']['text'].encode()==y['result']['text'].encode());prompts+=int(x['prompt_sha256']==y['prompt_sha256']);sitesA[x['signature'].get('site','unrecorded')]+=1;sitesB[y['signature'].get('site','unrecorded')]+=1;sizesA[x['result'].get('batch_size')]+=1;sizesB[y['result'].get('batch_size')]+=1
  encoding.append(dict(model=m,family=f,v1_N=len(A),v2_N=len(B),overlap_N=len(keys),response_byte_equal=same,equal_prompt_hash=prompts,reply_byte_equal_rate=same/len(keys) if keys else None,v1_sites=dict(sitesA),v2_sites=dict(sitesB),v1_batch_sizes=dict(sizesA),v2_batch_sizes=dict(sizesB)))
out['encoding_comparison']=encoding
state=L(U/'ready_queue/state.json')['tasks'];out['failed_registered_jobs']={k:v for k,v in state.items() if k.startswith('takeover30_') and v['state']=='failed'}
for k,v in out['failed_registered_jobs'].items():
 p=U/'queue_jobs'/v['job_dir']/'failure.json'
 if p.exists():v['failure']=L(p)
out['tap_gate_script_sha256']=H(T/'tap88_sorry_gate.py');out['vllm_version']=importlib.metadata.version('vllm')
# Published cost/utility summaries only; no broad score-cache traversal.
out['published_CPU_summaries']={n:L(U/n) for n in ['cost_main_benign.json','cost_read_aux2.json','cost_read_aux.json'] if (U/n).exists()}
out['coherence_assets']=[p.name for p in U.iterdir() if any(s in p.name.lower() for s in ['coher','mcal','mistral_label'])]
save(O/'CPU_audit.json',out)
print(json.dumps({k:v for k,v in out.items() if k!='published_CPU_summaries'},indent=2));print('PUBLISHED_CPU_SUMMARIES',json.dumps(out['published_CPU_summaries']))
