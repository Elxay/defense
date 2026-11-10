"""CPU sidecar: progress and sampled GPU memory only, no response/label reads."""
from pathlib import Path
import datetime,json,os,subprocess,time
U=Path('/data/HZX/Def/results/audit/unified300')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 out=U/'acceptance_resource_samples.jsonl';summary=U/'acceptance_resource_observer.json'
 assert not out.exists(),'Preserve previous monitor run'
 peaks={};minimum={};started=utc();samples=0
 while True:
  states={};running=False
  for model in ['llama','qwen']:
   d=U/'acceptance'/model;live=json.loads((d/'live.json').read_text());alive=Path('/proc')/str(live['pid'])
   states[model]={'pid':live['pid'],'phase':live['phase'],'cap':live.get('cap'),'condition':live.get('condition'),'path':live.get('path'),'saved_files':sum(1 for _ in (d/'generation.private').rglob('*.json')),'alive':alive.exists()}
   running |= alive.exists()
  gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.free','--format=csv,noheader,nounits'],text=True)
  cards={}
  for line in gpu.strip().splitlines():
   card,used,free=[int(x.strip())for x in line.split(',')]
   if card in[0,2]:
    cards[str(card)]={'used_MiB':used,'free_MiB':free};peaks[str(card)]=max(peaks.get(str(card),0),used);minimum[str(card)]=min(minimum.get(str(card),free),free)
  item={'utc':utc(),'states':states,'cards':cards}
  with out.open('a')as f:f.write(json.dumps(item)+'\n')
  samples+=1
  value={'utc':utc(),'pid':os.getpid(),'started_utc':started,'samples':samples,'interval_seconds':5,'sampled_peak_card_used_MiB':peaks,'sampled_min_card_free_MiB':minimum,'coverage':'Sampling starts at stated UTC; not full-run allocator peak. No retrospective peak is invented.','no_response_or_label_reads':True,'latest':item}
  temp=summary.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(summary)
  if not running or samples>=8640:break
  time.sleep(5)
if __name__=='__main__':main()
