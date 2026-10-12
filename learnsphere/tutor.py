import os
from .retrieval import search
def answer(question,chunks):
    sources=search(chunks,question)
    if not sources: return 'I can’t answer from your materials yet. Upload a source first.',[], 'offline'
    context='\n\n'.join(f'[{i+1}] {c.text}' for i,c in enumerate(sources)); key=os.getenv('OPENAI_API_KEY')
    if key:
        try:
            from openai import OpenAI
            client=OpenAI(api_key=key,base_url=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1')); prompt=f'Answer only from supplied excerpts. Cite claims as [1], [2]. If insufficient, say so.\n\n{context}\n\nQuestion: {question}'
            r=client.chat.completions.create(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),messages=[{'role':'user','content':prompt}],temperature=.2); return r.choices[0].message.content,sources,'llm'
        except Exception as e: mode=f'offline (provider unavailable: {type(e).__name__})'
    else: mode='offline deterministic demo'
    return f'**Deterministic study aid — not an LLM response.** Based on relevant course excerpts: {" ".join(c.text for c in sources[:2])[:900]}',sources,mode
