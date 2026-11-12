"""Versioned raw-reply script guard plus frozen langdetect routing."""
import hashlib,json,torch
from language300_local_translation import detect_reply_language,digest
RANGES={'CJK':[(0x3400,0x4DBF),(0x4E00,0x9FFF),(0xF900,0xFAFF)],'Hangul':[(0x1100,0x11FF),(0x3130,0x318F),(0xAC00,0xD7AF)],'Tamil':[(0x0B80,0x0BFF)],'Malayalam':[(0x0D00,0x0D7F)],'Devanagari':[(0x0900,0x097F)]}
def script_counts(text):return {k:sum(any(a<=ord(c)<=b for a,b in ranges) for c in text) for k,ranges in RANGES.items()}
def route_reply(text,seed=20261267,detected=None):
 original=detect_reply_language(text,seed) if detected is None else detected;counts=script_counts(text);has_script=any(counts.values());empty=not text.strip()
 return dict(original_language=original,script_counts=counts,script_forced_non_English=has_script,empty=empty,route='empty_passthrough' if empty else 'english_passthrough' if original['language']=='en' and not has_script else 'local_translate',english_subset=not empty and original['language']=='en' and not has_script)
def preprocess_reply(text,model,tokenizer,plan):
 routed=route_reply(text,plan['language_seed']);result=dict(raw_response_sha256=digest(text),**routed,translation_attempted=False,translation_human_validated=False)
 if routed['route'] in ['english_passthrough','empty_passthrough']:
  result.update(status=routed['route'],processed_response=text,processed_response_sha256=digest(text),primary_INVALID=False);return result
 result['translation_attempted']=True;torch.manual_seed(plan['translation_seed']);messages=[{'role':'system','content':plan['system_text']},{'role':'user','content':text}]
 ids=tokenizer.apply_chat_template(messages,add_generation_prompt=True,return_tensors='pt',enable_thinking=False).to(next(model.parameters()).device);length=ids.shape[1];result['translator_input_tokens']=length
 if length+plan['max_new_tokens']>model.config.max_position_embeddings:
  result.update(status='translator_context_overflow',processed_response=None,primary_INVALID=True);return result
 with torch.inference_mode():out=model.generate(input_ids=ids,attention_mask=torch.ones_like(ids),max_new_tokens=plan['max_new_tokens'],do_sample=False,pad_token_id=tokenizer.eos_token_id)
 new=out[0,length:];translated=tokenizer.decode(new,skip_special_tokens=True);eos=model.generation_config.eos_token_id;eos={eos} if isinstance(eos,int) else set(eos or []);finished=bool(len(new) and int(new[-1]) in eos)
 output_language=detect_reply_language(translated,plan['language_seed']);truncated=len(new)>=plan['max_new_tokens'] and not finished
 status='translation_truncated' if truncated else 'translation_empty' if not translated.strip() else 'translation_not_identified_English' if output_language['language']!='en' else 'translated'
 result.update(status=status,translated_response=translated,translated_response_sha256=digest(translated),translator_output_language=output_language,translator_new_tokens=len(new),translator_eos=finished,primary_INVALID=status!='translated',processed_response=translated if status=='translated' else None,processed_response_sha256=digest(translated) if status=='translated' else None)
 return result
