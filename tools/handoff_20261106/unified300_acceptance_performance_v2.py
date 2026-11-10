"""Metadata snapshot aware of the immutable long-panel memory fallback."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,sys,time
U=Path('/data/HZX/Def/results/audit/unified300')
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def iso(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat()
def main():
 text=subprocess.check_output([sys.executable,'/data/HZX/Def/tools/handoff_20261106/unified300_acceptance_performance.py'],text=True)
 parent=U/re.search(r'^FILE (.+)$',text,re.M).group(1);result=load(parent);now=time.time()
 d=U/'acceptance_v2/llama';live=load(d/'live.json');reference=load(U/'acceptance_performance_20261110T104428Z.json')['models']['llama']
 oldphase=next(x for x in reference['phases']if x['cap']==2400 and x['condition']=='alpha0'and x['path']=='legacy_single')
 byroute={route:[]for route in ['legacy_single','candidate_batch']};metrics_manifest={}
 for p in sorted((d/'metrics').glob('*.json')):
  match=re.fullmatch(r'cap2400_(alpha0|s3|random)_(legacy_single|candidate_batch)_start\d+.json',p.name);assert match
  value=load(p);value['condition']=match.group(1);byroute[match.group(2)].append(value);metrics_manifest[p.name]=sha(p)
 newcounts={k:sum(x['rows']for x in v)for k,v in byroute.items()};newsecs={k:sum(x['elapsed_seconds']for x in v)for k,v in byroute.items()}
 data={k:{'n':newcounts[k],'effective_rows_per_hour':newcounts[k]*3600/newsecs[k]}for k in byroute if newcounts[k]}
 data['legacy_single']={'n':100+newcounts['legacy_single'],'effective_rows_per_hour':(100+newcounts['legacy_single'])*3600/(oldphase['elapsed_seconds']+newsecs['legacy_single']),'includes_explicit_reused_reference_n':100,'reused_reference_rate':oldphase['effective_rows_per_hour']}
 remaining={'legacy_single':200-newcounts['legacy_single'],'candidate_batch':300-newcounts['candidate_batch']};eta={'scope':'generation only; no label/history/search gate completion claimed','status':'waiting for new B8 timing'}
 if newcounts['candidate_batch']:
  singles=[oldphase['effective_rows_per_hour']]+([oldphase['recent20_rows_per_hour']]if oldphase['recent20_rows_per_hour']else[])
  if newcounts['legacy_single']:singles.append(newcounts['legacy_single']*3600/newsecs['legacy_single'])
  batch_rate=data['candidate_batch']['effective_rows_per_hour'];low=remaining['legacy_single']/max(singles)*3600+remaining['candidate_batch']/batch_rate*3600;high=remaining['legacy_single']/min(singles)*3600+remaining['candidate_batch']/batch_rate*3600
  eta={'scope':'generation only, excludes labels/historical20/search20','utc_same_speed_range':[iso(now+low),iso(now+high)],'remaining_by_path':remaining,'rates_source':'Old measured alpha0 single cumulative/recent20 plus new v2 metrics; future conditions assumed to match. Batch timing currently covers '+str(newcounts['candidate_batch'])+' rows; not a CI or upper bound.'}
 allmetrics=sum(byroute.values(),[]);memory={}
 if allmetrics:memory={'window':'new v2 dispatch only, copied B1 rows excluded','peak_reserved_bytes':max(x['peak_reserved_bytes']for x in allmetrics),'peak_allocated_bytes':max(x['peak_allocated_bytes']for x in allmetrics),'minimum_measured_headroom_bytes':min(x['headroom_bytes']for x in allmetrics),'batches':len(allmetrics),'metrics_manifest_sha256':hashlib.sha256(json.dumps(metrics_manifest,sort_keys=True).encode()).hexdigest()}
 result['models']['llama']={'pid':live['pid'],'physical_gpu':2,'current':live,'total_saved':700+sum(newcounts.values()),'expected':1200,'reused_long_B1_reference_rows':100,'new_rows_v2':sum(newcounts.values()),'excluded_failed_B16_candidate_rows':80,'preserved_v1_total_files':780,'by_cap':{'120':reference['by_cap']['120'],'2400':data},'generation_ETA':eta,'own_batch_telemetry':memory,'memory_fallback':'B16 failed 3GiB margin; B8 full long candidate replacement; no OOM','source_reference_performance_sha256':sha(U/'acceptance_performance_20261110T104428Z.json')}
 result.update(utc=iso(now),parent_snapshot_sha256=sha(parent),metadata_only=True)
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');p=U/f'acceptance_performance_v2_{stamp}.json';p.write_text(json.dumps(result,indent=2)+'\n')
 print('FILE',p.name);print('SHA',sha(p));print(json.dumps({k:{'rows':v['total_saved'],'by_cap':v['by_cap'],'ETA':v['generation_ETA'],'own_batch_telemetry':v.get('own_batch_telemetry')}for k,v in result['models'].items()},indent=2))
if __name__=='__main__':main()
