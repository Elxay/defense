"""Versioned response-language routing; outputs stay private; no judge-driven choice."""
import hashlib,json,torch
from langdetect import DetectorFactory,detect_langs

def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def detect_reply_language(text,seed=20261267):
 DetectorFactory.seed=seed
 if not text.strip():return dict(language=None,probability=None,error='empty')
 try:
  result=detect_langs(text)[0];return dict(language=result.lang,probability=float(result.prob),error=None)
 except Exception as e:return dict(language=None,probability=None,error=type(e).__name__)

def preprocess_reply(text,model,tokenizer,plan):
 original=detect_reply_language(text,plan['language_seed']);result=dict(raw_response_sha256=digest(text),original_language=original,english_subset=original['language']=='en',translation_attempted=False,translation_human_validated=False)
 if original['language']=='en' or not text.strip():
  result.update(status='english_passthrough'if text.strip()else'empty_passthrough',processed_response=text,processed_response_sha256=digest(text),primary_INVALID=False);return result
 result['translation_attempted']=True;torch.manual_seed(plan['translation_seed'])
 messages=[{'role':'system','content':plan['system_text']},{'role':'user','content':text}]
 ids=tokenizer.apply_chat_template(messages,add_generation_prompt=True,return_tensors='pt',enable_thinking=False).to(next(model.parameters()).device);length=ids.shape[1];result['translator_input_tokens']=length
 if length+plan['max_new_tokens']>model.config.max_position_embeddings:
  result.update(status='translator_context_overflow',processed_response=None,primary_INVALID=True);return result
 with torch.inference_mode():out=model.generate(input_ids=ids,attention_mask=torch.ones_like(ids),max_new_tokens=plan['max_new_tokens'],do_sample=False,pad_token_id=tokenizer.eos_token_id)
 new=out[0,length:];translated=tokenizer.decode(new,skip_special_tokens=True);eos=model.generation_config.eos_token_id;eos={eos}if isinstance(eos,int)else set(eos or[]);finished=bool(len(new)and int(new[-1])in eos);output_language=detect_reply_language(translated,plan['language_seed']);truncated=len(new)>=plan['max_new_tokens']and not finished
 status='translation_truncated'if truncated else'translation_empty'if not translated.strip()else'translation_not_identified_English'if output_language['language']!='en'else'translated'
 result.update(status=status,translated_response=translated,translated_response_sha256=digest(translated),translator_output_language=output_language,translator_new_tokens=len(new),translator_eos=finished,primary_INVALID=status!='translated',processed_response=translated if status=='translated'else None,processed_response_sha256=digest(translated)if status=='translated'else None)
 return result
