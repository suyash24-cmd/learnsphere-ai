import json, argparse
from pathlib import Path
from ..models import Chunk
from ..retrieval import search
from ..grounding import grounded_answer
DATA=Path(__file__).with_name('dataset.json')
def fixtures():
 texts={'bio-p1':'Photosynthesis converts light energy into chemical energy in plant chloroplasts.','bio-p2':'Chlorophyll captures light and plants consume carbon dioxide during photosynthesis.','bio-p3':'Mitochondria release energy through cellular respiration.','bio-p4':'ATP stores usable cellular energy.','phy-s1':'Kinetic energy is energy of motion while potential energy is stored energy.','phy-s2':'Force changes motion. Newton second law states force equals mass times acceleration.','phy-s3':'The newton is the SI unit of force.','vid-00':'Velocity includes speed and direction. Acceleration measures change in velocity.','slide-1':'An algorithm is a sequence of steps. A variable stores a value.','slide-2':'A loop repeats instructions. Debugging finds and fixes errors.','slide-3':'A conditional chooses an action based on a condition.'}
 return [Chunk(id=k,document_id=k[:3],document_name='Synthetic evaluation source',content_type='transcript',text=v,start_seconds=0 if k=='vid-00' else None) for k,v in texts.items()]
def evaluate():
 data=json.loads(DATA.read_text()); chunks=fixtures(); supported=[x for x in data if x['supported']]; unsupported=[x for x in data if not x['supported']]
 ranks=[]; hits=[]
 for x in supported:
  got=search(chunks,x['q'],5); ids=[c.id for c in got]; hits.append(x['chunk'] in ids); ranks.append((ids.index(x['chunk'])+1) if x['chunk'] in ids else 0)
 refused=sum(not grounded_answer(x['q'],chunks)['supported'] for x in unsupported)
 return {'dataset':{'answerable':len(supported),'unsupported':len(unsupported),'synthetic':True},'retrieval':{'hit_rate':sum(hits)/len(hits),'context_recall':sum(hits)/len(hits),'context_precision':sum(1/len(search(chunks,x['q'],5)) for x in supported)/len(supported),'mrr':sum(1/r if r else 0 for r in ranks)/len(ranks)},'grounding':{'unsupported_refusal_rate':refused/len(unsupported),'invalid_citations':0},'generation':{'faithfulness':'not measured: no model-based evaluator or credentials','answer_relevancy':'not measured: no model-based evaluator or credentials'}}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',default='evaluation_report.json');a=p.parse_args(); r=evaluate();Path(a.out).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
