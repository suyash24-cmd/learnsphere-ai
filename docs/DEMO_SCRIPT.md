# 5-minute demo
1. **Overview (empty)**: show the onboarding state and the single "Add material" next step. No fake statistics.
2. **My Materials**: upload a PDF, slides or a `.vtt` transcript; watch the progress bar, then the library card with its page/slide/timestamp coverage. Open *Inspect passages*.
3. **AI Tutor**: click a suggested prompt; open a source card to show the exact page, slide or timestamp. Ask an off-material question to show the "Not found in your materials" abstention.
4. **Adaptive Quiz**: pick a topic, answer, go Back/Next to show answers are kept, submit. Point out the grading note and per-question sources.
5. **Learning Analytics** and **Revision Plan**: show updated mastery estimates, the "what does this mean" explainer, then *Targeted quiz* from a weak concept.
6. Run `python -m learnsphere.evaluation.run_eval` and state that the dataset is synthetic.
7. State the limits: OCR, video transcription and model-based evaluation are not configured; short-answer grading is keyword-based.
