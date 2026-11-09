"""CPU-only fixed-target tokenization and signed U1 payload checks."""
from pathlib import Path
import collections,csv,datetime,difflib,hashlib,json,re,statistics,sys,unicodedata
from transformers import AutoTokenizer
from crossmodel287_assets_and_render import model_path,render,fastchat_template
R=Path('/data/HZX/Def');C=R/'results/audit/crossmodel287';sys.path.insert(0,str(R/'src'))
from judge.refusal import new_rule
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def textsha(x):return hashlib.sha256(x.encode()).hexdigest()
def save(p,x,private=False):
 assert not p.exists(),p.name;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
 if private:p.chmod(0o600)
def summary(values):return {'n':len(values),'min':min(values),'median':statistics.median(values),'max':max(values),'mean':statistics.mean(values)}if values else{'n':0}
def normalize(s):return ' '.join(unicodedata.normalize('NFKC',s).split())
def opener(s):
 s=s.lstrip().lower().replace('’',"'")
 if re.match(r"^(i(?:'m| am) sorry|sorry|i apologize)",s):return 'APOLOGY'
 if re.match(r"^i (cannot|can't|can not|won't|will not|am unable)",s):return 'DIRECT_FIRST_PERSON_REFUSAL'
 if s.startswith('as an'):return 'IDENTITY_PREFIX'
 return 'OTHER'
