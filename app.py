import streamlit as st
from dotenv import load_dotenv

from learnsphere.db import Store
from learnsphere.ui import views
from learnsphere.ui.theme import inject_css

load_dotenv()
st.set_page_config(page_title='LearnSphere AI', page_icon='◉', layout='wide')
inject_css()


@st.cache_resource
def get_store():
    return Store()


ss = st.session_state
for key, default in {'page': 'overview', 'up_key': 0, 'chat': [], 'quiz': None, 'upload_report': []}.items():
    ss.setdefault(key, default)

db = get_store()
chunks = db.chunks()
views.sidebar(db, chunks)

SCREENS = {
    'overview': views.overview, 'materials': views.materials, 'tutor': views.tutor_view, 'quiz': views.quiz_view,
    'analytics': views.analytics, 'revision': views.revision, 'settings': views.settings,
}
SCREENS.get(ss.page, views.overview)(db, chunks)
