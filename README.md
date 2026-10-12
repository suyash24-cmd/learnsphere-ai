# LearnSphere AI

Multimodal, source-cited study companion for the Multimodal AI Hackathon 2026, Track D.

## Run

```powershell
# The supplied development environment is `.runenv`.
.\.runenv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Run validation with `pytest -q`. Without `OPENAI_API_KEY`, tutoring visibly uses a deterministic offline study aid; it is never presented as an LLM response. Add optional provider settings in `.env` copied from `.env.example`.

## Evaluation and reproducibility

```powershell
python -m pytest -q
python -m learnsphere.evaluation.run_eval --out evaluation_report.json
python -m learnsphere.evaluation.simulate
```

The checked-in evaluation dataset is synthetic: 20 answerable questions and 10 off-material questions across PDF-like, slide-like, and transcript-like sources. On 2026-10-13, deterministic lexical retrieval measured top-5 hit/recall `1.00`, MRR `0.95`, and context precision `0.637`; refusal rate on the 10 unsupported prompts was `1.00`. These are controlled retrieval/grounding measurements, not evidence of educational effectiveness. Model-based faithfulness and relevancy are not measured because no evaluator-model credentials are configured.

See [docs/REQUIREMENTS_MATRIX.md](docs/REQUIREMENTS_MATRIX.md) for an honest feature-status audit and `docs/` for architecture, grounding, learner-model, evaluation, and demonstration documentation.

## Design notes

The app normalizes all input to source-preserving chunks in SQLite. Lexical retrieval is the dependable offline baseline. PDF pages, slides, and transcript timestamps are retained in citations. For video, FFmpeg/transcription is deliberately configuration-dependent; transcript upload remains a complete offline path.