def main():
 effective=C/'protocol_effective_addendum5_U1.json';spec=json.loads(effective.read_text());assert spec['target_source_branch']['decision']=='U1'
 source=R/spec['target_source_branch']['teacher_file'];assert sha(source)==spec['target_source_branch']['teacher_sha256'];teacher=json.loads(source.read_text());fit=teacher['fit'];targets=teacher['ref_targets'];assert digest(targets)==spec['target_source_branch']['ordered_target_texts_sha256']
 rows=[];results={};qwen_tok=None;compare=None
 for key in ['qwen','gemma','vicuna']:
  path=model_path(key);tok=AutoTokenizer.from_pretrained(str(path),local_files_only=True);lengths=[];full_lengths=[];roundtrips=0;normalized=0;empty=0;unknown=0;special=0;badcode=0;full_prefix=[]
  for item,target in zip(fit,targets):
   prefix=render(tok,key,item['text']);assert prefix==render(tok,key,item['text']);ids=tok(target,add_special_tokens=False)['input_ids'];joined=prefix+ids
   decoded=tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
   exact=decoded==target;norm=normalize(decoded)==normalize(target);roundtrips+=int(exact);normalized+=int(norm);empty+=int(not ids);unknown_n=sum(t==tok.unk_token_id for t in ids)if tok.unk_token_id is not None else 0;special_n=sum(t in tok.all_special_ids for t in ids);unknown+=unknown_n;special+=special_n;badcode+=target.count('\ufffd')
   labels=[-100]*len(prefix)+ids;assert len(joined)==len(labels)and all(t==-100 for t in labels[:len(prefix)])and labels[len(prefix):]==ids
   if key!='vicuna':
    canonical=tok.apply_chat_template([{'role':'user','content':item['text']},{'role':'assistant','content':target}],add_generation_prompt=False)
    prefix_match=canonical[:len(prefix)]==prefix
   else:
    c=fastchat_template();canonical=tok(c['system_message']+c['sep']+c['roles'][0]+': '+item['text']+c['sep']+c['roles'][1]+': '+target+c['sep2'],add_special_tokens=True)['input_ids'];prefix_match=canonical[:len(prefix)]==prefix
   full_prefix.append(prefix_match);lengths.append(len(ids));full_lengths.append(len(joined))
   rows.append({'model':key,'fit_id':item['id'],'target_text_sha256':textsha(target),'target_token_ids_sha256':digest(ids),'native_prompt_ids_sha256':digest(prefix),'training_ids_sha256':digest(joined),'target_tokens':len(ids),'prompt_tokens':len(prefix),'training_tokens':len(joined),'target_unk_tokens':unknown_n,'target_special_tokens':special_n,'strict_roundtrip':exact,'whitespace_normalized_roundtrip':norm,'canonical_complete_chat_prefix_match':prefix_match,'training_label_mask_passed':True})
  results[key]={'repo':spec['models'][key]['repo'],'revision':spec['models'][key]['revision'],'tokenizer_config_sha256':sha(path/'tokenizer_config.json'),'target_lengths':summary(lengths),'training_lengths':summary(full_lengths),'nonempty_targets':12-empty,'target_unk_count':unknown,'target_special_control_count':special,'replacement_unicode_count':badcode,'strict_roundtrip':roundtrips,'whitespace_normalized_roundtrip':normalized,'canonical_complete_chat_prefix_matches':sum(full_prefix),'native_prompt_and_label_mask_checks':12,'target_text_list_sha256':digest(targets),'Gemma_system_baseline':'user_turn_prefix'if key=='gemma'else'not_applicable','training_sequence':'native rendered user prompt with assistant generation prefix + target encoded separately, no special tokens added to target; labels only on target tokens','canonical_full_chat_boundary_note':'separate-tokenized training path is the frozen old recipe; canonical full chat may retokenize whitespace at a boundary; no text normalization or target alteration'}
  assert empty==unknown==special==badcode==0,(key,'unrepresentable or control-bearing target; do not train')
  if key=='qwen':
   native=[]
   for row,target in zip(fit,targets):
    p=C/'qwen_private/fit_alpha0'/(row['id']+'.json');x=json.loads(p.read_text());output=x['output']
    if new_rule(output):
     a=normalize(output);b=normalize(target);native.append({'fit_id':row['id'],'native_alpha0_file_sha256':sha(p),'U1_target_text_sha256':textsha(target),'native_refusal_text_sha256':textsha(output),'native_refusal_tokens':len(tok(output,add_special_tokens=False)['input_ids']),'U1_target_tokens':len(tok(target,add_special_tokens=False)['input_ids']),'exact_same_text':output==target,'word_sequence_similarity':difflib.SequenceMatcher(None,a.split(),b.split()).ratio(),'native_opener_code':opener(output),'U1_opener_code':opener(target)})
   assert len(native)==2
   compare={'native_alpha0_n':12,'native_alpha0_v2_refusal_n':2,'native_alpha0_v2_nonrefusal_n':10,'native_refusal_comparisons':native,'native_refusal_lengths':summary([r['native_refusal_tokens']for r in native]),'same_ID_U1_lengths':summary([r['U1_target_tokens']for r in native]),'exact_same_text_n':sum(r['exact_same_text']for r in native),'all12_U1_opener_counts':dict(collections.Counter(opener(t)for t in targets)),'interpretation':'descriptive text/length differences on two paired baseline refusals; v2 is not a harmfulness or independent human label; no target is selected or replaced from this diagnostic'}
  print(json.dumps({'model':key,'result':results[key]}),flush=True)
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();out=C/'U1_tokenization_check.json';save(out,{'utc':now,'effective_protocol_sha256':sha(effective),'teacher_cache_sha256':sha(source),'code_sha256':sha(Path(__file__)),'GPU_used':False,'model_weights_loaded':False,'target_texts_changed':False,'models':results,'Qwen_native_wording_comparison':compare,'public_rows_contain_only_IDs_lengths_hashes_and_codes':True})
 csvfile=C/'U1_tokenization_rows.csv'
 assert not csvfile.exists()
 with csvfile.open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 # Keep the old conditional pack immutable. Rebind its unchanged payload to U1.
 prior=C/'qwen_transfer_targets.private.json';pack=json.loads(prior.read_text());assert len(pack['fit'])==12 and len(pack['keep'])==60
 assert all(r['id']==a['id']and r['target']==t for r,a,t in zip(pack['fit'],fit,targets))
 pack.update(created_utc=now,branch='U1_fixed_Llama_targets_all_new_models',effective_protocol_sha256=sha(effective),supersedes_metadata_only_private_pack_sha256=sha(prior),target_tokenization_check_sha256=sha(out))
 private=C/'qwen_U1_targets.private.json';save(private,pack,private=True)
 bindings={'utc':now,'effective_protocol_file':str(effective.relative_to(R)),'effective_protocol_sha256':sha(effective),'target_rule':'U1','tokenization_check_sha256':sha(out),'tokenization_rows_sha256':sha(csvfile),'ordered_target_texts_sha256':digest(targets),'model_targets':{'qwen':{'private_pack':str(private.relative_to(R)),'private_pack_sha256':sha(private),'fit12_source':'fixed_Llama_cache','keep60_source':'native_Qwen_alpha0','training_allowed':False,'waiting_for':'hashed addendum4 refusal review and admission'},'gemma':{'fit12_source':'fixed_Llama_cache','keep60_source':'must_generate_native_Gemma_alpha0','training_allowed':False},'vicuna':{'fit12_source':'fixed_Llama_cache','keep60_source':'must_generate_native_Vicuna_alpha0','training_allowed':False}},'all_native_donor_fit_outputs_excluded':True,'old_native_gate_not_a_training_condition':True,'old_private_pack_unchanged_sha256':sha(prior)}
 save(C/'U1_active_execution_binding.json',bindings)
 doc=R/'docs/287_U1_TOKENIZATION_AND_EXECUTION_CHECK.md';assert not doc.exists()
 lines=[]
 for key,v in results.items():
  z=v['target_lengths'];lines.append(f"|{key}|12|{z['min']} / {z['median']} / {z['max']}|{v['target_unk_count']}|{v['target_special_control_count']}|{v['strict_roundtrip']}/12|{v['whitespace_normalized_roundtrip']}/12|{v['canonical_complete_chat_prefix_matches']}/12|")
 doc.write_text(f'''# U1 tokenization and execution binding

CPU checkUTC {now}, after addendum5 and before vector training. No model weights loaded and no generation performed. All3 models use the same ordered12 target-text hashes; only their native tokenizer and prompt template differ.

|Model|Targets|Target tokens min / median / max|UNK|Control tokens|Exact decode roundtrip|Whitespace-normalized roundtrip|Canonical full-chat prefix matches|
|---|---:|---|---:|---:|---|---|---|
{chr(10).join(lines)}

The implemented training construction is the historical recipe: rendered native user prompt with assistant-generation prefix, then separately encoded target text with add_special_tokens=False. All36 label masks cover target tokens only and preserve the prefix. No BOS/EOS or role token is inserted inside the target. Full-chat tokenization is a separate boundary diagnostic, not an instruction to alter this frozen sequence. Any whitespace-normalization difference is reported rather than repaired by changing target text.

Qwen alpha0 has2 v2-positive refusals out of12. Against the corresponding two U1 targets, exact text matches are{compare['exact_same_text_n']}/2; native target token lengths={compare['native_refusal_lengths']}; same-ID U1 lengths={compare['same_ID_U1_lengths']}. The36-row CSV records per-item hashes and codes, not output text. Two examples describe wording differences and do not establish a general style effect or classifier accuracy.

The old Qwen conditional pack is unchanged. A new private U1 pack rebinds its12 fixed Llama targets and60 native Qwen keep targets to the new effective protocol. Neither native fit12 alpha0 replies nor native donor targets enter the attack-target loss. Gemma and Vicuna must supply their own keep60 continuations; none are silently copied from Llama. `U1_active_execution_binding.json` is the effective execution binding, and all3 training_allowed flags remain false pending independent refusal admission. Historical gate failures and old manifests remain in place.

Tokenization JSON SHA256 `{sha(out)}`. RowsCSV SHA256 `{sha(csvfile)}`. Active bindingSHA256 `{sha(C/'U1_active_execution_binding.json')}`. No raw prompts or targets are included.
''')
 for name in ['PREREG_LOG.txt','OPS_LOG.txt']:
  with(R/'docs'/name).open('a')as f:f.write(f'{now} CROSSMODEL287_U1_TOKENIZATION targets=12x3 CPU_only; JSON_SHA={sha(out)} rows_SHA={sha(csvfile)} active_binding_SHA={sha(C/"U1_active_execution_binding.json")} report_SHA={sha(doc)}; all_new_model_training_still_locked; historical_and_native_fit_targets_not_reused.\n')
 print(json.dumps({'utc':now,'tokenization_sha256':sha(out),'rows_sha256':sha(csvfile),'report_sha256':sha(doc),'active_binding_sha256':sha(C/'U1_active_execution_binding.json'),'Qwen_wording':compare}))
if __name__=='__main__':main()
