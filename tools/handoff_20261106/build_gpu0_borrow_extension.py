"""Build a scheduling-only extension without changing any running source file."""
from pathlib import Path
import ast
import json
import hashlib

ROOT=Path('/data/HZX/Def');TOOLS=ROOT/'tools/handoff_20261106';BASE=ROOT/'results/audit/pair500'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    original=(TOOLS/'prefix_generate.py').read_text();s=original
    s=s.replace('import collections\n','import collections\nfrom borrowed_gpu_support import verify_extension, gpu0_must_yield\n')
    s=s.replace('    verify_code();cfg=','    verify_extension();verify_code();cfg=')
    s=s.replace("(['2','3'] if node()=='innet'", "(['0','2','3'] if node()=='innet'")
    s=s.replace("PREFIX/('node_gate_generated' if task.get('gate') else 'generation.private')/name", "PREFIX/(task.get('gate_output','node_gate_generated') if task.get('gate') else 'generation.private')/name")
    needle='    for i,row in enumerate(todo,1):\n'
    s=s.replace(needle,needle+"        if os.environ['DEVICE']=='cuda:0' and gpu0_must_yield():\n            save(PREFIX/'live'/f'{name}_{node()}_{os.getpid()}.json',{'utc':utc(),'pid':os.getpid(),'phase':'borrowed_gpu0_yield','condition':name,'done':i-1,'total':len(todo)})\n            raise SystemExit(75)\n        row_started=time.monotonic()\n")
    s=s.replace("        save(out/(row['id']+'.json'),{'id':row['id'],'signature':signature(name,row,cfg),'result':result,", "        execution_signature={**signature(name,row,cfg),'device_uuid':result['device_uuid'],'physical_gpu':os.environ['DEVICE']}\n        save(out/(row['id']+'.json'),{'id':row['id'],'signature':signature(name,row,cfg),'execution_signature':execution_signature,'execution_signature_sha256':hashlib.sha256(__import__('json').dumps(execution_signature,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'row_seconds':time.monotonic()-row_started,'result':result,")
    def numeric_calls(text):
        tree=ast.parse(text);names={'generate_with_injection','AutoModelForCausalLM.from_pretrained','AutoTokenizer.from_pretrained'};out=[]
        for x in ast.walk(tree):
            if isinstance(x,ast.Call) and ast.unparse(x.func) in names:out.append(ast.dump(x,include_attributes=False))
        return sorted(out)
    assert numeric_calls(s)==numeric_calls(original)
    (TOOLS/'prefix_generate_borrowed.py').write_text(s)
    original_master=(TOOLS/'prefix_controller_dual.py').read_text();s=original_master
    s=s.replace('import prefix_controller as old','from borrowed_gpu_support import verify_extension, gpu0_enabled\nimport prefix_controller as old')
    s=s.replace('prefix_generate.py --task','prefix_generate_borrowed.py --task')
    s=s.replace('flock(fcntl', 'flock(fcntl')
    s=s.replace('fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);verify_code()','fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);verify_extension();verify_code()')
    s=s.replace("for device in ['2','3']:","for device in ['2','3','0']:\n                    if device=='0' and not gpu0_enabled():continue")
    s=s.replace("save(PREFIX/'dual_live.json',state)","save(PREFIX/'triple_live.json',state)")
    s=s.replace("'early_generation_dual'", "'early_generation_borrowed_three_lanes'")
    # Post-search completion remains under the already-frozen node fallback, not borrowed GPU0.
    (TOOLS/'prefix_controller_borrowed.py').write_text(s)
    checks={'original_generator_sha256':sha(TOOLS/'prefix_generate.py'),'extended_generator_sha256':sha(TOOLS/'prefix_generate_borrowed.py'),'numeric_model_and_generation_calls_AST_equal':True,'old_runtime_sha256':sha(BASE/'prefix254_runtime.json'),'no_existing_source_modified':True}
    (BASE/'gpu0_borrow_numeric_check.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks))

if __name__=='__main__':main()
