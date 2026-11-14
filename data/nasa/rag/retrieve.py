"""Offline lexical retrieval baseline. No API key or third-party packages required."""
import json,re,sys,math,pathlib,collections
ROOT=pathlib.Path(__file__).resolve().parent
ALIASES={'حرارة':'temperature','بتسخن':'temperature','سخونة':'temperature','warming':'temperature','التربة':'soil moisture','تربة':'soil moisture','جفاف':'soil moisture','الدلتا':'','القاهرة':''}
def tokens(text):
 text=text.lower()
 for key,value in ALIASES.items():
  if key in text:text+=' '+value
 return re.findall(r'[a-z0-9_]+',text)
def retrieve(query,k=3):
 docs=[json.loads(x) for x in (ROOT/'corpus.jsonl').read_text(encoding='utf-8').splitlines()]
 counts=[collections.Counter(tokens(d['title']+' '+d['text'])) for d in docs]
 terms=set(tokens(query)); n=len(docs); avg=sum(sum(c.values()) for c in counts)/max(n,1)
 scores=[]
 for d,c in zip(docs,counts):
  score=0
  for t in terms:
   df=sum(t in other for other in counts); tf=c[t]
   if tf:score+=math.log(1+(n-df+.5)/(df+.5))*tf*2.5/(tf+1.5*(.25+.75*sum(c.values())/avg))
  if score>0:scores.append(dict(d,score=round(score,4)))
 return sorted(scores,key=lambda x:x['score'],reverse=True)[:k]
if __name__=='__main__':
 query=' '.join(sys.argv[1:]) or 'soil moisture'
 print(json.dumps({'query':query,'mode':'retrieval_only_not_generated_answer','results':retrieve(query)},ensure_ascii=False,indent=2))
