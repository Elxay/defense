from pathlib import Path
import ast
source=Path(__file__).with_name('round10_analyze.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='choose_match');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'match-helper','exec'),ns);choose=ns['choose_match']
def grid(values):return[dict(alpha=a,ASR_pct=x,new_legal=i,distance_pp=abs(x-30.))for i,(a,x)in enumerate(values)]
_,r=choose(grid([(.25,65),(.5,34),(.75,18)]),30);assert r['endpoint_alphas']==[.5]and r['weights']==[1.]
_,r=choose(grid([(.25,70),(.5,50),(.75,10)]),30);assert r['endpoint_alphas']==[.5,.75]and r['weights']==[.5,.5]
_,r=choose(grid([(.25,70),(.5,60),(.75,50)]),30);assert r is None
_,r=choose(grid([(.25,40),(.5,40)]),30);assert r is None
_,r=choose(grid([(.25,70),(.5,10),(.75,50),(1.,10)]),30);assert r['endpoint_alphas']==[.5,.75]
print('5 matching tests passed: nearest, interpolation, no extrapolation, flat axis, bracket tie')
