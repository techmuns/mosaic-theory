# HYPOTHETICAL article B — a labelled test fixture, not a real publication

Used for the A → B update demonstration on the PRESERVED registry built from the real
J.P. Morgan article (and by `tests/test_theme_intelligence_overlap.py`'s twin). Replay:

```bash
.venv/bin/python -m vinci.theme_intelligence --data-dir <copy of the acceptance registry> article --url https://example.test/hypothetical/capex-reaffirmed-2026-02-20 --as-of 2026-02-20 --html tests/fixtures/theme_intelligence/hypothetical_b/article.html --fixture tests/fixtures/theme_intelligence/hypothetical_b/extraction.json
```
