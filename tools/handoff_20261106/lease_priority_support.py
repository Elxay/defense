"""Pinned scheduling-only helpers; no outcome aggregation."""
from pathlib import Path
import datetime,hashlib,json,os,time
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'results/audit/pair500';STATE=BASE/'lease_priority';STATE.mkdir(exist_ok=True)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.'+str(os.getpid())+'.tmp');q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');os.replace(q,p)
def verify():
    p=load(BASE/'lease_priority_implementation.json')
    for name,value in p['code_sha256'].items():assert sha(ROOT/name)==value,name
    for name,value in p['dependencies_sha256'].items():assert sha(ROOT/name)==value,name
def request_path(card):return STATE/('request_gpu'+str(card)+'.json')
def auxiliary_yield(card,started=None,max_seconds=540):
    if request_path(card).exists():return True
    if started is not None and time.monotonic()-started>=max_seconds:return True
    if str(card)=='0':
        from borrowed_gpu_support import gpu0_must_yield
        if gpu0_must_yield():return True
    return False
