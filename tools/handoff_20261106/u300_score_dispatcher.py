"""CPU-only scoring input manifest dispatcher; does not inspect judge labels."""
from pathlib import Path
import copy, datetime, fcntl, hashlib, json, os, subprocess, time
R=Path('/data/HZX/Def');U=R/'results/audit/unified300';T=R/'tools/handoff_20261106'
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def L(p):return json.loads(Path(p).read_text())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def cycle():
    assert L(U/'scoring_schedule_publication.json')['published']
    plan=L(U/'ready_generation_plan.json');inputs=L(U/'static_alpha0_inputs.private.json')
    prior=L(U/'score_dispatch_state.json') if (U/'score_dispatch_state.json').exists() else {'waves':[]}
    C=U/'ready_queue_catalog.json';cat=L(C);q=L(U/'ready_queue/state.json')['tasks']
    if (U/'score_waves/HB_0001/manifest.json').exists() and not any(w['judge']=='HB' for w in prior['waves']):
        m=L(U/'score_waves/HB_0001/manifest.json')
        prior['waves'].append(dict(utc=utc(),wave='HB_0001',judge='HB',task_id='score_HB_0001',
            N=m['N'],cells=m['cells'],manifest_sha256=H(U/'score_waves/HB_0001/manifest.json')))
    for judge in ['SORRY','WG','HB']:
        if judge=='HB' and not (U/'HB_scoring_publication.json').exists():continue
        existing=[w for w in prior['waves'] if w['judge']==judge]
        unfinished=[w for w in existing if q.get(w['task_id'],{}).get('state')!='done']
        if unfinished: continue
        known={tuple(c) for w in existing for c in w['cells']}
        cells=[];pack=[]
        for model in ['llama','qwen']:
            for family in inputs[model]:
                for condition in plan['condition_order'][model]:
                    if (model,family,condition) in known:continue
                    folder=U/'static_alpha0'/model/family if condition=='alpha0' else U/'ready_generated'/model/family/condition
                    marker=next((p for p in [folder/'complete.json',folder/'generation_complete.json'] if p.exists()),None)
                    if not marker:continue
                    meta=L(marker)
                    if meta.get('N')!=440:continue
                    files=meta['record_sha256'];data={str(r['id']):r for r in inputs[model][family]}
                    assert len(files)==440 and set(files)==set(data)
                    for k in sorted(data,key=int):
                        r=data[k];p=folder/'generation.private'/f'{int(k):04d}.json';g=L(p);gh=H(p)
                        assert gh==files[k];response=r['prefill']+g['result']['text']
                        assert hashlib.sha256(response.encode()).hexdigest()==g['full_response_sha256']
                        pack.append(dict(id=int(k),model=model,family=family,condition=condition,
                            prompt=r['prompt'],behavior=r['behavior'],response=response,
                            prompt_sha256=r['prompt_sha256'],behavior_sha256=r['behavior_sha256'],
                            response_sha256=g['full_response_sha256'],generation_sha256=gh,
                            generation_file_relative=str(p.relative_to(R))))
                    cells.append([model,family,condition])
        if not pack:continue
        wave=f'{judge}_{len(existing)+1:04d}';w=U/'score_waves'/wave
        save(w/'inputs.private.json',pack)
        manifest=dict(utc=utc(),N=len(pack),cells=cells,judges=[judge],inputs_sha256=H(w/'inputs.private.json'),
                      no_labels_or_texts_in_manifest=True,schedule_sha256=H(U/'scoring_schedule_v1.json'))
        save(w/'manifest.json',manifest)
        taskid='score_'+wave
        requires=[dict(path='results/audit/unified300/scoring_schedule_publication.json',key='published',value=True)]
        task=dict(id=taskid,priority=12 if judge=='HB' else 8,site='node01' if judge=='WG' else 'innet',
                  gpus=[0] if judge=='SORRY' else [2,3] if judge=='HB' else [2],kind='cache_only_judging',yieldable=False,
                  argv=['/data/ray/env/bin/python' if judge=='WG' else '/home/kemove/anaconda3/envs/HZX_GLA/bin/python',
                        '{ROOT}/tools/handoff_20261106/'+('u300_hb_cache_worker_v1.py' if judge=='HB' else 'u300_score_cache_worker.py'),judge,wave],
                  requires=requires)
        if judge=='HB':task['requires'].append(dict(path='results/audit/unified300/score_waves/SORRY_0001/SORRY_complete.json'))
        if judge=='WG':task['sync_relpath']='results/audit/unified300/main_scores/WG'
        rels=['tools/handoff_20261106/u300_score_cache_worker.py',
              'results/audit/unified300/scoring_schedule_v1.json',
              f'results/audit/unified300/score_waves/{wave}/manifest.json',
              f'results/audit/unified300/score_waves/{wave}/inputs.private.json']
        for rel in rels:
            if rel not in cat['node_deploy_files']:cat['node_deploy_files'].append(rel)
        assert not any(t['id']==taskid for t in cat['tasks']);cat['tasks'].append(task)
        prior['waves'].append(dict(utc=utc(),wave=wave,judge=judge,task_id=taskid,N=len(pack),cells=cells,
                                   manifest_sha256=H(w/'manifest.json')))
    # Runtime catalog is a CPU dispatch receipt under a previously published algorithm.
    # Existing running definitions are pinned by controller v8, never altered here.
    # Merge only the additions into the newest catalog. Other CPU preparers can add
    # tasks while this process is assembling a large private input pack.
    with (R/'logs/unified300_catalog_mutation.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        newest=L(C);ids={t['id'] for t in newest['tasks']}
        newest['tasks'] += [t for t in cat['tasks'] if t['id'] not in ids]
        newest['node_deploy_files']=list(dict.fromkeys(newest['node_deploy_files']+cat['node_deploy_files']))
        save(C,newest)
    save(U/'score_dispatch_state.json',{**prior,'utc':utc(),'pid':os.getpid(),'score_labels_read':False})

if __name__=='__main__':
    lock=(R/'logs/unified300_score_dispatch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    while True:
        try:cycle()
        except Exception as e:
            save(U/'score_dispatch_error.json',dict(utc=utc(),error_type=type(e).__name__,reason=str(e)[:350]))
        time.sleep(60)
