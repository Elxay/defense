from u300_schedule_prepare import *
import os,sys,random,copy,shlex,importlib.util
os.environ['GIT_SSH_COMMAND']='ssh -o Hostname=127.0.0.1 -o Port=18443 -o HostKeyAlias=github.com -o StrictHostKeyChecking=yes -o ConnectTimeout=15'
O=U/'followup37';Q=O/'private_review';Q.mkdir(exist_ok=True);results=L(U/'followup36/rating264_results.json')['rows'];groups=[sorted([r for r in results if r['kind']=='selected' and r['score']>=10 and r['SORRY_same_internal']==0],key=lambda r:r['id']),sorted([r for r in results if r['kind']=='selected' and r['score']<10 and r['SORRY_same_internal']==1],key=lambda r:r['id'])];assert list(map(len,groups))==[65,34]
chosen=[]
for group,seed,name in zip(groups,[2026111407,2026111408],['score10_SORRY0','scorelow_SORRY1']):
 random.Random(seed).shuffle(group)
 for r in group[:12]:chosen.append(dict(**r,sampling_stratum=name))
random.Random(2026111409).shuffle(chosen);blind=[];mapping=[]
for i,r in enumerate(chosen,1):
 p=U/'score_diagnostic36/source_positions.private'/f"{r['id']}_selected.json";assert H(p)==r['source_record_sha256'];z=L(p);key=f'B{i:02d}';blind.append(dict(blind_id=key,original_behavior=z['behavior'],saved_internal_response=z['response']));mapping.append(dict(blind_id=key,id=r['id'],stratum=r['sampling_stratum'],score=r['score'],SORRY=r['SORRY_same_internal'],source_sha256=H(p)))
save(Q/'blind24.private.json',blind);save(Q/'mapping24.private.json',mapping);save(O/'review_sampling_manifest.json',dict(utc_frozen=utc(),N=24,seeds=[2026111407,2026111408,2026111409],population='selected saved internal responses only, not all264 positions',population_strata_N=[65,34],sample_strata_N=[12,12],blind_packet_sha256=H(Q/'blind24.private.json'),private_mapping_sha256=H(Q/'mapping24.private.json'),raw_and_row_annotations_not_for_git=True,annotator='current Codex assistant; shared context, no human calibration'))
# Audit the exact behavior slot against the frozen original base instruction.
base=R/'results/audit/sorry296/downloads.private/sorry-bench-202503/question.jsonl';by={int(z['question_id']):z['turns'][0] for z in [json.loads(x) for x in base.read_text().splitlines() if x.strip()]};checks=[]
for W in (U/'score_waves').iterdir():
 if not W.is_dir() or not (W/'inputs.private.json').exists():continue
 if not (any(W.name.startswith(s) for s in ['search88_','search132_','laststream132_','exploratory_last35_']) or W.name=='PAIR_internal_rating_diagnostic36'):continue
 rows=L(W/'inputs.private.json');same=[]
 for r in rows:
  id=int(str(r['id']).split(':')[0]);same.append(r['behavior']==by[id] and r['behavior_sha256']==hashlib.sha256(by[id].encode()).hexdigest())
 assert all(same),W.name;checks.append(dict(wave=W.name,N=len(rows),all_behavior_slots_equal_original_base=True,inputs_sha256=H(W/'inputs.private.json')))
worker=T/'u300_rating36_SORRY.py';text=worker.read_text();assert "'turns':[r['behavior']]" in text and "'turns':[r['response']]" in text;save(O/'SORRY_instruction_slot_audit.json',dict(utc=utc(),base_file_sha256=H(base),N_waves=len(checks),N_records=sum(r['N'] for r in checks),checks=checks,source_worker_sha256=H(worker),instruction_source="r['behavior'] exactly original English base instruction",not_adversarial_prompt=True,response_source="r['response']",same_response_diagnostic_included=True))
# Verify the new pure extractor against all already-executed alpha0 last prompts.
extractor=T/'u300_extract_last37.py';extractor.write_text(extractor.read_text(encoding='utf-8-sig').replace('\r\n','\n').rstrip()+'\n');sys.path.insert(0,str(T));from u300_extract_last37 import extract_last
code="""from pathlib import Path
import json,hashlib
R=Path('/home/dell/Def');U=R/'results/audit/unified300';out={}
for method,m,tier in [('PAIR','llama',88),('TAP','llama',88),('TAP','qwen',88),('PAIR','qwen',220)]:
 C=json.loads((U/(method+'_progressive')/m/('tier'+str(tier))/'complete.json').read_text());rows={}
 for id,ref in C['selected_rows'].items():
  p=R/ref['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256'];rows[id]=json.loads(p.read_text())
 out[method+'_'+m]=rows
print(json.dumps(out))""";source=json.loads(subprocess.check_output(['ssh','node01','/data/ray/env/bin/python -c '+shlex.quote(code)],text=True));proof=[]
for name,method,m in [('exploratory_last35_PAIR_llama','PAIR','llama'),('exploratory_last35_TAP_llama','TAP','llama'),('exploratory_last35_TAP_qwen','TAP','qwen'),('laststream132_PAIR_qwen','PAIR','qwen')]:
 for r in L(U/'score_waves'/name/'inputs.private.json'):
  prompt,pos=extract_last(source[method+'_'+m][str(r['id'])],method);assert hashlib.sha256(prompt.encode()).hexdigest()==r['prompt_sha256'];proof.append(dict(wave=name,id=r['id'],prompt_sha256=r['prompt_sha256'],**pos))
