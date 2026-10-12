from dataclasses import dataclass, asdict, field
from typing import Optional

@dataclass
class Chunk:
    id: str; document_id: str; document_name: str; content_type: str; text: str
    page_number: Optional[int]=None; slide_number: Optional[int]=None
    start_seconds: Optional[float]=None; end_seconds: Optional[float]=None
    concept: Optional[str]=None; figure_description: Optional[str]=None
    def to_dict(self): return asdict(self)
    def citation(self):
        if self.page_number: return f"{self.document_name} — p. {self.page_number}"
        if self.slide_number: return f"{self.document_name} — slide {self.slide_number}"
        if self.start_seconds is not None:
            m,s=divmod(int(self.start_seconds),60); return f"{self.document_name} — {m:02d}:{s:02d}"
        return self.document_name

@dataclass
class Question:
    id: str; text: str; question_type: str; topic: str; concepts: list[str]
    difficulty: str; source_chunk_ids: list[str]; answer: object; explanation: str
    options: list[str]=field(default_factory=list); rubric: str=''
    tolerance: Optional[float]=None; unit: Optional[str]=None
    def fingerprint(self): return ' '.join(self.text.lower().split())
