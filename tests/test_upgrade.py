from learnsphere.ingestion import make_chunks
from learnsphere.assessment import validate,grade,generate
from learnsphere.models import Question
from learnsphere.db import Store
from learnsphere.learner import update_bkt,record,get_state
from learnsphere.grounding import grounded_answer,resolve_citations
from learnsphere.evaluation.run_eval import evaluate
from learnsphere.evaluation.simulate import run
def test_locations_and_resolution(tmp_path):
 db=Store(str(tmp_path/'a.db')); c=make_chunks('slides.pptx','pptx',[(2,'Energy is conserved in a closed system.',None)])[0]; db.add_chunks([c]); assert 'slide 2' in c.citation() and resolve_citations(db,[c.id])[0].text==c.text
def test_timestamp_and_abstention():
 c=make_chunks('lecture.vtt','transcript',[(None,'Velocity has both magnitude and direction.',(272,None))])[0]; assert '04:32' in c.citation(); assert not grounded_answer('Who won the World Cup?', [c])['supported']
def test_question_validation_and_numeric():
 q=Question('n','Compute','numeric','math',['force'],'easy',['x'],10,'10',tolerance=.1); assert validate(q)[0] and grade(q,'10.05')[0] and not grade(q,'11')[0]
def test_bkt_and_persistence(tmp_path):
 db=Store(str(tmp_path/'a.db')); assert update_bkt(.25,True)>.25; record(db,'energy',False); assert get_state(db,'energy')['attempts']==1
def test_dedup(tmp_path):
 db=Store(str(tmp_path/'a.db')); cs=make_chunks('x.txt','transcript',[(None,'Photosynthesis converts light energy into chemical energy in plants.',None)]); assert generate(cs,'photosynthesis',store=db); assert not generate(cs,'photosynthesis',store=db)
def test_evaluation_and_simulation_reproducible():
 r=evaluate(); assert r['dataset']['answerable']==20 and r['grounding']['unsupported_refusal_rate']==1; assert run()==run()
