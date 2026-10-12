import re
from .retrieval import search
def questions(chunks,topic,count=4):
    result=[]
    for c in search(chunks,topic,count):
        sentence=next((s.strip() for s in re.split(r'[.!?]',c.text) if len(s.split())>7),c.text[:180]); words=[w for w in re.findall(r'\b[A-Za-z]{5,}\b',sentence) if w.lower() not in {'which','their','these','about'}]
        if words: result.append({'prompt':f'Complete the statement: {sentence.replace(words[0],"_____",1)}','answer':words[0],'citation':c.citation()})
    return result
