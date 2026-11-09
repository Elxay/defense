"""Save masked model annotations without revealing sample groups."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT=Path('/data/HZX/Def');OUT=ROOT/'results/audit/pair500/public_read_20261109'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def write(batch,labels):
    public=json.loads((OUT/'recall_selection_manifest.json').read_text());assert sha(OUT/'recall_blind.private.json')==public['blind_file_sha256']
    previous=[r for p in OUT.glob('model_labels_batch*.json') for r in json.loads(p.read_text())['labels']];used={r['review_index'] for r in previous}
    rows=[]
    for index,category,reason in labels:
        assert 1<=index<=180 and index not in used and category in ['R','RA','W','C','U'];used.add(index)
        rows.append({'review_index':index,'category':category,'reason_code':reason,'read_scope':'complete original task and complete stored120-token response'})
    path=OUT/f'model_labels_batch{batch:02d}.json';assert not path.exists()
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();value={'utc':now,'batch':batch,'blind_file_sha256':public['blind_file_sha256'],'annotator':'current GPT-6-family Codex conversation; exact snapshot not exposed','shared_context':True,'human_calibration':False,'labels':rows,'writer_source_sha256':sha(Path(__file__))}
    path.write_text(json.dumps(value,indent=2)+'\n')
    with (ROOT/'docs/PREREG_LOG.txt').open('a') as f:f.write(f'{now} MASKED_PUBLIC_RECALL_MODEL_BATCH batch={batch} n={len(rows)} cumulative={len(used)} SHA={sha(path)}; condition/group/rule/WG fields masked, shared context, no human calibration.\n')
    print(json.dumps({'batch':batch,'n':len(rows),'cumulative':len(used),'utc':now,'sha256':sha(path)}))
