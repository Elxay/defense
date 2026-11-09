"""User-authorized GPU0 time extension; retain every original numerical source."""
from pathlib import Path
import hashlib,inspect,json
R=Path(__file__).resolve().parents[2];B=R/'results/audit/pair500'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def install():
    import borrowed_gpu_support as original
    if getattr(original,'_day_authorization_installed',False):return
    a=json.loads((B/'gpu0_day_authorization.json').read_text())
    for n,h in a['new_code_sha256'].items():assert sha(R/n)==h,n
    assert sha(R/a['document'])==a['document_sha256']
    assert sha(B/'gpu0_borrow_publication.json')==a['original_borrow_publication_sha256']
    source=inspect.getsource(original.gpu0_must_yield);needle="cfg=json.loads((BASE/'gpu0_borrow_publication.json').read_text())";assert source.count(needle)==1
    source=source.replace(needle,'cfg=authorized_current_window()')
    scope=dict(original.__dict__);scope['authorized_current_window']=lambda:{'borrow_until_utc':a['valid_until_utc']};exec(compile(source,'authorized_gpu0_schedule_only','exec'),scope)
    original.gpu0_must_yield=scope['gpu0_must_yield'];original._day_authorization_installed=True
