from pathlib import Path
import json,hashlib,datetime,statistics,csv,io,importlib.metadata
import numpy as np
from transformers import AutoTokenizer
R=Path('/home/dell/Def');U=R/'results/audit/unified300';O=U/'takeover30';O.mkdir(exist_ok=True)
def L(p):return json.loads(p.read_text())
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,z):p.write_text(json.dumps(z,indent=2)+'\n')
def stats(v):return dict(N=len(v),mean=float(np.mean(v)),SD=float(np.std(v,ddof=1)) if len(v)>1 else None,median=float(np.median(v)),p90=float(np.percentile(v,90)),min=min(v),max=max(v))
P=L(U/'S1b_PAIR_progressive_v1.json');tok=AutoTokenizer.from_pretrained(P['target_models']['qwen']['path'],local_files_only=True)
A=L(U/'PAIR_progressive/qwen/tier88/complete.json')['selected_rows'];B=L(U/'PAIR_progressive/qwen/tier220/complete.json')['selected_rows'];new=set(B)-set(A);assert len(A)==88 and len(new)==132
G=U/'search88_alpha0_v19/PAIR/qwen/generation.private';report={};rows=[]
for name,ids in [('tier88',set(A)),('tier220_new132',new)]:
 lens=[];replaylens=[];secs=[];iters=[];queries=[];matches=0;missing=0
 for i in sorted(ids,key=int):
  source=R/B[i]['path'];assert H(source)==B[i]['sha256'];z=L(source);streams=z['streams'];last=streams[-1][-1];comp=last['completion'];n=len(tok.encode(comp,add_special_tokens=False));lens.append(n)
  niter=max(map(len,streams));nquery=sum(map(len,streams));iters.append(niter);queries.append(nquery);secs.append(z['seconds']);matches+=int(last['adv_prompt']==z['selected_prompt'])
  replay=G/(f'{int(i):04d}.json');rn=None
  if replay.exists():rn=L(replay)['result']['new_tokens'];replaylens.append(rn)
  rows.append(dict(id=int(i),group=name,row_file_sha256=H(source),plan_sha256=z['plan_sha256'],completed_UTC=z['utc'],estimated_started_UTC=(datetime.datetime.fromisoformat(z['utc'])-datetime.timedelta(seconds=z['seconds'])).isoformat(),iterations=niter,target_queries=nquery,target_batch_calls=z.get('call_counts',{}).get('target'),elapsed_seconds=z['seconds'],internal_last_stream_completion_retokenized_tokens=n,last_stream_matches_selected_prompt=last['adv_prompt']==z['selected_prompt'],independent_replay_new_tokens=rn))
 report[name]=dict(N=len(ids),internal_completion_source='search row streams[-1][-1].completion; target_max_n_tokens=150; not necessarily selected_prompt',internal_retokenized_length=stats(lens),internal_retokenized_equal150=sum(n==150 for n in lens),internal_retokenized_greater150=sum(n>150 for n in lens),internal_actual_generation_token_count_not_persisted=True,last_stream_prompt_matches_selected=matches,independent_replay_N=len(replaylens),independent_replay_actual_new_tokens=stats(replaylens) if replaylens else None,independent_replay_at2400=sum(n==2400 for n in replaylens),iterations=stats(iters),target_queries=stats(queries),target_queries_total=sum(queries),wall_seconds=stats(secs),plan_sha256s=sorted({r['plan_sha256'] for r in rows if r['group']==name}))
# The later 132-row scorer used only /tmp/pair220/rows. Confirm exact membership if retained.
tmp=Path('/tmp/pair220/rows');tmpids={str(L(p)['id']) for p in tmp.glob('*.json')};report['temporary_gate_source_matches_new132']=tmpids==new
report.update(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_plan_sha256=H(U/'S1b_PAIR_progressive_v1.json'),frozen_worker_sha256=P['worker_sha256'],current_worker_sha256=H(R/'tools/handoff_20261106/unified300_pair_progressive_v1.py'),formal_target_cap=P['formal']['target_max_n_tokens'],headlines_not_recomputed=True,tier440_remains_held=True)
for tier in [88,220]:
 D=U/'PAIR_progressive/qwen'/('tier'+str(tier));report['tier'+str(tier)+'_receipt']={k:v for k,v in L(D/'complete.json').items() if k not in ['selected_rows']}
save(O/'PAIR_completion_sources30.json',report)
s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);(O/'PAIR_per_row30.csv').write_text(s.getvalue().replace('\r\n','\n'))
print(json.dumps(report,indent=2))
