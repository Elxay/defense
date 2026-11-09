"""Portable, immutable per-row generation and diagnostic node gates."""
import argparse
import hashlib
import os
from pathlib import Path
import socket
import sys
import time
import collections

from prefix_support import ROOT,BASE,PREFIX,RUNTIME,load,save,sha,utc,node,verify_role,verify_code,signature,verify_record,render_audit


def yield_to_hb():
    if node()!='innet':return False
    import subprocess
    pending=any(len(list((BASE/'public255/mapped_scores'/n).glob('*.json')))<2000 for n in ['rand3','old_s7'])
    ready=all(len(list((BASE/'public255/harmful.private'/n/'wildjailbreak_harmful').glob('*.json')))==2000 for n in ['rand3','old_s7'])
    if not(pending and ready):return False
    launched=BASE/'prefix254_launches.json'
    if not launched.exists():launched=BASE/'night27_launches.json'
    if launched.exists():
        parent=load(launched)['launch_shell_pids']['joint_hb']
        if not Path('/proc',str(parent)).exists():return False
    used=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits','-i','3'],text=True).strip())
    return used<=2000


def main():
    p=argparse.ArgumentParser();p.add_argument('--task',required=True);a=p.parse_args()
    verify_code();cfg=load(RUNTIME);task=load(a.task);name=task['condition'];assert name in cfg['conditions']
    assert task['runtime_sha256']==sha(RUNTIME)
    rows={r['id']:r for r in load(BASE/'rows.private.json')}
    snapshot=BASE/'frozen_prompt_snapshot.json'
    prefix_ids=([x['id'] for x in load(snapshot)['rows']] if snapshot.exists() else list(load(PREFIX/'accepted_source_files.json')))
    save(PREFIX/'launch_metadata'/(Path(a.task).stem+'_'+node()+'_'+str(os.getpid())+'.json'),{
        'utc':utc(),'pid':os.getpid(),'task_sha256':sha(a.task),'condition':name,'node':node(),'physical_device':os.environ.get('DEVICE'),
        'prefix_n':len(prefix_ids),'prefix_layers':dict(collections.Counter(rows[k]['layer'] for k in prefix_ids)),
        'batch_n':len(task['items']),'batch_layers':dict(collections.Counter(rows[x['id']]['layer'] for x in task['items'])),
        'before_model_load_and_generation':True})
    assert os.environ['DEVICE']=='cuda:'+os.environ['CUDA_VISIBLE_DEVICES'] and ',' not in os.environ['CUDA_VISIBLE_DEVICES']
    assert os.environ['CUDA_VISIBLE_DEVICES'] in (['2','3'] if node()=='innet' else ['0','1','2'])
    out=PREFIX/('node_gate_generated' if task.get('gate') else 'generation.private')/name
    todo=[]
    for row in task['items']:
        assert hashlib.sha256(row['prompt'].encode()).hexdigest()==row['prompt_sha256']
        path=out/(row['id']+'.json')
        if path.exists():verify_record(path,name,row,cfg)
        else:todo.append(row)
    if not todo:return
    verify_role('target')
    assert sha(ROOT/'src/gen/common.py')==cfg['core_sha256']
    import torch,numpy as np,transformers
    from transformers import AutoModelForCausalLM,AutoTokenizer
    sys.path.insert(0,str(ROOT/'src'));from gen.common import generate_with_injection
    spec=cfg['conditions'][name];vector=np.zeros(4096,dtype=np.float32)
    if 'vector' in spec:
        path=ROOT/spec['vector'];assert sha(path)==spec['file_sha256']
        frozen=ROOT/spec['injection_buffer'];assert sha(frozen)==spec['injection_buffer_file_sha256']
        vector=np.load(frozen).astype(np.float32)
        assert hashlib.sha256((vector+0.).tobytes()).hexdigest()==spec['injection_sha256']
    tokenizer=AutoTokenizer.from_pretrained(cfg['models'][node()]['target'],local_files_only=True)
    model=AutoModelForCausalLM.from_pretrained(cfg['models'][node()]['target'],torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval()
    start=time.monotonic()
    for i,row in enumerate(todo,1):
        if yield_to_hb():
            save(PREFIX/'live'/f'{name}_{node()}_{os.getpid()}.json',{'utc':utc(),'pid':os.getpid(),'phase':'yielding_hb_window','condition':name,'done':i-1,'total':len(todo)})
            raise SystemExit(75)
        if spec.get('system_prompt'):
            ids,audit=render_audit(tokenizer,row['prompt'],name,spec['system_prompt'])
        else:
            ids=tokenizer.apply_chat_template([{'role':'user','content':row['prompt']}],add_generation_prompt=True,return_tensors='pt')
            audit={'input_ids_sha256':hashlib.sha256(ids.cpu().numpy().astype('<i8').tobytes()).hexdigest()}
        result=generate_with_injection(model,tokenizer,ids.to('cuda:0'),vector,layer=9,max_new_tokens=2400,device='cuda:0',src_vec_sha256=spec.get('file_sha256'),alpha=spec['alpha'])
        result.update(audit);result['rho_runtime']=float(np.linalg.norm(vector))
        save(out/(row['id']+'.json'),{'id':row['id'],'signature':signature(name,row,cfg),'result':result,
            'generation_node':node(),'host':socket.gethostname(),'physical_gpu':os.environ['DEVICE'],
            'worker_sha256':sha(Path(__file__)),'torch_version':torch.__version__,'transformers_version':transformers.__version__})
        save(PREFIX/'live'/f'{name}_{node()}_{os.getpid()}.json',{'utc':utc(),'pid':os.getpid(),'phase':'generation','condition':name,'device':os.environ['DEVICE'],'done':i,'total':len(todo),'seconds_per_row':(time.monotonic()-start)/i})


if __name__=='__main__':main()
