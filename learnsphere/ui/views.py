"""LearnSphere AI screens. Each view reads real data from the Store and calls the existing services."""
import os
from datetime import datetime, timezone
from html import escape

import plotly.graph_objects as go
import streamlit as st

from .. import tutor
from ..assessment import generate, submit
from ..grounding import grounded_answer
from ..ingestion import ingest_upload
from ..learner import DEFAULT as BKT
from ..retrieval import search
from . import data
from .theme import avatar, badge, badges, empty_state, page_header, progress_bar

PAGES = [  # key, label, material icon
    ('overview', 'Overview', ':material/space_dashboard:'),
    ('materials', 'My Materials', ':material/folder_open:'),
    ('tutor', 'AI Tutor', ':material/forum:'),
    ('quiz', 'Adaptive Quiz', ':material/quiz:'),
    ('analytics', 'Learning Analytics', ':material/monitoring:'),
    ('revision', 'Revision Plan', ':material/event_repeat:'),
    ('settings', 'Settings', ':material/settings:'),
]
UPLOAD_TYPES = ['pdf', 'pptx', 'docx', 'txt', 'vtt', 'srt', 'mp4', 'mov', 'mkv', 'webm']


# ---------- navigation helpers ----------
def go_to(page, **state):
    """Button callback: switch page and optionally seed session state before the next run."""
    st.session_state.page = page
    for k, v in state.items():
        st.session_state[k] = v


def nav_button(label, page, key, primary=False, icon=None, **state):
    st.button(label, key=key, type='primary' if primary else 'secondary', icon=icon, on_click=go_to, args=(page,), kwargs=state)


def doc_options(chunks):
    docs = data.materials(chunks)
    return docs, {d['id']: f"{d['name']} ({d['label']})" for d in docs}


def friendly_error(name, err):
    msg = str(err)
    if 'scanned' in msg.lower() or 'OCR' in msg:
        return 'This PDF has no selectable text (it looks scanned).', 'Run OCR on it first, or export a text-based PDF, then upload again.'
    if 'Video' in msg:
        return 'Video files need FFmpeg and a transcription service, which are not configured.', 'Upload the lecture’s transcript (.vtt, .srt or .txt) instead.'
    if 'Unsupported' in msg:
        return 'This file type is not supported.', 'Use PDF, PPTX, DOCX, TXT, VTT or SRT.'
    return f'We could not read this file ({type(err).__name__}).', 'It may be corrupted or password-protected. Re-export it and try again.'


# ---------- sidebar ----------
def sidebar(db, chunks):
    with st.sidebar:
        st.markdown('<div class="ls-brand"><span class="ls-dot">◉</span> LearnSphere AI</div><div class="ls-note">Every lesson understood.</div>', unsafe_allow_html=True)
        st.write('')
        for key, label, icon in PAGES[:-1]:
            nav_button(label, key, f'nav_{key}', primary=st.session_state.page == key, icon=icon)
        st.divider()
        name = db.get('name', 'Learner')
        st.markdown(f'{avatar(name)} &nbsp; **{escape(name)}**', unsafe_allow_html=True)
        st.caption(f'{db.material_count()} materials · {len(chunks)} indexed passages')
        nav_button('Settings', 'settings', 'nav_settings', primary=st.session_state.page == 'settings', icon=':material/settings:')


