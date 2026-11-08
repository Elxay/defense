"""Audit dispatch chronology and prefix composition; never aggregate outcomes."""
import ast
import collections
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path('/data/HZX/Def');BASE=ROOT/'results/audit/pair500'
NAMES=['alpha0','old_s3','old_s4','old_s5','old_s6','old_s7','rand0','rand1','rand2','rand3']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stamp(p):return datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    source=ROOT/'tools/handoff_20261106/wildguard_public_queue.py'
    tree=ast.parse(source.read_text());literal=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(k,ast.Name) and k.id=='NAMES' for k in n.targets))
    assert ast.literal_eval(literal)==NAMES
    chronology=[]
    for name in NAMES:
        done=BASE/'wildguard_public'/(name+'_done.json');live=BASE/'wildguard_public'/(name+'_live.json')
        d=json.loads(done.read_text());x=json.loads(live.read_text());assert d['n']==1979
        chronology.append({'condition':name,'n':d['n'],'pid':x['pid'],'done_file_mtime_utc':stamp(done),'done_file_sha256':sha(done),'last_live_utc':x['utc'],'last_live_n':x.get('n')})
    assert [x['condition'] for x in sorted(chronology,key=lambda x:x['done_file_mtime_utc'])]==NAMES
    public={'recorded_utc':now,'order':NAMES,'source_sha256':sha(source),'conditions':chronology,
        'all_ten_complete':True,'no_summary_or_outcome_file_loaded':True,
        'timestamp_semantics':'Completion timestamps are done-file mtimes preserved by rsync; done markers have no explicit UTC field. Last-live timestamps are also retained. Historical PIDs are not current workers.',
        'correction':'The earlier report quoting alpha0 1670 rows was stale: its done marker predates 01:04 JST. At 02:08 JST the three completed conditions were alpha0, old_s3, old_s4; old_s5 was fourth.'}
    save(BASE/'public_wg_execution_chronology.json',public)
    rows={x['id']:x for x in json.loads((BASE/'rows.private.json').read_text())};order=json.loads((BASE/'row_audit.json').read_text())['order']
    first=min((BASE/'prefix254/tasks.private').glob('*.json'),key=lambda p:p.stat().st_mtime);task=json.loads(first.read_text());assert task['condition']=='alpha0'
    assert [x['id'] for x in task['items']]==order[:50]
    available=[]
    for key in order:
        p=BASE/'generations.private'/(key+'.json')
        if not p.exists() or p.stat().st_mtime>first.stat().st_mtime:break
        available.append(key)
    s7last=max((BASE/'public255/harmful.private/old_s7/wildjailbreak_harmful').glob('*.json'),key=lambda p:p.stat().st_mtime)
    last_source=BASE/'generations.private'/(available[-1]+'.json');next_source=BASE/'generations.private'/(order[len(available)]+'.json')
    assert last_source.stat().st_mtime<s7last.stat().st_mtime<first.stat().st_mtime<next_source.stat().st_mtime
    ids=BASE/'prefix254_start_available_ids.txt';ids.write_text(''.join(k+'\n' for k in available))
    overall=collections.Counter(x['layer'] for x in rows.values());counts=collections.Counter(rows[k]['layer'] for k in available);batch=collections.Counter(rows[x['id']]['layer'] for x in task['items'])
    prefix={'recorded_utc':now,'recording_status':'post-hoc operational reconstruction; no separate layer-count file was saved before generation',
        'first_task_utc':stamp(first),'first_task_sha256':sha(first),'prefix_n':len(available),'prefix_id_list_sha256':sha(ids),
        'source_time_bounds':{'last_completed_search_row_utc':stamp(last_source),'s7_completion_utc':stamp(s7last),'first_dispatch_utc':stamp(first),'next_search_row_utc':stamp(next_source)},
        'layers':{layer:{'overall_n':overall[layer],'overall_share_pct':100*overall[layer]/len(rows),'prefix_n':counts[layer],'prefix_share_pct':100*counts[layer]/len(available),'first_dispatched_batch_n':batch[layer]} for layer in ['standard','contextual','copyright','jbb']},
        'order':'The search worker processes the frozen order serially. Different row durations alter wall-clock completion, not the order. No prefix outcome analysis.',
        'baseline_input':'Selected prompt only; uniform helper generates a new 2400-token-cap alpha0. The 512-token search candidate replies are not evaluation inputs. The per-row native alpha0 used for the cross-node diagnostic is itself a separate eval_target_max_new_tokens generation.'}
    save(BASE/'prefix254_start_layer_reconstruction.json',prefix)
    sys.path.insert(0,str(ROOT/'tools/handoff_20261106'))
    from prefix_support import system_texts
    from transformers import AutoTokenizer
    runtime=json.loads((BASE/'prefix254_runtime.json').read_text());tok=AutoTokenizer.from_pretrained(runtime['models']['innet']['target'],local_files_only=True)
    user={'role':'user','content':'BENIGN_RENDER_CHECK'}
    def system_body(messages):
        rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        return rendered.split('<|start_header_id|>system<|end_header_id|>\n\n',1)[1].split('<|eot_id|>',1)[0]
    default=system_body([user]);texts=system_texts();placement={}
    for name,text in texts.items():
        body=system_body([{'role':'system','content':text},user])
        assert body.endswith(text) and body.startswith(default.rstrip('\n'))
        assert not any(label in body for label in ['A_short','B_detailed'])
        placement[name]={'system_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'one_explicit_system_message':True,'template_metadata_retained_before_text':True,'body_has_no_A_short_B_detailed_label':True,'no_extra_generic_default_instruction_appended':True}
    code=(ROOT/'tools/handoff_20261106/wjb_eval255_run.py').read_text();assert 'generate_with_injection(' in code
    common=(ROOT/'src/gen/common.py').read_text();assert '"new_tokens"' in common and '"eos"' in common
    render={'utc':now,'conditions':placement,'message_roles':['system','user'],'generation_helper_sha256':sha(ROOT/'src/gen/common.py'),'new_tokens_and_eos_fields_returned':True,
        'historical_comparison':'Uses the established body-only/no-label convention. No new byte-equivalence claim for historical A/B outputs; the template retains its own knowledge/date metadata.',
        'system_generation_coverage':{n:len(list((BASE/'public255/harmful.private'/n/'wildjailbreak_harmful').glob('*.json'))) for n in ['SYS_A','SYS_B']}}
    save(BASE/'llama_system_placement_and_fields.json',render)
    launch=next((BASE/'public255/judge_launches').glob('*'));started=json.loads((launch/'started.json').read_text());ready=json.loads((launch/'ready.json').read_text());finished=json.loads((BASE/'prefix254/wjb_primary_hb_window_complete.json').read_text())
    window={'recorded_utc':now,'s7_completed_utc':stamp(s7last),'s7_rows':2000,'started_utc':started['utc'],'pid':started['pid'],'conditions':started['conditions'],'backend':started['backend'],
        'device':started['cuda_visible_devices'],'model_hashes_verified':ready['model_hash_verified'],'model_manifest_sha256':ready['manifest_sha256'],'reference20_passed':ready['reference20_passed'],'ready_utc':ready['utc'],'reference20_sha256':ready['reference20_sha256'],'completed_utc':finished['utc'],
        'score_file_counts':{n:len(list((BASE/'public255/mapped_scores'/n).glob('*.json'))) for n in ['rand3','old_s7']},'no_outcome_labels_read':True,
        'contact':'No confirmed direct contact endpoint for hzx; no claim of having contacted him. User previously said GPU3 could not be yielded. PID592686 has now ended; attribution and planned duration remain unconfirmed.'}
    save(BASE/'wjb_joint_window_execution_record.json',window)
    for log in ['docs/PREREG_LOG.txt','docs/OPS_LOG.txt']:
        with (ROOT/log).open('a') as f:
            f.write(now+' PUBLIC_WG_TIMELINE_CORRECTION alpha0 completed by done-file mtime 2026-11-08T15:55:12.961224Z; earlier 1670-row report stale. At 02:08 JST completed alpha0/s3/s4, PID2452591 belonged to s5. All ten now complete; no public effect read.\n')
            f.write(now+f' PREFIX_START_LAYERS_POSTHOC reconstructed n={len(available)} counts={dict(counts)} first50={dict(batch)} from immutable order and source/dispatch timestamps; not represented as a pre-start layer-count record. No intermediate effect analysis; search512 replies not used as evaluation responses. SHA={sha(BASE/"prefix254_start_layer_reconstruction.json")}\n')
            f.write(now+f' JOINT_HB_EXECUTION s7 complete={window["s7_completed_utc"]} window start={window["started_utc"]} ready={window["ready_utc"]} complete={window["completed_utc"]}, model hashes/reference20 passed; no effect labels read. GPU3 external process ended without our intervention; hzx ownership not confirmed.\n')
    print(json.dumps({'public_order':NAMES,'prefix':prefix['layers'],'prefix_n':len(available),'first_task_utc':prefix['first_task_utc'],'window':window,'render':render,'report_sha256':{n:sha(BASE/n) for n in ['public_wg_execution_chronology.json','prefix254_start_layer_reconstruction.json','llama_system_placement_and_fields.json','wjb_joint_window_execution_record.json']}},ensure_ascii=False))


if __name__=='__main__':main()
