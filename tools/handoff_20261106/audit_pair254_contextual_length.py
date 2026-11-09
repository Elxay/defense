"""Measure formatted classifier inputs on CPU, without reading judge outcomes."""
from pathlib import Path
import collections,datetime,hashlib,json,os,sys
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['HF_HUB_OFFLINE']='1';os.environ['USE_TF']='0';os.environ['USE_FLAX']='0'
R=Path('/data/HZX/Def');B=R/'results/audit/pair500';sys.path.insert(0,str(R/'tools/handoff_20261106'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    from transformers import AutoTokenizer
    from pair500_score import harmbench_scope,clip
    cfg=json.loads((B/'prefix254_runtime.json').read_text());tok=AutoTokenizer.from_pretrained(cfg['models']['innet']['judge'],local_files_only=True);maxpos=json.loads((Path(cfg['models']['innet']['judge'])/'config.json').read_text())['max_position_embeddings'];template=harmbench_scope(R/'repos/HarmBench/eval_utils.py','classifier')['LLAMA2_CLS_PROMPT']['prompt_contextual'];rows={r['id']:r for r in json.loads((B/'rows.private.json').read_text())if r['layer']=='contextual'};measure=[];empty=[]
    for key,row in rows.items():
        empty.append({'id':key,'tokens_without_generation':len(tok(template.format(behavior=row['behavior'],context=row['context'],generation='')).input_ids)})
    for folder in(B/'prefix254/generation.private').glob('*'):
        if not folder.is_dir():continue
        for key,row in rows.items():
            p=folder/(key+'.json')
            if not p.exists():continue
            text=json.loads(p.read_text())['result']['text'];generation=clip(tok,text,512);n=len(tok(template.format(behavior=row['behavior'],context=row['context'],generation=generation)).input_ids);measure.append({'condition':folder.name,'id':key,'tokens':n,'generation_sha256':sha(p)})
    lengths=sorted(x['tokens']for x in measure);conditions={n:{'n':len(z),'min':min(x['tokens']for x in z),'max':max(x['tokens']for x in z),'over1900':sum(x['tokens']>1900 for x in z),'over2048':sum(x['tokens']>2048 for x in z)}for n in sorted({x['condition']for x in measure})for z in [[x for x in measure if x['condition']==n]]}
    result={'started_scope':'Current generated prefix only; no outcome labels, probabilities or INVALID fields read.','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_contextual_rows':len(rows),'measured_generated_inputs':len(measure),'model_max_positions':maxpos,'min_tokens':min(lengths),'max_tokens':max(lengths),'over1900':sum(n>1900 for n in lengths),'over2048':sum(n>2048 for n in lengths),'chunked_inputs':0,'actual_path':'PAIR incremental/final HF scorer formats original context+behavior+512-token-clipped generation, then refuses >max_position_embeddings; does not call night/judge_all.py.','legacy_path':'night/judge_all.py uses legacy CLS_PROMPT/behavior[:600], splits full rendered input >1900 into overlapping pieces. It is not the official contextual template path and is not used here.','per_condition':conditions,'overflow_rows':[x for x in measure if x['tokens']>maxpos],'without_generation_max':max(x['tokens_without_generation']for x in empty),'all100_contextual_rows_reviewed_for_source_length':True,'future_rule':'Stop on overflow; no silent truncation or unlogged switch to chunking. Re-audit after complete generation.','source_sha256':{n:sha(R/n)for n in ['night/judge_all.py','tools/handoff_20261106/prefix_hb_incremental_worker.py','tools/handoff_20261106/pair500_eval254.py']}}
    o=B/'tail_contextual_followup_20261109';o.mkdir(exist_ok=True);p=o/'contextual_length_audit.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'file':str(p.relative_to(R)),'sha256':sha(p),**{k:v for k,v in result.items()if k not in ['per_condition','source_sha256','overflow_rows']}}))
if __name__=='__main__':main()
