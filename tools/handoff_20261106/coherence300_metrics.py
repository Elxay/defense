"""Frozen descriptive coherence metrics. No main-output aggregation in this module."""
import unicodedata,re,importlib.metadata
from langdetect import detect,DetectorFactory
SEED=20261111
assert importlib.metadata.version('langdetect')=='1.0.9'
def metrics(text):
 DetectorFactory.seed=SEED
 text=unicodedata.normalize('NFC',text);empty=not text.strip();normalized=' '.join(text.split());tokens=normalized.casefold().split()
 def repeat(seq,n=4):
  grams=[tuple(seq[i:i+n])for i in range(max(0,len(seq)-n+1))]
  return None if not grams else (len(grams)-len(set(grams)))/len(grams)
 chars=[c for c in text if not c.isspace()]
 bad=sum(unicodedata.category(c)[0]in 'SC'for c in chars)
 try:language=detect(text);failed=False
 except Exception:language=None;failed=True
 return dict(empty=empty,word4_repeated_occurrence_fraction=repeat(tokens),character4_repeated_occurrence_fraction=repeat(normalized),nonlanguage_character_fraction=None if not chars else bad/len(chars),language=language,language_identification_failed=failed,nonempty_language_identification_failed=failed and not empty)
if __name__=='__main__':
 assert metrics('   ')['empty'];assert metrics('😀😀😀😀')['nonlanguage_character_fraction']==1
 assert metrics('red blue red blue red blue red blue')['word4_repeated_occurrence_fraction']>0
 assert not metrics('This is a harmless English sentence about the weather.')['language_identification_failed']
 print('harmless fixtures passed; no model output read')
