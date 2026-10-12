import math,re
from collections import Counter
STOP={'what','is','the','a','an','of','in','to','for','and','do','does','how','who','where','when','my','this','that','current','write'}
def tokens(text): return [x for x in re.findall(r"[a-zA-Z0-9']+",text.lower()) if x not in STOP]
def search(chunks,query,limit=5):
    q=Counter(tokens(query)); results=[]
    for c in chunks:
        d=Counter(tokens(c.text)); dot=sum(q[k]*d[k] for k in q); denom=math.sqrt(sum(x*x for x in q.values())*sum(x*x for x in d.values()))
        if dot: results.append((dot/denom,c))
    return [c for _,c in sorted(results,key=lambda x:x[0],reverse=True)[:limit]]