# ---------- overview ----------
def overview(db, chunks):
    name = db.get('name', 'Learner')
    page_header(f'Welcome back, {name}', 'Turn lectures, slides and notes into a study path you can trust.', 'Personal learning space')
    act = data.next_action(db, chunks)
    with st.container():
        st.markdown(f'<div class="ls-hero"><div class="ls-eyebrow">Next best step</div><h3>{escape(act["title"])}</h3><p>{escape(act["why"])}</p></div>', unsafe_allow_html=True)
        a, b, _ = st.columns([1.2, 1.2, 3])
        with a:
            nav_button(act['label'], act['page'], 'ov_primary', primary=True, **act['payload'])
        with b:
            if chunks:
                nav_button('Ask the tutor', 'tutor', 'ov_tutor', icon=':material/forum:')
            else:
                nav_button('Open materials', 'materials', 'ov_mat', icon=':material/folder_open:')
    st.write('')
    if not chunks:
        empty_state('Nothing to show yet', 'No statistics appear until you have real activity. Add a textbook chapter, slide deck or transcript to begin.')
        return
    quizzes, states = data.assessments(db), data.concept_states(db)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Materials', db.material_count())
    c2.metric('Quizzes taken', len(quizzes))
    c3.metric('Latest score', f"{quizzes[0]['score']:.0f}%" if quizzes else '—')
    c4.metric('Concepts tracked', len(states))
    left, right = st.columns([1.4, 1])
    with left:
        with st.container(border=True):
            st.markdown('**Needs attention**')
            weak = [s for s in states if s['mastery'] < data.WEAK_BELOW][:4]
            if not states:
                st.markdown('<span class="ls-note">Mastery estimates appear after your first quiz.</span>', unsafe_allow_html=True)
            elif not weak:
                st.markdown('<span class="ls-note">No concept is below the attention threshold right now.</span>', unsafe_allow_html=True)
            for s in weak:
                label = '{:.0%} est. mastery'.format(s['mastery'])
                st.markdown(f"{escape(s['concept'])} &nbsp; {badge(label, 'warn')}", unsafe_allow_html=True)
                progress_bar(s['mastery'], 'warn')
            if weak:
                nav_button('Open revision plan', 'revision', 'ov_rev')
            st.caption('Mastery is a heuristic estimate (Bayesian Knowledge Tracing), not a validated score.')
    with right:
        with st.container(border=True):
            st.markdown('**Recent activity**')
            if not quizzes:
                st.markdown('<span class="ls-note">No quizzes yet.</span>', unsafe_allow_html=True)
            for q in quizzes[:3]:
                st.markdown(f"{escape(q['topic'])} — **{q['score']:.0f}%** <span class='ls-note'>· {data.pretty_time(q['created_at'])}</span>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('**Recently added materials**')
            for d in list(reversed(data.materials(chunks)))[:3]:
                st.markdown(f"{escape(d['name'])} &nbsp; {badge(d['label'])}", unsafe_allow_html=True)


# ---------- materials ----------
def materials(db, chunks):
    page_header('My Materials', 'Upload what you are studying. Everything is indexed on this machine with page, slide or timestamp references.', 'Library')
    ss = st.session_state
    with st.container(border=True):
        uploads = st.file_uploader('Add learning materials', type=UPLOAD_TYPES, accept_multiple_files=True, key=f'uploader_{ss.up_key}',
                                   help='PDF, PPTX, DOCX, TXT, VTT and SRT are indexed locally.')
        st.caption('Supported: PDF · PPTX · DOCX · TXT · VTT · SRT. Video needs FFmpeg + a transcription service; upload its transcript instead. Scanned PDFs need OCR first.')
        if uploads and st.button('Index materials', type='primary', icon=':material/upload:'):
            report, bar = [], st.progress(0.0, text='Starting…')
            for i, up in enumerate(uploads):
                bar.progress(i / len(uploads), text=f'Extracting {up.name}…')
                try:
                    added = db.add_chunks(ingest_upload(up))
                    report.append({'name': up.name, 'ok': True, 'added': added})
                except Exception as e:  # shown in plain language, never swallowed silently
                    what, fix = friendly_error(up.name, e)
                    report.append({'name': up.name, 'ok': False, 'what': what, 'fix': fix})
            bar.progress(1.0, text='Done')
            ss.upload_report = report
            ss.up_key += 1
            st.rerun()
    for r in ss.get('upload_report', []):
        if r['ok'] and r['added']:
            st.success(f"{r['name']}: indexed {r['added']} new passage(s).")
        elif r['ok']:
            st.info(f"{r['name']}: already indexed, so nothing new was added.")
        else:
            with st.container(border=True):
                st.markdown(f"**{escape(r['name'])}** &nbsp; {badge('Failed', 'bad')}", unsafe_allow_html=True)
                st.markdown(f"{r['what']}  \n**What to do:** {r['fix']}")
    if ss.get('upload_report') and st.button('Dismiss messages'):
        ss.upload_report = []
        st.rerun()

    docs = data.materials(chunks)
    st.write('')
    if not docs:
        empty_state('Your library is empty', 'Upload a file above to build your searchable study index.')
        return
    f1, f2 = st.columns([2, 1])
    query = f1.text_input('Search your library', placeholder='Search by file name or passage text', label_visibility='collapsed')
    kind = f2.selectbox('File type', ['All types'] + sorted({d['label'] for d in docs}), label_visibility='collapsed')
    shown = [d for d in docs if (kind == 'All types' or d['label'] == kind)
             and (not query or query.lower() in d['name'].lower() or any(query.lower() in c.text.lower() for c in chunks if c.document_id == d['id']))]
    st.caption(f'{len(shown)} of {len(docs)} materials')
    if not shown:
        empty_state('No matches', 'Try a different search term or clear the type filter.')
    for d in shown:
        with st.container(border=True):
            top, acts = st.columns([3, 2])
            with top:
                st.markdown(f"**{escape(d['name'])}**", unsafe_allow_html=True)
                badges((d['label'], ''), ('Indexed', 'good'), (d['extent'], 'neutral'), (f"{d['passages']} passages", 'neutral'))
            with acts:
                x, y = st.columns(2)
                with x:
                    nav_button('Ask tutor', 'tutor', f"ask_{d['id']}", icon=':material/forum:', tutor_doc=d['id'])
                with y:
                    nav_button('Quiz me', 'quiz', f"quiz_{d['id']}", icon=':material/quiz:', quiz_doc=d['id'])
            with st.expander('Inspect passages and source references'):
                own = [c for c in chunks if c.document_id == d['id']]
                for c in own[:25]:
                    st.markdown(f"**{escape(data.cite(c))}**", unsafe_allow_html=True)
                    st.caption(c.text[:420] + ('…' if len(c.text) > 420 else ''))
                if len(own) > 25:
                    st.caption(f'Showing 25 of {len(own)} passages.')


# ---------- tutor ----------
def get_answer(question, chunks):
    """Existing grounding decides support/abstention; the optional LLM path is used only when a key is configured."""
    g = grounded_answer(question, chunks)
    if not g['supported'] or not os.getenv('OPENAI_API_KEY'):
        return g
    text, sources, mode = tutor.answer(question, chunks)
    return {'answer': text, 'sources': sources, 'mode': mode, 'supported': True}


def mode_badge(msg):
    if msg.get('error'):
        return ('Something went wrong', 'bad'), ''
    if not msg['supported']:
        return ('Not found in your materials', 'warn'), 'The tutor will not guess. Try rephrasing, widen the scope, or add material that covers this.'
    if msg['mode'] == 'llm':
        return ('AI answer from retrieved passages', ''), 'Written by a language model using only the passages below. Claims are not automatically verified, so check the sources.'
    if msg['mode'].startswith('offline (provider'):
        return ('Model unavailable: showing excerpts', 'warn'), 'The configured AI provider did not respond, so this is a plain excerpt from your materials.'
    return ('Excerpts from your materials · no AI model', 'neutral'), 'No AI model key is configured, so this shows the most relevant passages rather than a written explanation.'


def render_message(db, m, idx, last):
    with st.chat_message(m['role']):
        if m['role'] == 'user':
            st.markdown(m['content'])
            return
        (label, tone), note = mode_badge(m)
        badges((label, tone))
        if m.get('error'):
            st.error(m['content'])
        else:
            st.markdown(m['content'])
        if note:
            st.caption(note)
        srcs = [c for c in (db.get_chunk(i) for i in m.get('sources', [])) if c]
        if srcs:
            st.markdown('**Sources**')
            for n, c in enumerate(srcs, 1):
                with st.expander(f'[{n}] {data.cite(c)}'):
                    st.markdown(c.text)
                    st.caption('Retrieved passage from your uploaded file.')
        if last:
            a, b, _ = st.columns([1, 1.3, 4])
            with a:
                with st.popover('Copy', icon=':material/content_copy:'):
                    st.code(m['content'], language=None, wrap_lines=True)
            with b:
                st.button('Regenerate', key=f'regen_{idx}', icon=':material/refresh:', on_click=lambda q=m['question']: (
                    st.session_state.chat.pop(), st.session_state.__setitem__('pending_prompt', q)))


def tutor_view(db, chunks):
    page_header('AI Tutor', 'Ask anything about your materials. Answers cite the exact page, slide or timestamp they came from.', 'Tutor')
    ss = st.session_state
    if not chunks:
        empty_state('Add a material first', 'The tutor answers only from your own uploads, so it needs something to read.')
        nav_button('Go to My Materials', 'materials', 'tutor_to_mat', primary=True)
        return
    docs, labels = doc_options(chunks)
    ids = [''] + [d['id'] for d in docs]
    if ss.get('tutor_doc', '') not in ids:
        ss.tutor_doc = ''
    st.selectbox('Scope', ids, format_func=lambda i: 'All materials' if not i else labels[i], key='tutor_doc')
    pool = data.scoped(chunks, ss.tutor_doc)

    prompt = st.chat_input('Ask about your materials…') or ss.pop('pending_prompt', None)
    if prompt:
        ss.chat.append({'role': 'user', 'content': prompt})
        db.set('last_tutor_question', prompt)
        try:
            with st.spinner('Searching your materials…'):
                g = get_answer(prompt, pool)
            ss.chat.append({'role': 'assistant', 'content': g['answer'], 'sources': [c.id for c in g['sources']],
                            'mode': g['mode'], 'supported': g['supported'], 'question': prompt})
        except Exception as e:
            ss.chat.append({'role': 'assistant', 'content': f'The tutor hit an error ({type(e).__name__}). Your question was not lost.',
                            'sources': [], 'mode': 'error', 'supported': False, 'error': True, 'question': prompt})
    if not ss.chat:
        with st.container(border=True):
            st.markdown('**What would you like to understand?**')
            st.markdown('<span class="ls-note">Try one of these, or type your own question below.</span>', unsafe_allow_html=True)
            for i, p in enumerate(data.suggested_prompts(chunks, ss.tutor_doc)):
                st.button(p, key=f'sugg_{i}', on_click=lambda p=p: ss.__setitem__('pending_prompt', p))
        return
    last = len(ss.chat) - 1
    for i, m in enumerate(ss.chat):
        render_message(db, m, i, last=(i == last and m['role'] == 'assistant'))
        if m.get('error') and i == last:
            st.button('Retry', key='retry_err', type='primary', on_click=lambda q=m['question']: (ss.chat.pop(), ss.__setitem__('pending_prompt', q)))
    if st.button('Clear conversation', icon=':material/delete:'):
        ss.chat = []
        st.rerun()


# ---------- quiz ----------
def reset_quiz():
    st.session_state.quiz = None


def start_quiz(db, chunks, topic, doc_id, count):
    pool = data.scoped(chunks, doc_id)
    qs = generate(pool, topic, count=count, store=db)
    if not qs:
        return False
    st.session_state.quiz = {'questions': qs, 'topic': topic, 'doc_id': doc_id, 'answers': {}, 'i': 0, 'result': None}
    db.set('topic', topic)
    return True


def quiz_view(db, chunks):
    ss = st.session_state
    page_header('Adaptive Quiz', 'Source-based questions that update your mastery estimates.', 'Assess')
    if not chunks:
        empty_state('Add a material first', 'Quizzes are built from your own uploads.')
        nav_button('Go to My Materials', 'materials', 'quiz_to_mat', primary=True)
        return
    q = ss.quiz
    if q is None:
        quiz_setup(db, chunks)
    elif q['result'] is None:
        quiz_run(db, q)
    else:
        quiz_results(db, chunks, q)


def quiz_setup(db, chunks):
    ss = st.session_state
    docs, labels = doc_options(chunks)
    ids = [''] + [d['id'] for d in docs]
    if ss.get('quiz_doc', '') not in ids:
        ss.quiz_doc = ''
    if 'quiz_topic' not in ss:
        ss.quiz_topic = db.get('topic', '')
    with st.container(border=True):
        st.selectbox('Scope', ids, format_func=lambda i: 'All materials' if not i else labels[i], key='quiz_doc')
        st.text_input('Focus topic', key='quiz_topic', placeholder='A concept or keyword from your materials, e.g. photosynthesis')
        terms = data.key_terms(data.scoped(chunks, ss.quiz_doc), 4)
        if terms:
            st.caption('Ideas from your materials:')
            cols = st.columns(len(terms))
            for col, t in zip(cols, terms):
                col.button(t, key=f'term_{t}', on_click=lambda t=t: ss.__setitem__('quiz_topic', t), use_container_width=True)
        count = st.slider('Questions', 3, 8, 5)
        st.caption('Format: short answer · Difficulty: mixed · Never repeats a question you have already been served.')
        if st.button('Create quiz', type='primary', icon=':material/play_arrow:', disabled=not ss.quiz_topic.strip()):
            if start_quiz(db, chunks, ss.quiz_topic.strip(), ss.quiz_doc, count):
                st.rerun()
            st.warning('No new questions could be built for this topic. Questions you have already seen are not repeated, so try a broader topic or add material.')


def quiz_run(db, q):
    qs, i = q['questions'], q['i']
    cur = qs[i]
    badges((q['topic'], ''), (cur.difficulty.title(), 'neutral'), ({'short_answer': 'Short answer', 'mcq': 'Multiple choice', 'numeric': 'Numeric'}.get(cur.question_type, cur.question_type), 'neutral'))
    st.markdown(f'**Question {i + 1} of {len(qs)}**')
    progress_bar((i + 1) / len(qs))
    with st.container(border=True):
        st.markdown(f'#### {cur.text}')
        key = f'qa_{cur.id}'
        saved = q['answers'].get(cur.id, '')
        if cur.question_type == 'mcq':
            opts = list(cur.options)
            ans = st.radio('Choose one', opts, index=opts.index(saved) if saved in opts else None, key=key)
            ans = ans or ''
        elif cur.question_type == 'numeric':
            ans = st.text_input(f'Your answer{f" ({cur.unit})" if cur.unit else ""}', value=str(saved), key=key, placeholder='Enter a number')
        else:
            ans = st.text_input('Your answer', value=saved, key=key, placeholder='Type the missing word or phrase')
        q['answers'][cur.id] = ans
    unanswered = sum(1 for x in qs if not str(q['answers'].get(x.id, '')).strip())
    a, b, c, d = st.columns([1, 1, 2, 1.4])
    if a.button('Back', disabled=i == 0, icon=':material/arrow_back:'):
        q['i'] -= 1
        st.rerun()
    if i < len(qs) - 1:
        if b.button('Next', type='primary', icon=':material/arrow_forward:'):
            q['i'] += 1
            st.rerun()
    elif b.button('Submit', type='primary', icon=':material/check:'):
        responses = [q['answers'].get(x.id, '') for x in qs]
        score, details = submit(db, qs, responses)
        db.save_assessment(q['topic'], score, len(qs), report=details)
        q['result'] = {'score': score, 'details': details, 'responses': responses}
        st.rerun()
    c.caption(f'{unanswered} unanswered' if unanswered else 'All questions answered')
    with d.popover('Discard quiz'):
        st.write('Your answers will be lost.')
        st.button('Yes, discard', on_click=reset_quiz)


def quiz_results(db, chunks, q):
    res = q['result']
    qs, details = q['questions'], res['details']
    correct = sum(x['correct'] for x in details)
    badges((q['topic'], ''), ('Submitted', 'good'))
    c1, c2 = st.columns([1, 2])
    c1.metric('Score', f"{res['score']:.0f}%", f'{correct} of {len(qs)} correct', delta_color='off')
    with c2:
        with st.container(border=True):
            st.markdown('**How this was graded**')
            st.markdown('<span class="ls-note">Short answers are checked with a keyword rule, so a correct paraphrase can be marked wrong. Treat the score as a practice signal.</span>', unsafe_allow_html=True)
    st.markdown('### Review')
    for n, (cur, det, resp) in enumerate(zip(qs, details, res['responses']), 1):
        with st.expander(f"{'✓' if det['correct'] else '✗'}  Question {n}", expanded=not det['correct']):
            st.markdown(cur.text)
            st.markdown(f"Your answer: **{escape(str(resp)) or '(blank)'}** &nbsp; {badge('Correct' if det['correct'] else 'Incorrect', 'good' if det['correct'] else 'bad')}", unsafe_allow_html=True)
            if not det['correct']:
                st.markdown(f'Expected: **{cur.answer}**')
            st.markdown(det['explanation'])
            for cid in det['sources']:
                c = db.get_chunk(cid)
                if c:
                    st.caption(f'Source: {data.cite(c)}')
            st.caption('Estimated mastery of ' + ', '.join(f'“{k}” → {m:.0%}' for k, m in zip(det['concepts'], det['mastery'])))
    missed = [(k, m) for det in details if not det['correct'] for k, m in zip(det['concepts'], det['mastery'])]
    st.markdown('### Next steps')
    if missed:
        st.markdown('Concepts to revisit: ' + ', '.join(f'**{escape(k)}** ({m:.0%} est.)' for k, m in missed), unsafe_allow_html=True)
    else:
        st.markdown('Nice work. Every concept in this quiz was answered correctly.')
    a, b, c = st.columns(3)
    with a:
        if missed:
            st.button('Retry weak topics', type='primary', key='retry_weak', on_click=lambda: (reset_quiz(), st.session_state.__setitem__('quiz_topic', missed[0][0]), st.session_state.__setitem__('quiz_doc', q['doc_id'])))
        else:
            st.button('New quiz', type='primary', key='new_quiz', on_click=reset_quiz)
    with b:
        nav_button('Open revision plan', 'revision', 'res_rev')
    with c:
        if missed:
            st.button('New quiz', key='new_quiz2', on_click=reset_quiz)


# ---------- analytics ----------
INK, VIOLET, AMBER, GREEN = '#1B1B3A', '#5B4BDB', '#E39A2D', '#1F9D74'


def style_fig(fig, height=320):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(color=INK), title_font=dict(size=16), showlegend=False)
    fig.update_xaxes(gridcolor='#ECE9DD', zeroline=False)
    fig.update_yaxes(gridcolor='#ECE9DD', zeroline=False)
    return fig


