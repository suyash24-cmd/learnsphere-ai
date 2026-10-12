# Track D requirements matrix (2026-10-13)

| Requirement | Status | Evidence |
|---|---|---|
| Page/slide/timestamp source metadata | Implemented and tested | `models.py`, `ingestion.py`, `test_upgrade.py` |
| Scanned PDF OCR and figure vision | Blocked/partial | Clear OCR-required error; no OCR/vision dependency or credentials |
| Video audio/STT/frame ingestion | Partial | Transcript ingestion works; video reports configuration need |
| Grounded citations and abstention | Implemented and tested offline | `grounding.py`, evaluation, tests |
| Click-to-open source/video seek | Missing | Metadata is shown but source binaries are not persisted |
| Concept graph/prerequisites | Partial | Concept tags in chunks; no verified prerequisite extraction |
| MCQ/short/numeric validated assessment | Partial | Schema and validators/graders implemented; generator currently emits short-answer only |
| Question novelty | Implemented exact only | SQLite fingerprints; semantic metric explicitly unavailable |
| BKT learner model and persistence | Implemented and tested | `learner.py`, SQLite, tests |
| Diagnostic/onboarding | Partial | Empty-state onboarding; no dedicated diagnostic flow |
| Deterministic retrieval/grounding evaluation | Implemented | 20 answerable, 10 unsupported synthetic dataset |
| Model-based generation evaluation | Blocked | Requires evaluator model credentials; no result claimed |
| Simulated learner evaluation | Implemented | seeded `simulate.py`; simulation is not educational efficacy |
| Concept map | Missing | Deferred behind mandatory source/evaluation functionality |
| Citation accuracy for DOCX and timed transcripts | Fixed 2026-10-13 | DOCX passages no longer claim "p. 1"; VTT/SRT cues and leading `[mm:ss]` stamps are kept per passage; plain TXT gets no timestamp (`test_ui.py`) |
