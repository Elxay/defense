"""Counts, runtime metadata and measured service rates; never score outcome labels."""
from pathlib import Path
import collections,datetime,hashlib,json,subprocess
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';S=B/'lease_priority';O=B/'tail_contextual_followup_20261109'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    now=datetime.datetime.now(datetime.timezone.utc);handoff=load(S/'v2_handoff_complete.json');switch=datetime.datetime.fromisoformat(handoff['utc']);timings=[load(p)for p in S.glob('tail_done_*.json')];donepids={x['pid']for x in timings}
    for p in S.glob('tail_live_gpu*.json'):
        x=load(p)
        if x['pid']not in donepids and Path('/proc',str(x['pid'])).exists():timings.append({**x,'elapsed_seconds':x['wall_seconds'],'active_observation':True})
    baseline_manifest=load(S/'v2_handoff_existing_files.private.json');baseline_counts=collections.Counter()
    for n in baseline_manifest:
        p=Path(n);parts=p.parts
        if 'public255' in parts and any(k in parts for k in ['harmful.private','public.private']):
            kind='harmful'if'harmful.private'in parts else'public';pos=parts.index(kind+'.private');name=parts[pos+1]
            if name in ['old_s0','SYS_A','SYS_B']:baseline_counts[kind,name]+=len(load(R/n)['items'])
    result={'utc':now.isoformat(),'jst':now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'public_denominator':{'benign':1779,'unsafe_control':200,'total':1979},'v2_handoff':handoff,'conditions':{},'no_outcome_labels_selected':True}
    for name in ['old_s0','SYS_A','SYS_B']:
        out={}
        for kind in ['harmful','public']:
            dataset={};files=[];metadata=collections.Counter();shards=collections.Counter()
            for d in (B/'public255'/f'{kind}.private'/name).glob('*'):
                if not d.is_dir():continue
                count=0;ids=[]
                for p in d.glob('*.json'):
                    x=load(p);items=x['items'];count+=len(items);ids.extend(a['id']for a in items);files.append(p)
                    for a in items:
                        raw=x.get('generation',{});hook=raw.get('injection_count',a.get('prefill_hook_count'));rho=raw.get('rho_runtime',a.get('rho_runtime'));metadata['rows']+=1
                        for key in ['new_tokens','eos','eos_hit_generation_config','nonzero_vector_injection_count','system_text_sha256']:
                            if key in a or key in raw:metadata[key]+=1
                        if hook==1:metadata['prefill_hook_count_1']+=1
                        if name in ['SYS_A','SYS_B']:
                            assert rho==0.0
                            if 'nonzero_vector_injection_count'in a:assert a['nonzero_vector_injection_count']==0
                            assert(a.get('system_text_sha256')or raw.get('system_text_sha256'))
                assert len(ids)==len(set(ids));dataset[d.name]=count
            z=[t for t in timings if t['condition']==name and t['kind']==kind and t['new_rows']>0];rows=sum(t['new_rows']for t in z);elapsed=sum(t['elapsed_seconds']for t in z);recent=[t for t in z if datetime.datetime.fromisoformat(t['utc'])-datetime.timedelta(seconds=t['elapsed_seconds'])>=switch];rn=sum(t['new_rows']for t in recent);rs=sum(t['elapsed_seconds']for t in recent)
            rate=rs/rn if rn else elapsed/rows if rows else None;remaining=(2000 if kind=='harmful' else 1979)-sum(dataset.values());service=remaining*rate if rate else None
            delta=sum(dataset.values())-baseline_counts[kind,name];observed_seconds=(now-switch).total_seconds()
            if name!='old_s0' and z:
                first=min(datetime.datetime.fromisoformat(t['utc'])-datetime.timedelta(seconds=t['elapsed_seconds'])for t in z);observed_seconds=(now-first).total_seconds()
            calendar_rate=delta/observed_seconds if delta and observed_seconds>0 else None;calendar_eta=(now+datetime.timedelta(seconds=remaining/calendar_rate)).isoformat()if calendar_rate and remaining>0 else None
            out[kind]={'dataset_counts':dataset,'total_rows':sum(dataset.values()),'metadata_field_counts':dict(metadata),'timed_new_rows':rows,'measured_wall_seconds_per_new_row':elapsed/rows if rows else None,'v2_timed_rows':rn,'v2_seconds_per_row':rs/rn if rn else None,'remaining_rows':remaining,'remaining_card_hours_at_current_rate':service/3600 if service is not None else None,'new_rows_since_v2':delta,'calendar_rows_per_hour_since_v2':calendar_rate*3600 if calendar_rate else None,'calendar_ETA_utc_since_v2_rate':calendar_eta,'ETA_interpretation':'Calendar ETA includes observed v2 priority waits but is a short-run extrapolation. Service time excludes priority waits. Neither guarantees future throughput. A/B have no measured rate before first rows; do not infer their rate from s0.'}
        result['conditions'][name]=out
    ctrl=load(S/'controller_live.json');result['scheduler']={k:v for k,v in ctrl.items()if k!='jobs'};result['active_leases']=[{k:v for k,v in j.items()if k in ['kind','cards','condition','tail_kind','shard','launcher_pid']}for j in ctrl.get('jobs',{}).values()]
    life=B/'read_order10/lifecycle';result['search_complete_receipt']=load(life/'search_complete.json')if(life/'search_complete.json').exists()else None;result['target_generation_complete_receipt']=load(life/'target_generation_complete.json')if(life/'target_generation_complete.json').exists()else None;result['observer_live']=load(life/'observer_live.json')
    code="""from pathlib import Path
import json,statistics
b=Path('/home/dell/Def/results/audit/pair500');x=json.loads((b/'generation_live.json').read_text());s=[json.loads(p.read_text())['seconds']for p in(b/'generations.private').glob('*.json')];print(json.dumps({'n':len(s),'mean_seconds_per_row':statistics.mean(s),'phase':x['phase'],'worker_pid':x['pid'],'heartbeat_utc':x['utc']}))
""";result['PAIR_search']=json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=code,text=True))
    O.mkdir(exist_ok=True);dest=O/('tail_snapshot_'+now.strftime('%Y%m%dT%H%M%S')+'.json');dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'file':str(dest.relative_to(R)),'sha256':sha(dest),'utc':result['utc'],'conditions':{n:{k:{f:z[f]for f in ['dataset_counts','total_rows','v2_seconds_per_row','measured_wall_seconds_per_new_row','remaining_card_hours_at_current_rate']}for k,z in x.items()}for n,x in result['conditions'].items()},'active_leases':result['active_leases'],'PAIR_search':result['PAIR_search'],'search_complete_receipt':result['search_complete_receipt'],'target_generation_complete_receipt':result['target_generation_complete_receipt']}))
if __name__=='__main__':main()
