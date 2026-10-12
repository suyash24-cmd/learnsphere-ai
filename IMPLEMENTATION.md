# LearnSphere AI implementation checklist

- [x] Offline-first Streamlit application scaffold and SQLite learner store
- [x] PDF, PPTX, DOCX, transcript, and practical video ingestion paths
- [x] Unified source-preserving chunks and lexical retrieval fallback
- [x] Optional OpenAI-compatible grounded tutor; explicit deterministic fallback
- [x] Adaptive quiz, scoring, analytics, and revision plan
- [x] Automated service tests
- [x] Install dependencies and run tests (`pytest -q`: 21 passed on Python 3.12 / Streamlit 1.39)
- [x] Redesigned UI (`learnsphere/ui/`) with headless end-to-end tests via Streamlit AppTest
- [ ] Visual check in a real browser at narrow and wide widths (not performed in the build sandbox)
