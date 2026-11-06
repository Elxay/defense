"""Score completed WJB rand0 with the existing HF judge functions and a 20-item gate."""
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
passed=all(r['abs_delta'] is not None and r['abs_delta']<1e-3 for r in gate)
print('GATE',passed,'max',max(r['abs_delta'] or 0 for r in gate),flush=True)
for label,input_name,target_name in [('wjb_a0_innet_round2','WJB_A0_merged.json','results/hfjudge/JUDGE_HF_wjb_a0_innet_round2'),('wjb_rand0_innet_round2','WJB_rand0.json','results/hfjudge/JUDGE_HF_wjb_rand0_innet_round2')]:
    randpath=ROOT/'results/audit'/input_name
    rand=json.loads(randpath.read_text())
    assert len(rand)==300 and set(rand)==set(beh)

assert passed, 'same-backend gate failed; do not judge new conditions'
for tag in ['old_s3_a1.0','old_s4_a1.0','rand1']:
    input_path=ROOT/f'results/audit/WJB_{tag}.json'
    data=json.loads(input_path.read_text())
    assert len(data)==300 and set(data)==set(beh)
    out={}
    for i,key in enumerate(beh):
        p,ps,ch=judge_text(beh[key],data[key]['text'])
        out[key]={'p_yes':p,'chunked':ch,'chunk_ps':ps}
        if (i+1)%50==0:
            print(tag,'JUDGED',i+1,flush=True)
            if min(free().get(j,0) for j in [2,3])<2000:raise RuntimeError('memory watchdog')
    result={'file':tag,'items':out,'n':300,'invalid':sum(v['p_yes']is None for v in out.values()),'backend':'hf_innet','host':socket.gethostname(),'verified':passed,'gate':gate,'gate_mid_count':sum(.05<=r['reference']<=.95 for r in gate),'source_sha256':sha(input_path),'refusal_fn_sha256':sha(ROOT/'src/judge/refusal.py'),'baseline_file':'results/hfjudge/JUDGE_HF_wjb_a0_innet_round2'}
    target=ROOT/f'results/hfjudge/JUDGE_HF_wjb_{tag}_innet'
    assert not target.exists()
    temp=target.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2)+'\n');temp.replace(target)
    print('SCORED',tag,flush=True)