def analytics(db, chunks):
    page_header('Learning Analytics', 'What your quiz results say about where you are strong and where to focus.', 'Insights')
    quizzes, states = data.assessments(db), data.concept_states(db)
    if not quizzes and not states:
        empty_state('No results yet', 'Charts appear after you complete a quiz. Nothing here is placeholder data.')
        nav_button('Take a quiz', 'quiz', 'an_quiz', primary=True)
        return
    avg = sum(q['score'] for q in quizzes) / len(quizzes) if quizzes else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Quizzes taken', len(quizzes))
    c2.metric('Latest score', f"{quizzes[0]['score']:.0f}%" if quizzes else '—')
    c3.metric('Average score', f'{avg:.0f}%' if quizzes else '—')
    c4.metric('Concepts tracked', len(states))
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            if quizzes:
                ordered = list(reversed(quizzes))
                fig = go.Figure(go.Scatter(x=list(range(1, len(ordered) + 1)), y=[q['score'] for q in ordered], mode='lines+markers',
                                           line=dict(color=VIOLET, width=3), marker=dict(size=9),
                                           customdata=[[q['topic'], data.pretty_time(q['created_at'])] for q in ordered],
                                           hovertemplate='Quiz %{x}: %{y:.0f}%<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>'))
                style_fig(fig).update_layout(title='Quiz score over time')
                fig.update_xaxes(title='Quiz number (oldest → newest)', dtick=1)
                fig.update_yaxes(title='Score (%)', range=[0, 100])
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                if len(quizzes) == 1:
                    st.caption('One quiz so far. A trend appears after your second.')
            else:
                st.markdown('**Quiz score over time**')
                st.caption('No quizzes yet.')
    with right:
        with st.container(border=True):
            if states:
                top = states[:12]
                fig = go.Figure(go.Bar(x=[s['mastery'] * 100 for s in top][::-1], y=[s['concept'] for s in top][::-1], orientation='h',
                                       marker_color=[AMBER if s['mastery'] < data.WEAK_BELOW else GREEN if s['mastery'] >= data.STRONG_FROM else VIOLET for s in top][::-1],
                                       customdata=[s['attempts'] for s in top][::-1], hovertemplate='%{y}: %{x:.0f}% est. (%{customdata} attempts)<extra></extra>'))
                style_fig(fig).update_layout(title='Estimated concept mastery (weakest first)')
                fig.update_xaxes(title='Estimated mastery (%)', range=[0, 100])
                fig.update_yaxes(title='Concept (keyword from your sources)')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.caption(f'Amber below {data.WEAK_BELOW:.0%} · violet building · green from {data.STRONG_FROM:.0%}. Showing up to 12 concepts.')
            else:
                st.markdown('**Estimated concept mastery**')
                st.caption('Appears after your first scored quiz.')
    a, b = st.columns(2)
    weak = [s for s in states if s['mastery'] < data.WEAK_BELOW]
    strong = [s for s in states if s['mastery'] >= data.STRONG_FROM]
    with a:
        st.markdown('**Needs attention**')
        st.markdown(', '.join(escape(s['concept']) for s in weak) or '<span class="ls-note">None right now.</span>', unsafe_allow_html=True)
        if weak:
            nav_button('Open revision plan', 'revision', 'an_rev')
    with b:
        st.markdown('**Going well**')
        st.markdown(', '.join(escape(s['concept']) for s in strong) or '<span class="ls-note">Nothing at this level yet.</span>', unsafe_allow_html=True)
    if quizzes:
        st.markdown('### Recent quizzes')
        st.dataframe([{'When': data.pretty_time(q['created_at']), 'Topic': q['topic'], 'Score (%)': round(q['score']), 'Questions': q['total']} for q in quizzes[:10]],
                     use_container_width=True, hide_index=True)
    with st.expander('What do these mastery numbers mean?'):
        st.markdown(f"Mastery is an **estimate**, produced by Bayesian Knowledge Tracing with fixed assumptions (starting guess {BKT['prior']:.0%}, learn rate {BKT['learn']:.0%}, slip {BKT['slip']:.0%}, guess {BKT['guess']:.0%}). "
                    'Each correct or incorrect answer nudges the estimate. It is a transparent heuristic, **not** a validated measure of what you know, and concepts are keywords taken from your own materials.')


