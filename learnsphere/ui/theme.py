"""Design tokens, scoped CSS, and small HTML helpers. User-supplied text is always escaped."""
from html import escape
import streamlit as st

CSS = """
<style>
:root{
  --ls-ink:#1B1B3A; --ls-muted:#5E6082; --ls-line:#E6E3D8; --ls-surface:#FFFFFF; --ls-bg:#FBFAF7;
  --ls-violet:#5B4BDB; --ls-violet-soft:#EEEBFF; --ls-blue:#2F6BFF;
  --ls-good:#12795A; --ls-good-soft:#E3F5EE; --ls-warn:#9A5B00; --ls-warn-soft:#FFF1DA; --ls-bad:#B3261E; --ls-bad-soft:#FDE8E6;
  --ls-r-sm:8px; --ls-r-md:14px; --ls-r-lg:20px;
  --ls-shadow:0 1px 2px rgba(27,27,58,.04),0 6px 20px rgba(27,27,58,.05);
  --ls-ease:160ms cubic-bezier(.2,.7,.3,1);
}
.stApp{background:var(--ls-bg);color:var(--ls-ink)}
.block-container{max-width:1080px;padding-top:2.2rem;padding-bottom:4rem}
h1,h2,h3{letter-spacing:-.015em;color:var(--ls-ink)}
/* sidebar */
[data-testid="stSidebar"]{background:#F6F4EC;border-right:1px solid var(--ls-line)}
[data-testid="stSidebar"] .stButton>button{justify-content:flex-start;border:0;background:transparent;color:var(--ls-ink);font-weight:500;border-radius:var(--ls-r-sm);padding:.45rem .7rem;box-shadow:none}
[data-testid="stSidebar"] .stButton>button:hover{background:#ECE9DD}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:var(--ls-violet-soft);color:var(--ls-violet);font-weight:650}
/* buttons + focus */
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{border-radius:10px;transition:transform var(--ls-ease),box-shadow var(--ls-ease),background var(--ls-ease)}
.stButton>button[kind="primary"],[data-testid="stFormSubmitButton"]>button[kind="primary"]{background:linear-gradient(135deg,var(--ls-violet),var(--ls-blue));border:0;color:#fff}
.stButton>button:hover{transform:translateY(-1px)}
:focus-visible{outline:3px solid #8E83F5!important;outline-offset:2px!important}
/* bordered containers act as cards */
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--ls-line)!important;border-radius:var(--ls-r-md)!important;background:var(--ls-surface);box-shadow:var(--ls-shadow)}
[data-testid="stMetric"]{background:var(--ls-surface);border:1px solid var(--ls-line);border-radius:var(--ls-r-md);padding:.8rem 1rem}
[data-testid="stMetricLabel"]{color:var(--ls-muted)}
/* custom bits */
.ls-eyebrow{font-size:.74rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--ls-violet)}
.ls-title{font-size:2rem;font-weight:750;line-height:1.15;margin:.15rem 0 .35rem}
.ls-desc{color:var(--ls-muted);font-size:1.02rem;max-width:62ch;margin:0 0 1.2rem}
.ls-hero{background:linear-gradient(135deg,#F1EEFF 0%,#EAF1FF 100%);border:1px solid #DCD7FA;border-radius:var(--ls-r-lg);padding:1.4rem 1.5rem}
.ls-hero h3{margin:.2rem 0 .3rem;font-size:1.35rem}
.ls-hero p{margin:0;color:var(--ls-muted)}
.ls-badge{display:inline-block;font-size:.74rem;font-weight:650;padding:.12rem .55rem;border-radius:999px;margin-right:.35rem;background:var(--ls-violet-soft);color:var(--ls-violet)}
.ls-badge.good{background:var(--ls-good-soft);color:var(--ls-good)}
.ls-badge.warn{background:var(--ls-warn-soft);color:var(--ls-warn)}
.ls-badge.bad{background:var(--ls-bad-soft);color:var(--ls-bad)}
.ls-badge.neutral{background:#EFEDE4;color:var(--ls-muted)}
.ls-note{font-size:.88rem;color:var(--ls-muted)}
.ls-avatar{width:38px;height:38px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;color:#fff;background:linear-gradient(135deg,var(--ls-violet),var(--ls-blue))}
.ls-brand{font-size:1.15rem;font-weight:780;letter-spacing:-.02em}
.ls-dot{color:var(--ls-violet)}
.ls-bar{height:8px;border-radius:999px;background:#ECE9DD;overflow:hidden}
.ls-bar>span{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--ls-violet),var(--ls-blue));transition:width 400ms ease}
.ls-bar.warn>span{background:#E39A2D}.ls-bar.good>span{background:#1F9D74}
@media (prefers-reduced-motion:no-preference){.block-container{animation:ls-in 220ms ease-out}@keyframes ls-in{from{opacity:.0;transform:translateY(4px)}to{opacity:1;transform:none}}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media (max-width:640px){.ls-title{font-size:1.55rem}.block-container{padding-top:1.2rem}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title, desc, eyebrow=''):
    eb = f'<div class="ls-eyebrow">{escape(eyebrow)}</div>' if eyebrow else ''
    st.markdown(f'{eb}<div class="ls-title">{escape(title)}</div><p class="ls-desc">{escape(desc)}</p>', unsafe_allow_html=True)


def badge(text, tone=''):
    return f'<span class="ls-badge {tone}">{escape(str(text))}</span>'


def badges(*items):
    """items: (text, tone) tuples -> one markdown line."""
    st.markdown(''.join(badge(t, tone) for t, tone in items), unsafe_allow_html=True)


def progress_bar(fraction, tone=''):
    pct = max(0, min(100, round(fraction * 100)))
    st.markdown(f'<div class="ls-bar {tone}" role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100"><span style="width:{pct}%"></span></div>', unsafe_allow_html=True)


def avatar(name):
    initial = escape((name.strip() or 'L')[0].upper())
    return f'<span class="ls-avatar" aria-hidden="true">{initial}</span>'


def empty_state(title, body):
    with st.container(border=True):
        st.markdown(f'**{escape(title)}**')
        st.markdown(f'<span class="ls-note">{escape(body)}</span>', unsafe_allow_html=True)
