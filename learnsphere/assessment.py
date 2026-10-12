import re, uuid
from .models import Question
from .retrieval import search
from .learner import record
def validate(q):
    if not q.id or not q.text or not q.source_chunk_ids or not q.explanation:return False,'missing required fields'
    if q.question_type=='mcq' and (len(q.options)<2 or q.options.count(q.answer)!=1): return False,'MCQ must have one answer in options'
    if q.question_type=='numeric' and (not isinstance(q.answer,(int,float)) or q.tolerance is None): return False,'numeric answer/tolerance required'
    return True,'ok'
def generate(chunks,topic,count=5,difficulty='mixed',store=None):
    output=[]
    for c in search(chunks,topic,count*3):
        s=next((x.strip() for x in re.split(r'[.!?]',c.text) if len(x.split())>=6),None)
        if not s: continue
        terms=[x for x in re.findall(r'\b[A-Za-z]{5,}\b',s) if x.lower() not in {'which','their','these','about','where'}]
        if not terms: continue
        key=terms[0]; q=Question(str(uuid.uuid4()),f"Complete the source statement: {s.replace(key,'_____',1)}",'short_answer',topic,[key.lower()],difficulty,[c.id],key,f"The source states: {s}",rubric='Deterministic keyword rubric; it does not assess paraphrase quality.')
        ok,_=validate(q)
        if ok and (not store or not store.served(q.fingerprint())):
            output.append(q)
            if store:store.serve(q)
        if len(output)>=count:break
    return output
def grade(q,response):
    if q.question_type=='numeric':
        try:return abs(float(response)-float(q.answer))<=q.tolerance,'numeric tolerance comparison'
        except ValueError:return False,'not numeric'
    if q.question_type=='mcq':return response.strip()==q.answer,'exact option match'
    return str(q.answer).lower() in response.lower(),'deterministic keyword rubric; semantic grading unavailable'
def submit(store,questions,responses):
    details=[]
    for q,r in zip(questions,responses):
        correct,rationale=grade(q,r); states=[record(store,c,correct) for c in q.concepts]
        details.append({'id':q.id,'correct':correct,'rationale':rationale,'explanation':q.explanation,'sources':q.source_chunk_ids,'concepts':q.concepts,'mastery':[s['mastery'] for s in states]})
    return (100*sum(x['correct'] for x in details)/len(details) if details else 0),details
