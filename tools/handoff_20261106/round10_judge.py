"""Score addendum8 rand2/rand3 using unchanged validated HF functions and gate."""
from pathlib import Path
import ast, datetime, hashlib, json, os, socket, sys, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
ROOT=Path('/data/HZX/Def')
import fcntl
os.environ['DSH_OWNER']='/data/HZX/Def'
with (ROOT/'logs/pid_registry.txt').open('a') as reg:
    fcntl.flock(reg,fcntl.LOCK_EX)
    reg.write(str(os.getpid())+'|'+__import__('subprocess').check_output(['ps','-p',str(os.getpid()),'-o','lstart='],text=True).strip()+'|'+str(Path(__file__))+'\n')
    reg.flush()

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/'night/hf_judge_round2_reference.py'
tree=ast.parse(source.read_text())
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['free','p_yes','judge_text']]
assert len(functions)==3
os.environ['TOKENIZERS_PARALLELISM']='false'
tok=AutoTokenizer.from_pretrained('/data/HZX/Def/local_judge13b',local_files_only=True)
CLS=(ROOT/'night/cls_prompt.txt').read_text()
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='2,3', 'physical GPU2/3 isolation required'
exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),globals())
fr=free();print('FREE',fr,flush=True)
used=__import__('subprocess').check_output(['nvidia-smi','--query-gpu=index,memory.used','--format=csv,noheader,nounits'],text=True)
usage={int(x.split(',')[0]):int(x.split(',')[1]) for x in used.splitlines()}
if any(usage.get(i,999999)>2000 for i in [2,3]):raise RuntimeError('wait_gpu refusal: GPU2/3 not idle; no bypass')
mdl=AutoModelForCausalLM.from_pretrained('/data/HZX/Def/local_judge13b',torch_dtype=torch.bfloat16,device_map='auto',max_memory={0:'13GiB',1:'13GiB','cpu':'0GiB'},local_files_only=True).eval()
rows=json.loads((ROOT/'configs/stage0_data/wjb300.json').read_text());beh={x['id']:x['vanilla'] for x in rows}
base=json.loads((ROOT/'results/audit/WJB_A0_merged.json').read_text())
reference=json.loads((ROOT/'results/hfjudge/JUDGE_HF_wjb_a0_innet_round2').read_text())['items']
randpath=ROOT/'results/audit/WJB_A0_merged.json';rand=json.loads(randpath.read_text())
assert set(rand)==set(beh)==set(base)==set(reference) and len(rand)==300
gate_keys=sorted(reference,key=lambda k:abs(reference[k]['p_yes']-.5))[:20]
gate=[]
for key in gate_keys:
    p,_,_=judge_text(beh[key],base[key]['text'])
    gate.append({'id':key,'reference':reference[key]['p_yes'],'p_yes':p,'abs_delta':abs(p-reference[key]['p_yes']) if p is not None else None})
passed=all(r['abs_delta'] is not None and r['abs_delta']<1e-3 for r in gate) and sum(.05<=r['reference']<=.95 for r in gate)>=8 and sum(r['p_yes'] is not None and .05<=r['p_yes']<=.95 for r in gate)>=8
print('GATE',passed,'max',max(r['abs_delta'] or 0 for r in gate),flush=True)
for label,input_name,target_name in [('wjb_a0_innet_round2','WJB_A0_merged.json','results/hfjudge/JUDGE_HF_wjb_a0_innet_round2'),('wjb_rand0_innet_round2','WJB_rand0.json','results/hfjudge/JUDGE_HF_wjb_rand0_innet_round2')]:
    randpath=ROOT/'results/audit'/input_name
    rand=json.loads(randpath.read_text())
    assert len(rand)==300 and set(rand)==set(beh)

assert passed, 'same-backend gate failed; do not judge new conditions'
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['repeats','grid','full'],required=True);args=parser.parse_args()
O=ROOT/'results/audit/handoff_round10'
def pulse(phase,**kw):
 p=O/'judge_live.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),phase=phase,physical_gpus=[2,3],**kw),indent=2));q.replace(p)
wjb_beh=beh;val_beh=json.loads((ROOT/'results/audit/handoff_round7/val70_behaviors.json').read_text());jobs=json.loads((O/f'judge_jobs_{args.phase}.json').read_text())
for job in jobs:
 beh=wjb_beh if job['kind']=='wjb'else val_beh;source_path=ROOT/job['input_file'];raw=json.loads(source_path.read_text());data=raw['items']if 'items'in raw else raw;assert len(data)==job['n']and set(data)==set(beh)
 signature=dict(input_file=job['input_file'],source_sha256=sha(source_path),backend='hf_innet',classifier_prompt_sha256=sha(ROOT/'night/cls_prompt.txt'),reference_functions_sha256=sha(source),judge_script_sha256=sha(Path(__file__)),baseline_file=job['baseline_file'],refusal_fn_sha256=sha(ROOT/'src/judge/refusal.py'))
 cache=ROOT/job['target_file'];partial=cache.with_suffix('.partial.json')
 if cache.exists():
  saved=json.loads(cache.read_text());assert saved['signature']==signature and saved['invalid']==0 and saved['n']==job['n'];continue
 saved=json.loads(partial.read_text())if partial.exists()else dict(signature=signature,items={});assert saved['signature']==signature;out=saved['items'];begin=time.monotonic();initial=len(out)
 for key in beh:
  if key in out:continue
  p,ps,ch=judge_text(beh[key],data[key]['text']);assert p is not None,'INVALID: stop, no coercion';out[key]=dict(p_yes=p,chunked=ch,chunk_ps=ps);n=len(out)
  if n%10==0:
   q=partial.with_suffix('.tmp');q.write_text(json.dumps(saved,indent=2)+'\n');q.replace(partial);pulse('judging',stage=args.phase,condition=job['tag'],n=n,total=job['n'],seconds_per_item=(time.monotonic()-begin)/max(1,n-initial));print('JUDGED',job['tag'],n,flush=True)
   if min(free().get(j,0)for j in[2,3])<2000:raise RuntimeError('memory watchdog')
 result=dict(signature=signature,items=out,n=job['n'],invalid=0,verified=passed,gate=gate,backend='hf_innet',host=socket.gethostname(),physical_gpus=[2,3]);q=cache.with_suffix('.tmp');q.write_text(json.dumps(result,indent=2)+'\n');q.replace(cache)
pulse('complete',stage=args.phase,n_conditions=len(jobs))
