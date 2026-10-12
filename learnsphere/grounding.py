from .retrieval import search
def grounded_answer(question,chunks):
    sources=search(chunks,question)
    if not sources:return {'answer':'I cannot establish an answer from the uploaded materials. This question is unsupported.','sources':[],'mode':'abstained','supported':False}
    excerpt=' '.join(c.text for c in sources[:2])[:900]
    return {'answer':f'**Deterministic extractive study aid — not an LLM response.** The relevant uploaded material says: {excerpt}','sources':sources,'mode':'offline deterministic extraction','supported':True}
def answer_tuple(question,chunks):
    result=grounded_answer(question,chunks)
    return result['answer'],result['sources'],result['mode']
def resolve_citations(store,ids): return [store.get_chunk(i) for i in ids if store.get_chunk(i)]
