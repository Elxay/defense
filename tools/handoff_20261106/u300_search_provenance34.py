from u300_schedule_prepare import *
import shlex,statistics,sys
O=U/'followup34';code="""from pathlib import Path
import json
U=Path('/home/dell/Def/results/audit/unified300');print(json.dumps({method:json.loads((U/(method+'_progressive')/'llama/tier88/complete.json').read_text())['selected_rows'] for method in ['PAIR','TAP']}))""";receipts=json.loads(subprocess.check_output(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(code)],text=True));out=dict(utc=utc(),Llama={})
for method in ['PAIR','TAP']:
 D=U/'search88_alpha0_v19'/method/'llama';rows=L(D/'inputs.private.json');assert all(r['prompt_sha256']==receipts[method][str(r['id'])]['selected_prompt_sha256'] for r in rows);out['Llama'][method]=dict(N=88,selected_prompt_hash_matches=88,cap=2400,backend='HF/bf16/sdpa',B=8,inputs_manifest_sha256=H(D/'inputs_manifest.json'),generation_manifest_sha256=H(D/'complete.json'),SORRY_backend='vLLM0.6.6.post1/bf16/eager')
last=L(U/'search132_laststream_alpha0_v34/PAIR/qwen/inputs.private.json');selected=L(U/'search132_alpha0_v31/PAIR/qwen/inputs.private.json');assert [r['id'] for r in last]==[r['id'] for r in selected];out['Qwen132']=dict(N=132,same_ID_order=True,same_prompt_IDs=[a['id'] for a,b in zip(last,selected) if a['prompt_sha256']==b['prompt_sha256']],both_backend='HF/bf16/sdpa/B4/greedy/max2400',only_prompt_object_varied=True,SORRY_backend='vLLM0.6.6.post1/bf16/eager')
for tag,D in [('selected',U/'search132_alpha0_v31/PAIR/qwen'),('laststream',U/'search132_laststream_alpha0_v34/PAIR/qwen')]:
 zs=[L(p)['result'] for p in (D/'generation.private').glob('*.json')];lengths=sorted(z['new_tokens'] for z in zs);out['Qwen132'][tag+'_lengths']=dict(median=statistics.median(lengths),p90=lengths[int(.9*(len(lengths)-1))],at2400=sum(x==2400 for x in lengths))
save(O/'search_provenance.json',out);print(json.dumps(out))
