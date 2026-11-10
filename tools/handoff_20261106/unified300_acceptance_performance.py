"""Metadata-only acceptance throughput and same-speed ETA, no text/labels."""
from pathlib import Path
import datetime,hashlib,json,os,time
U=Path('/data/HZX/Def/results/audit/unified300')
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def iso(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat()
def main():
 now=time.time();out={'utc':iso(now),'models':{},'method':'Rows from atomic file counts; phase wall time between consecutive checkpoint completions, first phase includes cold load. Batch write bursts are not mistaken for per-row timing. No response or label read.'}
 for model in ['llama','qwen']:
  d=U/'acceptance'/model;live=load(d/'live.json');pid=live['pid'];boot=next(int(x.split()[1])for x in Path('/proc/stat').read_text().splitlines()if x.startswith('btime '))
  p=Path('/proc')/str(pid)/'stat'
  if not p.exists():continue
  start=boot+int(p.read_text().split(') ')[1].split()[19])/os.sysconf('SC_CLK_TCK');previous=start;phases=[];all_completed=True
  for cap in [120,2400]:
   for condition in ['alpha0','s3','random']:
    for route in ['legacy_single','candidate_batch']:
     fs=list((d/'generation.private'/f'cap{cap}'/condition/route).glob('*.json'));times=sorted(x.stat().st_mtime for x in fs);n=len(times)
     if times:
      duration=times[-1]-previous;rate=n*3600/duration
      recent=20*3600/(times[-1]-times[-21])if route=='legacy_single'and n>20 else None
      phases.append({'cap':cap,'condition':condition,'path':route,'n':n,'elapsed_seconds':duration,'effective_rows_per_hour':rate,'recent20_rows_per_hour':recent,'first_saved_utc':iso(times[0]),'last_saved_utc':iso(times[-1])})
      if n==100:previous=times[-1]
     else:phases.append({'cap':cap,'condition':condition,'path':route,'n':0})
     if n<100:all_completed=False
  bycap={}
  for cap in [120,2400]:
   bycap[str(cap)]={}
   for route in ['legacy_single','candidate_batch']:
    xs=[x for x in phases if x['cap']==cap and x['path']==route and x['n']]
    if xs:bycap[str(cap)][route]={'n':sum(x['n']for x in xs),'effective_rows_per_hour':sum(x['n']for x in xs)*3600/sum(x['elapsed_seconds']for x in xs)}
  remaining={route:300-sum(x['n']for x in phases if x['cap']==2400 and x['path']==route)for route in ['legacy_single','candidate_batch']}
  refs={route:[x for x in phases if x['cap']==2400 and x['path']==route and x['n']>=20]for route in remaining}
  eta={'scope':'generation only; excludes judge label gate, historical20 and search20; no guarantee or upper bound'}
  if all(refs.values()):
   ranges={}
   for route,xs in refs.items():
    rates=[x['effective_rows_per_hour']for x in xs]
    if route=='legacy_single':rates +=[x['recent20_rows_per_hour']for x in xs if x['recent20_rows_per_hour']]
    ranges[route]=[min(rates),max(rates)]
   seconds_low=sum(remaining[k]/ranges[k][1]*3600 for k in remaining);seconds_high=sum(remaining[k]/ranges[k][0]*3600 for k in remaining)
   eta.update(utc_same_speed_range=[iso(now+seconds_low),iso(now+seconds_high)],rates_source='Actual 2400 acceptance phase cumulative rates; also recent20 for singles. Future conditions assumed within this observed range; batch length variation may invalidate it.',remaining_by_path=remaining)
  else:eta['status']='No completed/20-row 2400 batch phase yet; do not extrapolate from short-output tokens/s.'
  out['models'][model]={'pid':pid,'physical_gpu':live['physical_gpu'],'worker_start_utc':iso(start),'current':live,'total_saved':sum(x['n']for x in phases),'expected':1200,'phases':phases,'by_cap':bycap,'generation_ETA':eta,'complete':all_completed}
 observer=U/'acceptance_resource_observer.json'
 if observer.exists():out['sampled_memory']=load(observer)
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');p=U/f'acceptance_performance_{stamp}.json';p.write_text(json.dumps(out,indent=2)+'\n')
 print('FILE',p.name);print('SHA',sha(p));print(json.dumps({k:{'saved':v['total_saved'],'by_cap':v['by_cap'],'ETA':v['generation_ETA']}for k,v in out['models'].items()},indent=2))
if __name__=='__main__':main()
