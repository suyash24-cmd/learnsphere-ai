from learnsphere.ingestion import make_chunks
from learnsphere.retrieval import search
from learnsphere.db import Store
def test_chunks_retain_citation():
 c=make_chunks('Biology.pdf','pdf',[(4,'Cells use mitochondria to release energy for their functions.',None)])[0]
 assert c.page_number==4 and 'p. 4' in c.citation()
def test_retrieval():
 cs=make_chunks('a.txt','transcript',[(None,'Photosynthesis converts light energy into chemical energy in plants.',None)])
 assert search(cs,'light energy')[0].document_name=='a.txt'
def test_store_deduplicates(tmp_path):
 db=Store(str(tmp_path/'x.db')); cs=make_chunks('a.txt','transcript',[(None,'A sufficiently long source statement for indexing in a learner database.',None)])
 assert db.add_chunks(cs)==1 and db.add_chunks(cs)==0
