import json, sqlite3
from pathlib import Path
from .models import Chunk

class Store:
    def __init__(self, path="data/learnsphere.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True); self.conn=sqlite3.connect(path,check_same_thread=False); self.conn.row_factory=sqlite3.Row
        self.conn.executescript('''CREATE TABLE IF NOT EXISTS chunks (id TEXT PRIMARY KEY, document_id TEXT, document_name TEXT, content_type TEXT, text TEXT, metadata TEXT); CREATE TABLE IF NOT EXISTS assessments (id INTEGER PRIMARY KEY, topic TEXT, score REAL, total INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP, report TEXT DEFAULT '{}'); CREATE TABLE IF NOT EXISTS profile (key TEXT PRIMARY KEY, value TEXT); CREATE TABLE IF NOT EXISTS learner_state(concept TEXT PRIMARY KEY, mastery REAL, prior REAL, learn REAL, slip REAL, guess REAL, attempts INTEGER, last_activity TEXT); CREATE TABLE IF NOT EXISTS served_questions(fingerprint TEXT PRIMARY KEY, question_id TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);''');
        try: self.conn.execute("ALTER TABLE assessments ADD COLUMN report TEXT DEFAULT '{}'")
        except sqlite3.OperationalError: pass
        self.conn.commit()
    def add_chunks(self,chunks):
        added=0
        for c in chunks:
            exists=self.conn.execute('SELECT 1 FROM chunks WHERE document_name=? AND text=?',(c.document_name,c.text)).fetchone()
            if c.text.strip() and not exists:
                meta={k:v for k,v in c.to_dict().items() if k not in {'id','document_id','document_name','content_type','text'}}; self.conn.execute('INSERT INTO chunks VALUES (?,?,?,?,?,?)',(c.id,c.document_id,c.document_name,c.content_type,c.text,json.dumps(meta))); added+=1
        self.conn.commit(); return added
    def chunks(self):
        rows=self.conn.execute('SELECT * FROM chunks').fetchall(); return [Chunk(id=r['id'],document_id=r['document_id'],document_name=r['document_name'],content_type=r['content_type'],text=r['text'],**json.loads(r['metadata'])) for r in rows]
    def get_chunk(self,chunk_id):
        r=self.conn.execute('SELECT * FROM chunks WHERE id=?',(chunk_id,)).fetchone()
        return Chunk(id=r['id'],document_id=r['document_id'],document_name=r['document_name'],content_type=r['content_type'],text=r['text'],**json.loads(r['metadata'])) if r else None
    def material_count(self): return self.conn.execute('SELECT COUNT(DISTINCT document_id) FROM chunks').fetchone()[0]
    def save_assessment(self,topic,score,total,report=None): self.conn.execute('INSERT INTO assessments(topic,score,total,report) VALUES (?,?,?,?)',(topic,score,total,json.dumps(report or {}))); self.conn.commit()
    def assessments(self): return self.conn.execute('SELECT * FROM assessments ORDER BY created_at DESC').fetchall()
    def set(self,key,value): self.conn.execute('INSERT OR REPLACE INTO profile VALUES (?,?)',(key,value)); self.conn.commit()
    def get(self,key,default=''):
        row=self.conn.execute('SELECT value FROM profile WHERE key=?',(key,)).fetchone(); return row[0] if row else default
    def served(self,fingerprint): return bool(self.conn.execute('SELECT 1 FROM served_questions WHERE fingerprint=?',(fingerprint,)).fetchone())
    def serve(self,q): self.conn.execute('INSERT OR IGNORE INTO served_questions(fingerprint,question_id) VALUES (?,?)',(q.fingerprint(),q.id)); self.conn.commit()
    def close(self): self.conn.close()
