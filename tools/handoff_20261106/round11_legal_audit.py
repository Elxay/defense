from pathlib import Path
import json,re,ast,hashlib,datetime,sys,random
B=Path('/data/HZX/Def');O=B/'results/audit/handoff_round11';sys.path.insert(0,str(B/'src'));from judge.refusal import new_rule

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def func(path,name,ns):
 node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name==name);exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns);return ns[name],hashlib.sha256(ast.get_source_segment(path.read_text(),node).encode()).hexdigest()
v3,v3sha=func(B/'tools/handoff_20261106/audit.py','v3',{'re':re});vb,vbsha=func(B/'tools/handoff_20261106/analyze_doc246_complete.py','vb',{'re':re,'new_rule':new_rule});rules={'v2':new_rule,'v2_union_saved_v3':lambda x:new_rule(x)or v3(x),'V_b':vb}
basefile=B/'results/audit/LEGALVALB_none.json';base=json.loads(basefile.read_text());eligible=[k for k,v in base.items()if not new_rule(v['text'])];assert len(eligible)==388;prompts={r['key']:r['prompt']for r in json.loads((B/'data/legal_val_items.json').read_text())};matches=json.loads((B/'results/style_retrained/alpha_matches_frozen.json').read_text());rng=random.Random(202611070254);summary=[];sample=[]
for arm in ['control','treatment']:
 for seed in range(3,8):
  alpha=1. if arm=='control'else matches['rows'][str(seed)]['selected_alpha'];path=B/f'results/style_retrained/eval_s{seed}/{arm}_a{alpha:g}_legal400.json';data=json.loads(path.read_text())['items'];assert set(data)==set(base)
  for name,rule in rules.items():
   own=[k for k,v in base.items()if not rule(v['text'])];summary.append(dict(seed=seed,arm=arm,alpha=alpha,vector_norm=5.21*alpha,rule=name,common_n=388,new_common=sum(rule(data[k]['text'])and not rule(base[k]['text'])for k in eligible),own_baseline_n=len(own),new_own_baseline=sum(rule(data[k]['text'])for k in own),baseline_rule_positives=sum(rule(v['text'])for v in base.values()),baseline_file=str(basefile.relative_to(B)),source_file=str(path.relative_to(B)),source_sha256=sha(path),refusal_fn_sha256=sha(B/'src/judge/refusal.py')))
  pool=[k for k in eligible if not rules['v2_union_saved_v3'](data[k]['text'])];selected=rng.sample(sorted(pool),6)
  for k in selected:sample.append(dict(seed=seed,arm=arm,alpha=alpha,key=k,prompt=prompts[k],text=data[k]['text'],baseline_text=base[k]['text'],sample_population='v2_union_saved_v3 negative within frozen388,6perseed',text_sha256=hashlib.sha256(data[k]['text'].encode()).hexdigest(),n_chars=len(data[k]['text']),source_file=str(path.relative_to(B))))
assert len(sample)==60;order=list(range(60));rng.shuffle(order);blind=[];mapping={}
for index,original in enumerate(order):
 r=sample[original];blind.append(dict(blind_id=f'blind{index:02d}',prompt=r['prompt'],text=r['text'],n_chars=r['n_chars'],text_sha256=r['text_sha256']));mapping[f'blind{index:02d}']=r
now=datetime.datetime.now(datetime.timezone.utc).isoformat();meta=dict(utc=now,rng_seed=202611070254,match_sha256=sha(B/'results/style_retrained/alpha_matches_frozen.json'),v2_file_sha256=sha(B/'src/judge/refusal.py'),v3_ast_sha256=v3sha,Vb_ast_sha256=vbsha,v3_source='tools/handoff_20261106/audit.py',Vb_source='tools/handoff_20261106/analyze_doc246_complete.py',baseline_file=str(basefile.relative_to(B)),baseline_sha256=sha(basefile),sampling_note='post-hoc;30perarm,6perseed,union-negative pool; not random over entire400 and not human calibration')
for name,data in [('legal_rule_sensitivity.json',dict(metadata=meta,rows=summary)),('legal_recall_blind60.json',dict(metadata=meta,items=blind)),('legal_recall_blind60_mapping.json',dict(metadata=meta,items=mapping))]:(O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
with(B/'docs/PREREG_LOG.txt').open('a')as f:f.write(now+' LEGAL_POSTHOC_RECALL_SAMPLE_FROZEN rng202611070254 union-negative fixed388 6perseed30perarm, blindedorder; v3/Vb sensitivity computed samebaseline; before anytwoarm holdout effect aggregate read. sampleSHA='+sha(O/'legal_recall_blind60.json')+'\n')
print('LEGAL_RULE_COUNTS')
for arm in ['control','treatment']:
 for rule in rules:
  rows=[r for r in summary if r['arm']==arm and r['rule']==rule];print(arm,rule,'common388',[r['new_common']for r in rows],'own_n',[r['own_baseline_n']for r in rows],'own_new',[r['new_own_baseline']for r in rows])
