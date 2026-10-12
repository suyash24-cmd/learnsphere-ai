"""UI-layer tests: data helpers, ingestion citation accuracy, and headless end-to-end flows via Streamlit AppTest."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from learnsphere.db import Store
from learnsphere.ingestion import make_chunks, parse_transcript, transcript_parts
from learnsphere.ui import data
from learnsphere.ui.views import friendly_error

TEXTS = {
    'Biology.pdf': ('pdf', 3, 'Photosynthesis converts light energy into chemical energy inside plant chloroplasts every day.'),
    'Energy.pptx': ('pptx', 2, 'Kinetic energy describes motion while potential energy describes stored energy in objects.'),
    'Cells.pdf': ('pdf', 5, 'Mitochondria release usable energy through cellular respiration inside animal cells constantly.'),
}


def seed(db):
    for name, (kind, loc, text) in TEXTS.items():
        db.add_chunks(make_chunks(name, kind, [(loc, text, None)]))


# ---- citation accuracy ----
def test_docx_never_claims_a_page():
    c = make_chunks('Notes.docx', 'docx', [(1, 'A document paragraph that is long enough to keep.', None)])[0]
    assert c.page_number is None and c.citation() == 'Notes.docx' and data.cite(c) == 'Notes.docx'


def test_vtt_cues_keep_their_own_timestamps():
    raw = 'WEBVTT\n\n1\n00:00:05.000 --> 00:00:08.000\nHello class.\n\n2\n01:02:03.500 --> 01:02:05.000\n<v Prof>Velocity has direction.</v>\n'
    assert parse_transcript(raw) == [(5, 'Hello class.'), (3723, 'Velocity has direction.')]


def test_plain_text_gets_no_invented_timestamp():
    parts = transcript_parts('Just notes with no time markers at all.')
    assert parts[0][2] is None
    assert make_chunks('n.txt', 'transcript', parts)[0].citation() == 'n.txt'


def test_leading_timestamps_are_used():
    assert parse_transcript('[04:32] Energy is conserved.\n[04:50] Next topic.') == [(272, 'Energy is conserved.'), (290, 'Next topic.')]


# ---- data helpers ----
def test_materials_summary_and_scope(tmp_path):
    db = Store(str(tmp_path / 'a.db')); seed(db)
    rows = data.materials(db.chunks())
    assert [r['name'] for r in rows] == list(TEXTS) and rows[0]['extent'] == '1 pages indexed' and rows[1]['label'] == 'Slides'
    assert len(data.scoped(db.chunks(), rows[0]['id'])) == 1


def test_next_action_follows_real_state(tmp_path):
    db = Store(str(tmp_path / 'a.db'))
    assert data.next_action(db, [])['page'] == 'materials'
    seed(db); chunks = db.chunks()
    assert data.next_action(db, chunks)['page'] == 'quiz'
    from learnsphere.learner import record
    for _ in range(2): record(db, 'energy', False)
    assert data.next_action(db, chunks)['page'] == 'revision'


def test_friendly_errors_are_plain_language():
    what, fix = friendly_error('x.pdf', ValueError('No selectable text was found. This appears scanned; OCR is required before indexing.'))
    assert 'scanned' in what and 'OCR' in fix
    assert 'Upload' in friendly_error('v.mp4', ValueError('Video needs FFmpeg plus a configured transcription service.'))[1]


# ---- headless end-to-end ----
@pytest.fixture
def app(tmp_path, monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    monkeypatch.chdir(tmp_path); monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    st.cache_resource.clear()
    db = Store(str(tmp_path / 'data' / 'learnsphere.db')); seed(db); db.conn.close()
    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    yield at
    st.cache_resource.clear()


def nav(at, label):
    next(b for b in at.sidebar.button if b.label == label).click(); at.run()
    assert not at.exception, [e.value for e in at.exception]


def press(at, label):
    next(b for b in at.main.button if b.label == label).click(); at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_every_screen_renders(app):
    assert not app.exception
    for label in ['Overview', 'My Materials', 'AI Tutor', 'Adaptive Quiz', 'Learning Analytics', 'Revision Plan', 'Settings']:
        nav(app, label)


def test_tutor_cites_and_abstains(app):
    nav(app, 'AI Tutor')
    app.chat_input[0].set_value('What does the material say about photosynthesis?').run()
    assert not app.exception
    assert any('Biology.pdf — p. 3' in e.label for e in app.expander)
    assert any('no AI model' in m.value for m in app.markdown)       # honestly labelled, not passed off as an LLM
    app.chat_input[0].set_value('Who won the World Cup?').run()
    assert any('Not found in your materials' in m.value for m in app.markdown)


def test_quiz_to_results_to_analytics_and_revision(app):
    nav(app, 'Adaptive Quiz')
    app.text_input(key='quiz_topic').set_value('energy').run()
    press(app, 'Create quiz')
    answers_given = 0
    for _ in range(10):
        box = [t for t in app.text_input if t.label == 'Your answer']
        if not box: break
        box[0].set_value('wrong').run(); answers_given += 1
        press(app, 'Next' if any(b.label == 'Next' for b in app.main.button) else 'Submit')
    assert answers_given >= 2
    assert [m.label for m in app.metric] == ['Score'] and app.metric[0].value == '0%'
    nav(app, 'Learning Analytics')
    assert dict((m.label, m.value) for m in app.metric)['Quizzes taken'] == '1'
    nav(app, 'Revision Plan')
    assert any(b.label == 'Mark reviewed' for b in app.main.button)
    press(app, 'Mark reviewed')
    assert any(b.label == 'Mark reviewed' and b.disabled for b in app.main.button)


def test_quiz_answers_survive_back_and_next(app):
    nav(app, 'Adaptive Quiz')
    app.text_input(key='quiz_topic').set_value('energy').run(); press(app, 'Create quiz')
    app.text_input[0].set_value('kept').run(); press(app, 'Next'); press(app, 'Back')
    assert app.text_input[0].value == 'kept'


def test_empty_state_has_no_fake_numbers(tmp_path, monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    monkeypatch.chdir(tmp_path); st.cache_resource.clear()
    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    assert not at.exception and len(at.metric) == 0
    st.cache_resource.clear()
