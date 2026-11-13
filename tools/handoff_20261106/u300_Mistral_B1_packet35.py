from pathlib import Path
import os,sys,json,hashlib,datetime,time,subprocess
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';T=R/'tools/handoff_20261106';L=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(z,indent=2)+'\n');q.replace(p)
P=L(U/'Mistral_calibration_B1_35_plan.json');D=Path(P['output_root']);B=L(U/'followup35/Mistral_B1_scoring_binding.json')
while not ((D/'complete22.json').exists() and (D/'adjacent_contract.json').exists() and L(D/'adjacent_contract.json')['passed']):time.sleep(10)
raw=L(P['input_path']);raw=raw if isinstance(raw,list) else raw.get('rows') or raw['items'];pack=[];conditions=['alpha0']+[f's{s}_a{a:.2f}' for s in [3,4,5] for a in P['alpha_grid']]
for c in conditions:
 comp=L(D/c/'complete.json');assert comp['N']==700
 for i in range(700):
  gp=D/c/'generation.private'/f'{i:04d}.json';assert H(gp)==comp['record_sha256'][gp.name];z=L(gp);assert z['plan_sha256']==H(U/'Mistral_calibration_B1_35_plan.json');prompt=raw[i].get('prompt') or raw[i].get('text');response=z['result']['text'];ph=hashlib.sha256(prompt.encode()).hexdigest()
  pack.append(dict(id=f'{c}:{i}',model='mistral',family='calibration700_B1_v35',condition=c,prompt=prompt,behavior=prompt,response=response,prompt_sha256=ph,behavior_sha256=ph,response_sha256=hashlib.sha256(response.encode()).hexdigest(),generation_sha256=H(gp),preprocessing_sha256=None))
assert len(pack)==15400;W=U/'score_waves/Mistral_calibration_B1_35';save(W/'inputs.private.json',pack);save(W/'manifest.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),N=15400,judges=['WG'],inputs_sha256=H(W/'inputs.private.json'),scope='corrected calibration only; cache write, no selection statistics',generation_plan_sha256=H(U/'Mistral_calibration_B1_35_plan.json')))

save(U/'followup35/Mistral_B1_scoring_wave_ready.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),N=15400,manifest_sha256=H(W/'manifest.json'),cache_only=True,selection_read_admitted=False))
