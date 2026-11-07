from pathlib import Path
import json,subprocess,shlex,datetime
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round10';T=B/'results/style_retrained';matches=json.loads((T/'alpha_matches_frozen.json').read_text())['rows']
code="""from pathlib import Path
import json
B=Path('/home/dell/Def');out={}
for s in[3,4,5]:
 d=B/f'results/style_retrained/eval_s{s}';cache={p.name:len(json.loads(p.read_text())['items'])for p in d.glob('*.json')if not p.name.startswith('speed')and(p.name.endswith('_wjb300.json')or p.name.endswith('_pairs600.json'))};speed={p.name:json.loads(p.read_text())['seconds_per_item']for p in d.glob('speed25_full*.json')};out[str(s)]=dict(counts=cache,speeds=speed,live=json.loads((B/f'results/audit/handoff_round9/generate_full_s{s}_live.json').read_text()))
print(json.dumps(out))"""
node=json.loads(subprocess.check_output(['ssh','node01','python3','-c',shlex.quote(code)],text=True));out=[]
for s in range(3,8):
 if s<=5:r=node[str(s)]
 else:
  d=T/f'eval_s{s}';r=dict(counts={p.name:len(json.loads(p.read_text())['items'])for p in d.glob('*.json')if not p.name.startswith('speed')and(p.name.endswith('_wjb300.json')or p.name.endswith('_pairs600.json'))},speeds={p.name:json.loads(p.read_text())['seconds_per_item']for p in d.glob('speed25_full*.json')},live=json.loads((B/f'results/audit/handoff_round9/generate_full_s{s}_live.json').read_text()))
 wjb_rates=[v for k,v in r['speeds'].items()if'wjb300'in k];pair_rates=[v for k,v in r['speeds'].items()if'pairs600'in k];wref=max(wjb_rates)if wjb_rates else 20.;pref=max(pair_rates)if pair_rates else (5. if s<=5 else 3.4);remaining=0
 for cond,alpha in[('control',1.),('treatment',matches[str(s)]['selected_alpha'])]:
  for kind,total,fallback in[('wjb300',300,wref),('pairs600',600,pref)]:
   name=f'{cond}_a{alpha:g}_{kind}.json';rate=r['speeds'].get('speed25_full_'+name,fallback);remaining+=(total-r['counts'].get(name,0))*rate
 out.append(dict(seed=s,host='node01'if s<=5 else'innet',cached_counts=r['counts'],first25_speeds=r['speeds'],estimated_remaining_seconds_without_queue=remaining,live=r['live']))
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=out,max_remaining_seconds=max(r['estimated_remaining_seconds_without_queue']for r in out),caveat='Unmeasured future treatment speeds projected from same-host first25; target-window queue and judge time additional; not a completion guarantee')
(O/'measured_eta_snapshot.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
