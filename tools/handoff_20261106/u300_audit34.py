from u300_schedule_prepare import *
import sys,collections,re,os,shlex,statistics
sys.path.insert(0,str(T));from u300_alpha0_cache_scope20 import load_alpha0_cache
O=U/'followup34';O.mkdir(exist_ok=True)
schedule=H(U/'scoring_schedule_v1.json')
def labs(w):
 rows=L(U/'score_waves'/w/'inputs.private.json');return rows,{r['id']:load_alpha0_cache(R,r,schedule)['label'] for r in rows}
old,a=labs('search88_PAIR_qwen');new,b=labs('search132_PAIR_qwen');tap,t=labs('search88_TAP_qwen')
base=L(U/'score_waves/SORRY_0001/inputs.private.json');br=[r for r in base if r['model']=='qwen' and r['condition']=='alpha0' and r['family'] in ['base','direct','direct_request','direct-request','basic']]
if not br:
 print('BASE_FAMILIES',sorted(set((r['model'],r['family'],r['condition']) for r in base if r['condition']=='alpha0')))
 # Resolve only explicitly sealed alpha0 waves, without opening score records for nonzero rows.
 for w in sorted((U/'score_waves').iterdir()):
  if not w.name.startswith('SORRY_'):continue
  p=w/'inputs.private.json'
  if not p.exists():continue
  rs=L(p);cand=[r for r in rs if r['model']=='qwen' and r['condition']=='alpha0' and r['family'] in ['base','direct','direct_request','direct-request','basic']]
  if cand:br=cand;break
assert br,'No exact base alpha0 manifest found'
d={r['id']:load_alpha0_cache(R,r,schedule)['label'] for r in br}
def trans(ids,other):
 assert all(d[i] in [0,1] and other[i] in [0,1] for i in ids)
 mat=collections.Counter((d[i],other[i]) for i in ids)
 return dict(N=len(ids),direct=sum(d[i] for i in ids),search=sum(other[i] for i in ids),up=mat[0,1],down=mat[1,0],unchanged=mat[0,0]+mat[1,1],matrix={str(k):v for k,v in sorted(mat.items())})
ids78={L(p)['id'] for p in Path('/tmp/tap88/rows').glob('*.json')}
out=dict(utc=utc(),PAIR88=trans(list(a),a),PAIR132=trans(list(b),b),PAIR220=trans(list(a)+list(b),{**a,**b}),TAP78=trans(sorted(ids78),t),PAIR_same78=trans(sorted(ids78),a))
raw=L(R/'results/audit/sorry296/downloads.private/sorry-bench-202503/question.jsonl') if False else [json.loads(x) for x in (R/'results/audit/sorry296/downloads.private/sorry-bench-202503/question.jsonl').read_text().splitlines()]
print('SORRY_KEYS',list(raw[0]));out['source_base_manifest_rows']=len(br)
for method in ['PAIR','TAP']:
 D=U/'search88_alpha0_v19'/method/'llama';out[method+'_llama']=dict(complete=L(D/'complete.json'),gate=L(D/'gate_read.json') if (D/'gate_read.json').exists() else None)
save(O/'transitions.json',out);print('TRANSITIONS',json.dumps({k:v for k,v in out.items() if 'llama' not in k}))
ep=L(U/'encoding_alpha0_plan_v2.json');inp=L(U/'encoding_alpha0_inputs.private.json');cfg=ep['models']['llama']['families']['ascii'];by={str(r['id']):r for r in inp['llama']['ascii']};tail=[dict(position=i+1,id=int(k),prompt_tokens=len(by[str(k)]['input_ids'])) for i,k in enumerate(cfg['ordered_IDs']) if i>=424];save(O/'ASCII_tail_lengths.json',dict(utc=utc(),rows=tail,max_prompt_tokens=max(r['prompt_tokens'] for r in tail),min_prompt_tokens=min(r['prompt_tokens'] for r in tail)));print('ASCII_TAIL',json.dumps(tail))
lang=[]
for folder in (U/'language_processed33').iterdir():
 if not folder.is_dir() or folder.name=='gates':continue
 records=[L(p) for p in (folder/'processed.private').glob('*.json')];counts=collections.Counter(z.get('status') or z.get('failure_type') for z in records);bad=[z for z in records if z.get('primary_INVALID')];secs=sum(z.get('elapsed_seconds',0) for z in records)
 lang.append(dict(cell=folder.name,N=len(records),status_counts=dict(counts),INVALID_IDs=[z['id'] for z in bad],row_processing_seconds=secs,rows_per_active_hour=len(records)*3600/secs if secs else None,complete=L(folder/'complete.json') if (folder/'complete.json').exists() else None))
save(O/'translation_status.json',dict(utc=utc(),cells=lang));print('LANG',json.dumps([{k:v for k,v in z.items() if k!='complete'} for z in lang]))
os.environ['HF_DATASETS_OFFLINE']='1';os.environ['HF_HUB_OFFLINE']='1'
from datasets import load_dataset,DownloadConfig
arc=load_dataset('allenai/ai2_arc','ARC-Challenge',split='test',download_config=DownloadConfig(local_files_only=True));M=L(R/'configs/benign_cost_manifest_20261212.json');gold={r['id']:arc[int(r['id'].split(':')[1])]['answerKey'] for r in M['sets']['arc_c_200']};oldgold=gold.copy();corrections=[]
for i,v in list(gold.items()):
 if v not in 'ABCD':
  row=arc[int(i.split(':')[1])];labels=row['choices']['label'];gold[i]='ABCD'[labels.index(v)];corrections.append(dict(id=i,old_key=v,choice_labels=labels,canonical_key=gold[i]))
acc={}
for m,conds in [('llama',['alpha0','s3','s4','s5','rand0','rand1']),('qwen',['alpha0','s3','s4','s5','61000','61001'])]:
 rows=[]
 for c in conds:
  vals=L(U/'cost_WG'/m/c/'arc_c_200.json')['items'];assert set(vals)==set(gold);n=0;oldn=0;inv=0
  for i,v in vals.items():
   match=re.search(r'\b([ABCD])\b',v['response'][:200],re.I);pred=match.group(1).upper() if match else None;inv+=pred is None;n+=pred==gold[i];oldn+=pred==oldgold[i]
  rows.append(dict(condition=c,N=200,correct=n,old_key_correct=oldn,INVALID=inv,accuracy_bounds_pct=[n/2,(n+inv)/2],old_key_accuracy_bounds_pct=[oldn/2,(oldn+inv)/2]))
 by={z['condition']:z for z in rows};learn=[sum(by[c]['accuracy_bounds_pct'][j] for c in conds[1:4])/3 for j in [0,1]];rand=[sum(by[c]['accuracy_bounds_pct'][j] for c in conds[4:])/2 for j in [0,1]]
 acc[m]=dict(rows=rows,learned_minus_random_pp_bounds=[learn[0]-rand[1],learn[1]-rand[0]],learned_minus_alpha0_pp_bounds=[learn[0]-rows[0]['accuracy_bounds_pct'][1],learn[1]-rows[0]['accuracy_bounds_pct'][0]])
save(O/'ARC_accuracy_bounds.json',dict(utc=utc(),models=acc,numeric_key_corrections=corrections,protocol='first standalone A-D in first200 chars; INVALID 0/1; N200 fixed denominator',conditional_on_frozen_vectors=True));print('ARC',json.dumps(acc));print('ARC_GOLD',json.dumps(corrections))
