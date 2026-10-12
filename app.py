import os
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from learnsphere.db import Store
from learnsphere.ingestion import ingest_upload
from learnsphere.grounding import answer_tuple as answer
from learnsphere.quiz import questions
load_dotenv()
st.set_page_config(page_title='LearnSphere AI',page_icon='◉',layout='wide')
st.markdown('''<style>.stApp{background:#fafbff}.hero{padding:1.4rem 0}.card{background:white;border:1px solid #e7e9f4;border-radius:14px;padding:1rem;box-shadow:0 3px 15px #1118270b}.tag{color:#4f46e5;font-weight:700;font-size:.8rem}</style>''',unsafe_allow_html=True)
db=Store(); name=db.get('name','Learner'); chunks=db.chunks()
with st.sidebar:
 st.markdown('## ◉ LearnSphere AI\n*Every lesson understood.*')
 page=st.radio('Navigate',['Overview','My Materials','AI Tutor','Adaptive Quiz','Learning Analytics','Revision Plan','Settings'])
 st.caption(f'{db.material_count()} materials · {len(chunks)} indexed passages')
if page=='Overview':
 st.markdown(f'<div class="hero"><div class="tag">PERSONAL LEARNING SPACE</div><h1>Welcome back, {name}.</h1><p>Turn every lecture, slide, and note into a study path you can trust.</p></div>',unsafe_allow_html=True)
 if not chunks:
  st.info('Start your learning space by uploading a textbook, slides, or transcript. No statistics are shown until you have real activity.')
  if st.button('Add study material',type='primary'): st.switch_page('app.py')
 else:
  a,b,c=st.columns(3); a.metric('Study topic',db.get('topic','Your materials')); b.metric('Uploaded materials',db.material_count()); c.metric('Searchable passages',len(chunks))
  left,right=st.columns([1.3,1]); left.markdown('<div class="card"><h3>Topic mastery</h3><p>Mastery appears after an assessment.</p></div>',unsafe_allow_html=True)
  assessments=db.assessments()
  if assessments: right.metric('Latest assessment',f"{assessments[0]['score']:.0f}%");
  else: right.info('Take a short adaptive quiz to establish your baseline.')
  st.button('Continue studying',type='primary')
elif page=='My Materials':
 st.header('My Materials'); st.caption('PDF, PPTX, DOCX, TXT, VTT, and SRT are indexed locally. Video needs FFmpeg + transcription configuration; upload a transcript for the offline demo.')
 uploads=st.file_uploader('Add learning materials',type=['pdf','pptx','docx','txt','vtt','srt','mp4','mov','mkv','webm'],accept_multiple_files=True)
 if uploads and st.button('Index materials',type='primary'):
  for up in uploads:
   try:
    with st.spinner(f'Extracting {up.name}…'): added=db.add_chunks(ingest_upload(up))
    st.success(f'{up.name}: {added} new passages indexed.')
   except Exception as e: st.error(f'{up.name}: {e}')
 if chunks: st.dataframe([{'source':c.document_name,'type':c.content_type,'location':c.citation(),'preview':c.text[:110]} for c in chunks],use_container_width=True)
elif page=='AI Tutor':
 st.header('AI Tutor'); st.caption('Answers are grounded in your uploaded materials and include source locations.')
 q=st.text_area('What would you like to understand?',placeholder='Explain the central idea in simple terms…')
 if st.button('Ask LearnSphere',type='primary',disabled=not q):
  reply,sources,mode=answer(q,chunks); st.caption(f'Mode: {mode}'); st.markdown(reply)
  if sources: st.markdown('**Sources**'); [st.markdown(f'- `{i+1}` {s.citation()}') for i,s in enumerate(sources)]
elif page=='Adaptive Quiz':
 st.header('Adaptive Quiz'); topic=st.text_input('Focus topic',value=db.get('topic',''))
 if st.button('Create source-based quiz',type='primary'):
  st.session_state.quiz=questions(chunks,topic); st.session_state.topic=topic
 quiz=st.session_state.get('quiz',[])
 if quiz:
  with st.form('quiz'):
   answers=[st.text_input(x['prompt'],key=f'a{i}') for i,x in enumerate(quiz)]
   submitted=st.form_submit_button('Submit answers')
  if submitted:
   correct=sum(x['answer'].lower() in a.lower() for x,a in zip(quiz,answers)); score=100*correct/len(quiz); db.save_assessment(st.session_state.topic,score,len(quiz)); db.set('topic',st.session_state.topic); st.success(f'{correct}/{len(quiz)} correct ({score:.0f}%). Review the cited passages below.'); [st.caption(x['citation']) for x in quiz]
elif page=='Learning Analytics':
 st.header('Learning Analytics'); rows=db.assessments()
 if not rows: st.info('Complete an assessment to see your real performance trend.')
 else: st.plotly_chart(px.line(rows,x='created_at',y='score',markers=True,title='Assessment results'),use_container_width=True); st.dataframe(rows,use_container_width=True)
elif page=='Revision Plan':
 st.header('Revision Plan'); rows=db.assessments()
 if not chunks: st.info('Upload material first. Your revision plan will be built from it.')
 elif not rows: st.write('1. Ask the tutor about your current topic.\n2. Take a baseline adaptive quiz.\n3. Revisit every missed citation before retesting.')
 else:
  latest=rows[0]; action='Revisit the source excerpts and retry a focused quiz.' if latest['score']<75 else 'Build retention with a new quiz tomorrow.'; st.success(f'Recommended next action: {action}')
elif page=='Settings':
 st.header('Settings'); new_name=st.text_input('Display name',value=name); st.text_input('Configured model',value=os.getenv('OPENAI_MODEL','Not configured'),disabled=True)
 st.caption('Add secrets locally in `.env` from `.env.example`. The app labels deterministic fallback responses and never presents them as LLM output.')
 if st.button('Save profile'): db.set('name',new_name); st.success('Profile saved.')
