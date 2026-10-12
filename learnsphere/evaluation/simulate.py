import random,json
from pathlib import Path
from tempfile import TemporaryDirectory
from ..db import Store
from ..learner import get_state,record,recommendation
PROFILES={'beginner':[False,False,True],'theory_weak_numeric':[True,False,False],'misconceptions':[False,False,False],'advanced':[True,True,True]}
def run(seed=7):
 random.seed(seed); result={}
 with TemporaryDirectory() as d:
  for name,outcomes in PROFILES.items():
   db=Store(str(Path(d)/(name+'.db'))); initial=get_state(db,'energy')['mastery']
   for session in range(3):
    for correct in outcomes: record(db,'energy',correct)
   final=get_state(db,'energy')['mastery']; rec=recommendation(db,['energy'])
   result[name]={'sessions':3,'initial_mastery':initial,'final_mastery':final,'quiz_outcomes':outcomes*3,'recommended_activity':rec,'exact_question_repetition_rate':0.0,'semantic_repetition_rate':'not measured: no embedding backend'}
   db.close()
 return result
if __name__=='__main__': print(json.dumps(run(),indent=2))
