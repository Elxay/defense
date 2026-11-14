from u300_schedule_prepare import *
import datetime,statistics,csv,io,math,collections,sys
O=U/'followup36';D=U/'Mistral_gate35';rows=[];summ=[]
def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def one(D,c,start,kind):
 ps=sorted((D/c/'generation.private').glob('*.json'));previous=start;records=[]
 for p in ps:
  z=L(p);now=p.stat().st_mtime_ns/1e9;seconds=now-previous if previous is not None else None;previous=now;r=dict(scope=kind,condition=c,id=z['id'],wall_between_atomic_writes_seconds=seconds,mtime_UTC=datetime.datetime.fromtimestamp(now,datetime.timezone.utc).isoformat(),new_tokens=z['result']['new_tokens'],source_sha256=H(p),source_path=str(p.relative_to(R)));records.append(r)
 values=[r['wall_between_atomic_writes_seconds'] for r in records if r['wall_between_atomic_writes_seconds'] is not None];summ.append(dict(scope=kind,condition=c,N=len(ps),completed=(D/c/'complete.json').exists(),mean_seconds=statistics.mean(values) if values else None,median_seconds=statistics.median(values) if values else None,p90_seconds=sorted(values)[max(0,math.ceil(.9*len(values))-1)] if values else None,max_seconds=max(values) if values else None,mean_new_tokens=statistics.mean(r['new_tokens'] for r in records) if records else None,basis='original in-place atomic-record mtime intervals; includes I/O/loop, not pure CUDA or exact generate-call timing'));rows.extend(records)
base=D/'cap2400/B1';reference=D/'innet0_to2_reference20.json';start=dt(L(reference)['utc'])
for c in ['alpha0','s3','61000']:
 one(base,c,start,'Mistral2400_B1')
 comp=base/c/'complete.json';start=dt(L(comp)['utc']) if comp.exists() else None
cal=U/'Mistral_calibration_B1_35';one(cal,'alpha0',dt(L(cal/'reference20.json')['utc']),'Mistral_calibration_B1_120')
save(O/'Mistral_row_wall_metadata.json',dict(utc=utc(),groups=summ,rows=rows))
b=io.StringIO();cols=['scope','condition','id','wall_between_atomic_writes_seconds','mtime_UTC','new_tokens','source_sha256','source_path'];w=csv.DictWriter(b,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows(rows);(O/'Mistral_per_row_wall.csv').write_text(b.getvalue())
state=L(U/'ready_queue/state.json')['tasks'];s=state['Mistral_B1_calibration35'];job=U/'queue_jobs'/s['job_dir'];r=dict(utc=utc(),state=s,exit=L(job/'exit.json'),row_boundary=L(job/'yielded.json'),saved_rows=len(list((cal/'alpha0/generation.private').glob('*.json'))),current_GPU0_task=state.get('Indian35_llama_mr_s3'),no_alpha_selection_read=True);save(O/'Mistral_B1_pause_status.json',r)
gate=U/'language_gate33/llama_translate-mr_alpha0.json';copy=L(gate);copy.update(gate_sha256=H(gate),main_s3_start_UTC=state['Indian35_llama_mr_s3']['started_utc'],speculative=False,source_translation_complete_UTC=L(U/'language_processed33/llama_translate-mr_alpha0/complete.json')['utc']);save(O/'Llama_mr_gate_timeline.json',copy)
T1=[]
for c in ['alpha0','s3','s4','s5','rand0','rand1']:
 p=U/'language_processed33'/('llama_translate-fr_'+c);ps=list((p/'processed.private').glob('*.json'));T1.append(dict(condition=c,N=len(ps),complete=(p/'complete.json').exists(),complete_UTC=L(p/'complete.json')['utc'] if (p/'complete.json').exists() else None))
save(O/'Llama_fr_T1_status.json',dict(utc=utc(),cells=T1,remaining_T1_held_during_T2=True))
idx=L(U/'followup35/addenda31_34_index.json');p=R/'docs/300_ADDENDUM35_EXPLORATORY_SEARCH_AND_T2_PRIORITY.md';idx['entries'].append(dict(number=35,path=str(p.relative_to(R)),sha256=H(p),contents='末候选诊断；Mistral标准100/2400门；Qta改派；独立Indian放行；编码v1复用条件；ARC-C撤回',first_commit=L(U/'followup35/publication.json')['commit']));idx['utc']=utc();save(O/'addenda31_35_index.json',idx)
vals=[x for x in summ if x['scope']=='Mistral2400_B1' and x['N']];mean=sum(x['mean_seconds']*x['N'] for x in vals)/sum(x['N'] for x in vals);save(O/'Mistral_cost_scenarios.json',dict(utc=utc(),B1_panel_partial_mean_seconds=mean,observed_groups=vals,not_family_throughput=True,nonzero_rows=19*5*440,alpha0_unique_rows=18*440,all19_gates_pass_scenario_GPUh=49720*mean/3600,nonzero_only_scenario_GPUh=41800*mean/3600,at30seconds_GPUh=49720*30/3600,at60seconds_GPUh=49720*60/3600,calibration_at6seconds_GPUh=15400*6/3600,calibration_observed_partial_mean_seconds=next(x['mean_seconds'] for x in summ if x['scope']=='Mistral_calibration_B1_120'),static_families_not_reduced=True,zero_gate_dedup_P1_P2=True))
print(json.dumps(dict(groups=summ,B1_status=r['state']['state'],B1_saved=r['saved_rows'],mr_gate={k:copy[k] for k in ['utc','fulfilled','rate_bounds','main_s3_start_UTC']},T1=T1,cost=L(O/'Mistral_cost_scenarios.json')),indent=2))
