"""Read-only view helpers. Everything here derives from the real SQLite store; nothing is invented."""
import re
from collections import Counter
from datetime import datetime

TYPE_LABEL = {'pdf': 'PDF', 'pptx': 'Slides', 'docx': 'Word', 'transcript': 'Transcript'}
UNIT_LABEL = {'pdf': 'pages', 'pptx': 'slides'}
WEAK_BELOW = 0.60      # heuristic thresholds, labelled as such in the UI
STRONG_FROM = 0.80
_STOP = {'which', 'their', 'these', 'about', 'where', 'there', 'would', 'could', 'should', 'being', 'other',
         'while', 'those', 'using', 'because', 'between', 'through', 'during', 'after', 'before', 'under'}


def cite(chunk):
    """Citation text that never claims a page for formats that have none (legacy DOCX rows stored 'page 1')."""
    if chunk.content_type == 'docx':
        return chunk.document_name
    return chunk.citation()


def materials(chunks):
    """One summary row per uploaded document, in upload order."""
    docs = {}
    for c in chunks:
        d = docs.setdefault(c.document_id, {'id': c.document_id, 'name': c.document_name, 'type': c.content_type,
                                            'passages': 0, 'locations': set(), 'timed': False})
        d['passages'] += 1
        loc = c.page_number if c.content_type == 'pdf' else c.slide_number if c.content_type == 'pptx' else None
        if loc:
            d['locations'].add(loc)
        d['timed'] = d['timed'] or c.start_seconds is not None
    rows = []
    for d in docs.values():
        unit = UNIT_LABEL.get(d['type'])
        extent = f"{len(d['locations'])} {unit} indexed" if unit and d['locations'] else (
            'timestamped' if d['timed'] else 'no page or time markers')
        rows.append({**d, 'label': TYPE_LABEL.get(d['type'], d['type'].upper()), 'extent': extent})
    return rows


def scoped(chunks, doc_id):
    return chunks if not doc_id else [c for c in chunks if c.document_id == doc_id]


def key_terms(chunks, n=5):
    """Most frequent non-trivial words in the materials (used only to propose example prompts)."""
    words = Counter(w.lower() for c in chunks for w in re.findall(r'\b[A-Za-z]{6,}\b', c.text))
    ranked = [(w, k) for w, k in words.most_common(60) if w not in _STOP]
    repeated = [w for w, k in ranked if k >= 2]          # prefer words the material keeps coming back to
    return (repeated + [w for w, _ in ranked if w not in repeated])[:n]


def suggested_prompts(chunks, doc_id=None):
    pool = scoped(chunks, doc_id)
    if not pool:
        return []
    name = pool[0].document_name if doc_id else None
    prompts = [f'Summarize the main ideas in {name}' if name else 'Summarize the main ideas in my materials']
    prompts += [f'What does the material say about {t}?' for t in key_terms(pool, 3)]
    return prompts


def assessments(db):
    out = []
    for r in db.assessments():
        out.append({'id': r['id'], 'topic': r['topic'] or 'Untitled quiz', 'score': r['score'], 'total': r['total'],
                    'created_at': r['created_at']})
    return out


def concept_states(db):
    rows = db.conn.execute('SELECT concept, mastery, attempts, last_activity FROM learner_state ORDER BY mastery ASC').fetchall()
    return [dict(r) for r in rows]


def mastery_band(m):
    return 'needs attention' if m < WEAK_BELOW else 'on track' if m >= STRONG_FROM else 'building'


def pretty_time(ts):
    if not ts:
        return ''
    try:
        return datetime.fromisoformat(str(ts).replace('Z', '+00:00')).strftime('%d %b, %H:%M')
    except ValueError:
        return str(ts)


def reviewed_after_activity(db, concept, last_activity):
    """A revision task counts as done only if the learner marked it reviewed after their latest attempt."""
    stamp = db.get(f'reviewed:{concept}', '')
    return bool(stamp and last_activity and stamp >= str(last_activity))


def next_action(db, chunks):
    """Single most useful next step, derived from real state. Returns dict(title, why, label, page, payload)."""
    if not chunks:
        return {'title': 'Add your first study material', 'why': 'Everything in LearnSphere is built from your own PDFs, slides, notes and transcripts.',
                'label': 'Add material', 'page': 'materials', 'payload': {}}
    states = concept_states(db)
    weak = [s for s in states if s['mastery'] < WEAK_BELOW and not reviewed_after_activity(db, s['concept'], s['last_activity'])]
    if weak:
        w = weak[0]
        return {'title': f"Revisit “{w['concept']}”", 'why': f"Estimated mastery is {w['mastery']:.0%} after {w['attempts']} scored attempt(s). Review the source, then retry.",
                'label': 'Open revision plan', 'page': 'revision', 'payload': {}}
    last_q = db.get('last_tutor_question', '')
    if not states:
        return {'title': 'Take a short baseline quiz', 'why': 'A few source-based questions establish your starting point so recommendations can be personal.',
                'label': 'Start quiz', 'page': 'quiz', 'payload': {}}
    if last_q:
        return {'title': 'Pick up where you left off', 'why': f'Your last tutor question: “{last_q[:90]}”',
                'label': 'Open tutor', 'page': 'tutor', 'payload': {}}
    return {'title': 'Keep the momentum', 'why': 'No weak concepts right now. Try a fresh quiz to keep your estimates current.',
            'label': 'Start quiz', 'page': 'quiz', 'payload': {}}