# ---------- revision ----------
def mark_reviewed(db, concept):
    db.set(f'reviewed:{concept}', datetime.now(timezone.utc).isoformat())


def revision(db, chunks):
    page_header('Revision Plan', 'A short, ordered list of what to review next, weakest concepts first.', 'Plan')
    if not chunks:
        empty_state('Upload material first', 'Your plan is built from your own materials and quiz results.')
        nav_button('Go to My Materials', 'materials', 'rev_to_mat', primary=True)
        return
    states = data.concept_states(db)
    if not states:
        with st.container(border=True):
            st.markdown('**Start here**')
            st.markdown('1. Ask the tutor about something you are studying.  \n2. Take a baseline quiz so we can estimate where you stand.  \n3. Come back here for a prioritized plan.')
            a, b, _ = st.columns([1, 1, 3])
            with a:
                nav_button('Ask the tutor', 'tutor', 'rev_tutor', icon=':material/forum:')
            with b:
                nav_button('Take baseline quiz', 'quiz', 'rev_quiz', primary=True, icon=':material/quiz:')
        return
    todo = [s for s in states if s['mastery'] < data.STRONG_FROM]
    done = [s for s in todo if data.reviewed_after_activity(db, s['concept'], s['last_activity'])]
    st.markdown(f'**{len(done)} of {len(todo)}** concepts reviewed since your last attempt' if todo else '**Everything is on track.** Nice work.')
    if todo:
        progress_bar(len(done) / len(todo), 'good')
    st.caption('Review is self-reported: “Mark reviewed” records that you revisited the source. Your estimate only changes after you answer new questions.')
    for s in todo:
        is_done = s in done
        with st.container(border=True):
            band = data.mastery_band(s['mastery'])
            st.markdown(f"**{escape(s['concept'])}** &nbsp; {badge(band, 'warn' if band == 'needs attention' else '')} {badge('Reviewed', 'good') if is_done else ''}", unsafe_allow_html=True)
            top = search(chunks, s['concept'], 1)
            why = 'Estimated mastery is {:.0%} from {} scored attempt(s).'.format(s['mastery'], s['attempts'])
            st.markdown(f"{why}" + (f"  \nBest source to review: **{escape(data.cite(top[0]))}**" if top else ''), unsafe_allow_html=True)
            progress_bar(s['mastery'], 'warn' if s['mastery'] < data.WEAK_BELOW else '')
            a, b, c = st.columns(3)
            with a:
                nav_button('Ask the tutor', 'tutor', f"rv_ask_{s['concept']}", icon=':material/forum:', pending_prompt=f"Explain {s['concept']} using my materials", tutor_doc='')
            with b:
                nav_button('Targeted quiz', 'quiz', f"rv_quiz_{s['concept']}", icon=':material/quiz:', quiz=None, quiz_topic=s['concept'], quiz_doc='')
            with c:
                st.button('Mark reviewed', key=f"rv_done_{s['concept']}", icon=':material/check:', disabled=is_done, on_click=mark_reviewed, args=(db, s['concept']))
    ok = [s for s in states if s['mastery'] >= data.STRONG_FROM]
    if ok:
        with st.expander(f'On track ({len(ok)})'):
            for s in ok:
                st.markdown('{} — {:.0%} est.'.format(s['concept'], s['mastery']))


# ---------- settings ----------
def settings(db, chunks):
    page_header('Settings', 'Your profile and how the app is configured on this machine.', 'Account')
    with st.container(border=True):
        name = st.text_input('Display name', value=db.get('name', 'Learner'))
        if st.button('Save profile', type='primary'):
            db.set('name', name.strip() or 'Learner')
            st.toast('Profile saved')
            st.rerun()
    with st.container(border=True):
        st.markdown('**AI provider**')
        has_key = bool(os.getenv('OPENAI_API_KEY'))
        badges(('API key set' if has_key else 'No API key', 'good' if has_key else 'neutral'))
        st.text_input('Configured model', value=os.getenv('OPENAI_MODEL', 'gpt-4o-mini') if has_key else 'Not configured', disabled=True)
        st.caption('Add secrets locally in `.env` (copy `.env.example`). Without a key the tutor shows labelled excerpts from your materials and never presents them as AI output.')
