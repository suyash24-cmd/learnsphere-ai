# Architecture
Uploads are normalized into `Chunk` records and stored in SQLite with source location metadata. CPU lexical retrieval selects evidence. `grounding.py` produces an explicit deterministic extractive answer or abstains. The optional OpenAI provider remains in `tutor.py`; it must cite the supplied context. Assessment records update persisted BKT concept state.

No hosted service, GPU, or paid API is required for the offline demo.