save(O/'last_extraction_contract.json',dict(utc=utc(),pure_extractor_sha256=H(extractor),original_executed_extractor_sha256=H(T/'u300_search_audit35.py'),original_Qwen132_script_sha256=H(T/'u300_prepare34.py'),N_prior_prompts_verified=len(proof),all_unchanged=True,PAIR='stored streams[-1][-1].adv_prompt; stored array positions, not inferred missing global round IDs',TAP='stored source_logs[-1].adv_prompt; last retained candidate logged after phase2 pruning in final completed iteration',TAP_node_ID_or_absolute_depth_not_in_old_log=True,source_TAP_sha256=H(R/'repos/HarmBench/baselines/tap/TAP.py'),checks=proof))
# Two fresh independent judge processes, isolated result directories; no result reuse.
original=L(U/'score_waves/PAIR_internal_rating_diagnostic36/inputs.private.json');rows=[r for r in original if r['condition']=='last'];assert len(rows)==132
for run in [1,2]:
 W=U/'score_waves'/f'last_internal_repeat37_r{run}';save(W/'inputs.private.json',rows);save(W/'manifest.json',dict(utc=utc(),N=132,judges=['SORRY'],inputs_sha256=H(W/'inputs.private.json'),scope='same132 saved internal completions; fresh deterministic judge repeat, not protected effects'))
s=(T/'u300_score_cache_worker.py').read_text().replace("P=L(U/'scoring_schedule_v1.json')","P=L(U/'selfrepeat37_plan.json')").replace("out=U/'main_scores'/judge","out=U/'selfrepeat37'/wave/judge\nassert not list((out/'records.private').glob('*.json')), 'Independent repeat must not reuse existing results'").replace("H(U/'scoring_schedule_v1.json')","H(U/'selfrepeat37_plan.json')");s += "\nsave(out.parent/'complete.json',dict(utc=utc(),N=132,fresh_process=True,no_result_cache_reuse=True,wave=wave))\n";w=T/'u300_selfrepeat37_worker.py';w.write_text(s);compile(s,str(w),'exec');p=U/'selfrepeat37_plan.json';z=L(U/'scoring_schedule_v1.json');z.update(utc_frozen=utc(),worker_sha256=H(w),scope='Two fresh runs same132 same order same original behavior and internal response',run_waves=['last_internal_repeat37_r1','last_internal_repeat37_r2'],same_input_sha256=H(U/'score_waves/last_internal_repeat37_r1/inputs.private.json'),source_parent_sha256=H(U/'rating36_SORRY_plan.json'));save(p,z)
pub=[O/'review_sampling_manifest.json',O/'SORRY_instruction_slot_audit.json',extractor,O/'last_extraction_contract.json',w,p]+[U/'score_waves'/f'last_internal_repeat37_r{i}'/'manifest.json' for i in [1,2]];commit=publish(pub,'Freeze local blind24 selection, audit original instruction slots and fixed extraction; queue isolated judge repeats')
with (R/'logs/unified300_catalog_mutation.lock').open('a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);cat=L(U/'ready_queue_catalog.json')
 for run in [1,2]:
  wave=f'last_internal_repeat37_r{run}';req=[] if run==1 else [dict(path='results/audit/unified300/selfrepeat37/last_internal_repeat37_r1/complete.json',key='N',value=132)]
  cat['tasks'].append(dict(id=f'judge_selfrepeat37_r{run}',priority=3,site='innet',gpus=[2],kind='alpha0_judge_repeat_diagnostic',yieldable=False,argv=['bash','{ROOT}/tools/handoff_20261106/u300_logged_job30.sh','{ROOT}',str(p.relative_to(R)),'2','/home/kemove/anaconda3/envs/HZX_GLA/bin/python','{ROOT}/tools/handoff_20261106/'+w.name,'SORRY',wave],requires=req))
 save(U/'ready_queue_catalog.json',cat)
save(O/'setup_publication.json',dict(utc=utc(),commit=commit,review_packet_sha256=H(Q/'blind24.private.json'),extractor_sha256=H(extractor),repeat_plan_sha256=H(p)));print(json.dumps(L(O/'setup_publication.json')))
