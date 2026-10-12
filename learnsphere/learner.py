"""Transparent Bayesian Knowledge Tracing state; not a claim of real learning efficacy."""
from datetime import datetime, timezone
DEFAULT={'prior':.25,'learn':.12,'slip':.1,'guess':.2}
def update_bkt(p,correct,learn=.12,slip=.1,guess=.2):
    likelihood=(1-slip) if correct else slip; non=(guess if correct else 1-guess)
    posterior=(p*likelihood)/(p*likelihood+(1-p)*non)
    return posterior+(1-posterior)*learn
def get_state(store,concept):
    r=store.conn.execute('SELECT * FROM learner_state WHERE concept=?',(concept,)).fetchone()
    return dict(r) if r else {'concept':concept,'mastery':DEFAULT['prior'],'attempts':0,**DEFAULT,'last_activity':None}
def record(store,concept,correct):
    s=get_state(store,concept); s['mastery']=update_bkt(s['mastery'],correct,s['learn'],s['slip'],s['guess']); s['attempts']+=1; s['last_activity']=datetime.now(timezone.utc).isoformat()
    store.conn.execute('INSERT OR REPLACE INTO learner_state VALUES (?,?,?,?,?,?,?,?)',(concept,s['mastery'],s['prior'],s['learn'],s['slip'],s['guess'],s['attempts'],s['last_activity'])); store.conn.commit(); return s
def recommendation(store,concepts):
    states=[get_state(store,c) for c in concepts]
    if not states:return None
    weak=min(states,key=lambda x:x['mastery']); return {'concept':weak['concept'],'mastery':weak['mastery'],'rationale':f"{weak['concept']} has lowest estimated mastery ({weak['mastery']:.0%}) from {weak['attempts']} scored attempts."}
