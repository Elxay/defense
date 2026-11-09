"""Operational estimates separating model/startup cost from token generation."""
from pathlib import Path
import datetime,json,statistics
ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500';P=BASE/'prefix254';S=BASE/'lease_priority'
def main():
    batches=[]
    for path in (P/'launch_metadata').glob('*_innet_*.json'):
        meta=json.loads(path.read_text());pid=meta['pid'];name=meta['condition'];live=P/'live'/f'{name}_innet_{pid}.json'
        if Path('/proc',str(pid)).exists() or not live.exists():continue
        state=json.loads(live.read_text());start=datetime.datetime.fromisoformat(meta['utc']).timestamp();end=datetime.datetime.fromisoformat(state['utc']).timestamp();stem=path.name.rsplit('_innet_',1)[0];task=P/'tasks.private'/(stem+'.json')
        if not task.exists():continue
        data=json.loads(task.read_text())
        if data.get('gate'):continue
        rows=[]
        for item in data['items']:
            p=P/'generation.private'/name/(item['id']+'.json')
            if not p.exists() or not(start<=p.stat().st_mtime<=end+1):continue
            r=json.loads(p.read_text())
            if r.get('physical_gpu')!=meta['physical_device'] or 'row_seconds'not in r:continue
            rows.append((p.stat().st_mtime,r['row_seconds']))
        if not rows:continue
        rows.sort();load=max(0,rows[0][0]-start-rows[0][1]);batches.append({'condition':name,'card':meta['physical_device'],'worker_pid':pid,'n':len(rows),'net_generation_seconds':sum(v for _,v in rows),'observed_startup_seconds':load,'wall_seconds':max(0,end-start),'wall_s_per_row':max(0,end-start)/len(rows)})
    summary={}
    for name in sorted({r['condition']for r in batches}):
        b=[r for r in batches if r['condition']==name];summary[name]={'completed_batches':len(b),'rows':sum(r['n']for r in b),'net_seconds_per_row':sum(r['net_generation_seconds']for r in b)/sum(r['n']for r in b),'wall_seconds_per_row':sum(r['wall_seconds']for r in b)/sum(r['n']for r in b),'median_startup_seconds':statistics.median(r['observed_startup_seconds']for r in b)}
    small=[r for r in batches if r['n']<=5];large=[r for r in batches if r['n']>=25]
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'conditions':summary,'n_batches':len(batches),'small_batches':len(small),'large_batches':len(large),'small_median_wall_s_per_row':statistics.median(r['wall_s_per_row']for r in small)if small else None,'large_median_wall_s_per_row':statistics.median(r['wall_s_per_row']for r in large)if large else None,'rows':batches,'interpretation':'Launch-to-first-save minus measured first-row generation estimates startup/metadata time, not a precise model-loading profiler. Wall time includes startup and file operations; net rates omit them. Timing associations use original batch IDs/card/UTC windows; no output labels read.'}
    p=S/'prefix_loading_cost.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
